from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    github_login = fields.Char(string='GitHub Login', index=True)
