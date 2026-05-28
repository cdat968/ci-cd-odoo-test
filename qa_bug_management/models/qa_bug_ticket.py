from markupsafe import Markup
from odoo import models, fields, api


class QaBugTicket(models.Model):
    _name = 'qa.bug.ticket'
    _description = 'QA Bug Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Reference', readonly=True, default='New', copy=False)
    title = fields.Char(string='Summary', required=True, tracking=True)
    description = fields.Text(string='Description')
    feature_area = fields.Char(string='Feature / Area')
    keyword = fields.Char(string='Keyword')
    build_found = fields.Char(string='Build Found')

    # ── Classification ────────────────────────────────────────────
    severity = fields.Selection([
        ('s1_critical', 'S1 - Critical'),
        ('s2_major',    'S2 - Major'),
        ('s3_minor',    'S3 - Minor'),
        ('s4_trivial',  'S4 - Trivial'),
    ], default='s3_minor', required=True, tracking=True)

    priority = fields.Selection([
        ('p1_urgent', 'P1 - Urgent'),
        ('p2_high',   'P2 - High'),
        ('p3_medium', 'P3 - Medium'),
        ('p4_low',    'P4 - Low'),
    ], default='p3_medium', required=True, tracking=True)

    frequency = fields.Selection([
        ('everytime', 'Everytime'),
        ('sometimes', 'Sometimes'),
        ('hardly',    'Hardly'),
    ], tracking=True)

    reproducibility = fields.Selection([
        ('always',       'Always'),
        ('intermittent', 'Intermittent'),
        ('once',         'Once'),
    ], tracking=True)

    # ── Lifecycle ─────────────────────────────────────────────────
    status = fields.Selection([
        ('new',             'New'),
        ('assigned',        'Assigned'),
        ('in_progress',     'In Progress'),
        ('fixed',           'Fixed'),
        ('in_verification', 'In Verification'),
        ('closed',          'Closed'),
        ('reopened',        'Re-opened'),
        ('rejected',        'Rejected'),
    ], default='new', required=True, tracking=True)

    resolution = fields.Selection([
        ('fixed',               'Fixed'),
        ('not_reproducible',    'Not Reproducible'),
        ('not_a_bug',           'Not a Bug'),
        ('duplicated',          'Duplicated'),
        ('wont_fix',            "Won't Fix"),
        ('deferred',            'Deferred'),
        ('feature_limitation',  'Feature Limitation'),
        ('na',                  'N/A'),
    ], tracking=True)

    # ── Reproduction detail ───────────────────────────────────────
    steps = fields.Text(string='Steps to Reproduce')
    expected_result = fields.Text(string='Expected Result')
    observed_result = fields.Text(string='Observed Result')
    note = fields.Text(string='Note')
    suggested_fix = fields.Text(string='Suggested Fix')

    ci_error_log = fields.Html(string='CI Error Log')

    # ── Source / traceability ─────────────────────────────────────
    source = fields.Selection([
        ('ci',          'CI/CD'),
        ('manual',      'Manual'),
        ('report_link', 'Report Link'),
    ], default='ci', required=True)
    ci_run_url = fields.Char(string='CI Run URL')
    ci_commit_sha = fields.Char(string='Commit SHA')
    ci_branch = fields.Char(string='Branch')
    report_share_url = fields.Char(string='Report URL')
    component_a_bug_id = fields.Char(string='Report Bug ID')

    # ── Relations ─────────────────────────────────────────────────
    report_id = fields.Many2one('qa.report', string='Report', ondelete='cascade', index=True)
    evidence_ids = fields.One2many('qa.bug.evidence', 'ticket_id', string='Evidence')
    evidence_gallery_html = fields.Html(
        compute='_compute_evidence_gallery_html', sanitize=False
    )
    assignee_id = fields.Many2one('res.users', string='Assignee', tracking=True)
    reporter = fields.Char(string='Reporter', default='ci-bot')
    resolved_at = fields.Datetime(string='Resolved At', readonly=True)

    @api.depends('evidence_ids.url', 'evidence_ids.caption', 'evidence_ids.kind')
    def _compute_evidence_gallery_html(self):
        for rec in self:
            shots = rec.evidence_ids.filtered(lambda e: e.kind == 'screenshot' and e.url)
            if not shots:
                rec.evidence_gallery_html = Markup(
                    '<p class="text-muted fst-italic">No evidence images attached.</p>'
                )
                continue
            cards = []
            for ev in shots:
                url     = (ev.url     or '').replace('"', '%22')
                caption = (ev.caption or '').replace('<', '&lt;').replace('>', '&gt;')
                cards.append(Markup(
                    f'<div class="qa-evidence-card">'
                    f'<div class="qa-evidence-thumb">'
                    f'<img src="{url}" alt="{caption}" loading="lazy"/>'
                    f'</div>'
                    f'<div class="qa-evidence-caption">{caption}</div>'
                    f'</div>'
                ))
            rec.evidence_gallery_html = Markup(
                '<div class="qa-evidence-gallery"><div class="qa-evidence-grid">'
                + ''.join(cards)
                + '</div></div>'
            )

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env.ref('qa_bug_management.seq_qa_bug_ticket', raise_if_not_found=False)
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (seq.sudo().next_by_id() if seq else None) or 'New'
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('status') in ('fixed', 'closed', 'rejected'):
            vals['resolved_at'] = fields.Datetime.now()
        return super().write(vals)

    def action_open_ci_run(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_url', 'url': self.ci_run_url, 'target': 'new'}

    def action_open_report(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_url', 'url': self.report_share_url, 'target': 'new'}

    def action_upload_evidence_image(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Upload Image',
            'res_model': 'qa.evidence.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_ticket_id': self.id},
        }
