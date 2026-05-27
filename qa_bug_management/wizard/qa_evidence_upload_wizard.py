import base64
import os
import urllib.parse
from odoo import models, fields
from odoo.exceptions import UserError


class QaEvidenceUploadWizard(models.TransientModel):
    _name = 'qa.evidence.upload.wizard'
    _description = 'Upload Evidence Image to Cloudinary'

    ticket_id = fields.Many2one('qa.bug.ticket', required=True, ondelete='cascade')
    file_data  = fields.Binary(string='Image', required=True)
    file_name  = fields.Char()
    caption    = fields.Char(string='Caption')

    def action_upload(self):
        self.ensure_one()
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

        file_bytes = base64.b64decode(self.file_data)
        result = cloudinary.uploader.upload(
            file_bytes,
            folder='qa-evidence',
            use_filename=True,
            unique_filename=True,
            overwrite=False,
            resource_type='image',
        )
        secure_url = result.get('secure_url', '')
        public_id  = result.get('public_id', '')
        if not secure_url:
            raise UserError('Cloudinary did not return a secure_url.')

        self.env['qa.bug.evidence'].create({
            'ticket_id':           self.ticket_id.id,
            'kind':                'screenshot',
            'url':                 secure_url,
            'caption':             self.caption or self.file_name or '',
            'cloudinary_public_id': public_id,
        })

        return {'type': 'ir.actions.act_window_close'}
