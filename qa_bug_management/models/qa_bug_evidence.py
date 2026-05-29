from odoo import models, fields


class QaBugEvidence(models.Model):
    _name = 'qa.bug.evidence'
    _description = 'QA Bug Evidence'

    ticket_id = fields.Many2one('qa.bug.ticket', required=True, ondelete='cascade')
    kind = fields.Selection([
        ('screenshot', 'Screenshot'),
        ('log', 'Log'),
        ('link', 'Link'),
    ], required=True, default='screenshot')
    url = fields.Char(string='URL')
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Attachment',
        ondelete='set null',
    )
    caption = fields.Char(string='Caption')
    cloudinary_public_id = fields.Char(string='Cloudinary ID')
