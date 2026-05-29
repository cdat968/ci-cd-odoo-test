from odoo import models, fields


class QaBugEvidence(models.Model):
    _name = 'qa.bug.evidence'
    _description = 'QA Bug Evidence'

    ticket_id = fields.Many2one('qa.bug.ticket', required=True, ondelete='cascade')
    kind = fields.Char(required=True, default='screenshot')
    url = fields.Char(string='URL')
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Attachment',
        ondelete='set null',
    )
    caption = fields.Char(string='Caption')
    cloudinary_public_id = fields.Char(string='Cloudinary ID')

    def is_image(self):
        self.ensure_one()
        if self.attachment_id:
            return (self.attachment_id.mimetype or '').startswith('image/')
        return self.kind == 'screenshot' or (self.kind or '').startswith('image/')

    def get_image_url(self):
        self.ensure_one()
        if self.url:
            return self.url
        if not self.attachment_id:
            return ''
        token = self.attachment_id.access_token
        token_param = f'&access_token={token}' if token else ''
        return f'/web/content/{self.attachment_id.id}?download=false{token_param}'
