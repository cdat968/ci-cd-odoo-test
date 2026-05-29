import base64
import os
import urllib.parse
from odoo import models, fields
from odoo.exceptions import UserError
from odoo.tools.mimetypes import guess_mimetype


class QaEvidenceUploadWizard(models.TransientModel):
    _name = 'qa.evidence.upload.wizard'
    _description = 'Upload Evidence Image to Cloudinary'

    ticket_id = fields.Many2one('qa.bug.ticket', required=True, ondelete='cascade')
    attachment_ids = fields.Many2many('ir.attachment', string='Images', required=True)
    caption = fields.Char(string='Caption')

    def _get_validated_image_bytes(self, attachment, max_upload_size):
        file_bytes = attachment.raw or base64.b64decode(attachment.datas or b'')
        if len(file_bytes) > max_upload_size:
            raise UserError('%s is over the maximum allowed file size.' % attachment.name)

        mimetype = guess_mimetype(file_bytes)
        if not (mimetype or '').startswith('image/'):
            raise UserError('%s is not an image file.' % attachment.name)
        return file_bytes, mimetype

    def action_upload(self):
        self.ensure_one()
        if not self.attachment_ids:
            raise UserError('Select at least one image to upload.')
        cloudinary_url = os.environ.get('CLOUDINARY_URL', '').strip()
        if not cloudinary_url:
            raise UserError('CLOUDINARY_URL is not configured on the server.')

        try:
            import cloudinary
            import cloudinary.uploader
        except ImportError:
            raise UserError("Python package 'cloudinary' is not installed in this environment.")

        parsed = urllib.parse.urlparse(cloudinary_url)
        cloudinary.config(
            cloud_name=parsed.hostname,
            api_key=parsed.username,
            api_secret=parsed.password,
        )

        max_upload_size = int(
            self.env['ir.config_parameter'].sudo().get_param(
                'web.max_file_upload_size',
                128 * 1024 * 1024,
            )
        )
        for attachment in self.attachment_ids:
            file_bytes, mimetype = self._get_validated_image_bytes(
                attachment,
                max_upload_size,
            )

            result = cloudinary.uploader.upload(
                file_bytes,
                folder='qa-evidence',
                use_filename=True,
                unique_filename=True,
                overwrite=False,
                resource_type='image',
            )
            secure_url = result.get('secure_url', '')
            public_id = result.get('public_id', '')
            if not secure_url:
                raise UserError('Cloudinary did not return a secure_url.')

            self.env['qa.bug.evidence'].create({
                'ticket_id': self.ticket_id.id,
                'kind': mimetype,
                'url': secure_url,
                'caption': self.caption or attachment.name or '',
                'cloudinary_public_id': public_id,
            })

        return {'type': 'ir.actions.act_window_close'}
