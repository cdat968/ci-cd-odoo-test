from odoo import models, fields, api


class QaBugTicket(models.Model):
    _name = 'qa.bug.ticket'
    _description = 'QA Bug Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Reference', readonly=True, default='New', copy=False)
    title = fields.Char(string='Title', required=True, tracking=True)
    description = fields.Html(string='Description')
    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium', required=True, tracking=True)
    status = fields.Selection([
        ('new', 'New'),
        ('triaged', 'Triaged'),
        ('in_progress', 'In Progress'),
        ('fixed', 'Fixed'),
        ('wont_fix', "Won't Fix"),
        ('duplicate', 'Duplicate'),
    ], default='new', required=True, tracking=True)
    source = fields.Selection([
        ('ci', 'CI/CD'),
        ('manual', 'Manual'),
        ('report_link', 'Report Link'),
    ], default='ci', required=True)
    ci_run_url = fields.Char(string='CI Run URL')
    ci_commit_sha = fields.Char(string='Commit SHA')
    ci_branch = fields.Char(string='Branch')
    report_share_url = fields.Char(string='Report URL')
    component_a_bug_id = fields.Char(string='Report Bug ID')
    evidence_ids = fields.One2many('qa.bug.evidence', 'ticket_id', string='Evidence')
    assignee_id = fields.Many2one('res.users', string='Assignee', tracking=True)
    reporter = fields.Char(string='Reporter', default='ci-bot')
    resolved_at = fields.Datetime(string='Resolved At', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('qa.bug.ticket') or 'New'
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('status') in ('fixed', 'wont_fix', 'duplicate'):
            vals['resolved_at'] = fields.Datetime.now()
        return super().write(vals)

    def action_open_ci_run(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_url', 'url': self.ci_run_url, 'target': 'new'}

    def action_open_report(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_url', 'url': self.report_share_url, 'target': 'new'}
