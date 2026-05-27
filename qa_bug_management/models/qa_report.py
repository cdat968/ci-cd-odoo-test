import secrets
from odoo import models, fields, api


class QaReport(models.Model):
    _name = 'qa.report'
    _description = 'QA Bug Report'
    _order = 'create_date desc'

    name = fields.Char(string='Report Name', required=True)
    project_name = fields.Char(string='Project')
    report_date = fields.Char(string='Report Date')
    share_token = fields.Char(string='Share Token', readonly=True, index=True, copy=False)
    html = fields.Text(string='HTML Source')
    bug_ids = fields.One2many('qa.bug.ticket', 'report_id', string='Bug Tickets')
    bug_count = fields.Integer(string='Bug Count', compute='_compute_bug_count', store=True)

    @api.depends('bug_ids')
    def _compute_bug_count(self):
        for rec in self:
            rec.bug_count = len(rec.bug_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('share_token'):
                vals['share_token'] = secrets.token_urlsafe(32)
        return super().create(vals_list)
