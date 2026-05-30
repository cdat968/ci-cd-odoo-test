from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    qa_bug_id = fields.Many2one(
        'qa.bug.ticket',
        string='QA Bug',
        copy=False,
        readonly=True,
    )

    def action_create_qa_bug(self):
        self.ensure_one()
        if not self.qa_bug_id:
            reporter = (
                self.partner_id.display_name
                or self.user_id.display_name
                or self.create_uid.display_name
            )
            bug = self.env['qa.bug.ticket'].sudo().create({
                'title': self.name,
                'description': self.description,
                'source': 'manual',
                'reporter': reporter,
                'helpdesk_ticket_id': self.id,
                'project_id': self.project_id.id,
                'assignee_id': self.user_id.id,
            })
            self._create_qa_bug_evidence_from_attachments(bug)
            if self.env.user.has_group('qa_bug_management.group_qa_manager'):
                bug.with_user(self.env.user)._auto_create_or_sync_project_task()
            self.sudo().qa_bug_id = bug.id
        return self.action_open_qa_bug()

    def _sync_qa_bug_assignee(self):
        if not self.env.user.has_group('qa_bug_management.group_qa_manager'):
            return
        for ticket in self.filtered('qa_bug_id'):
            ticket.qa_bug_id.write({'assignee_id': ticket.user_id.id or False})

    def write(self, vals):
        res = super().write(vals)
        if 'user_id' in vals:
            self._sync_qa_bug_assignee()
        return res

    def _create_qa_bug_evidence_from_attachments(self, bug):
        for attachment in self.attachment_ids:
            attachment.sudo().generate_access_token()
            self.env['qa.bug.evidence'].sudo().create({
                'ticket_id': bug.id,
                'kind': attachment.mimetype or 'application/octet-stream',
                'attachment_id': attachment.id,
                'caption': attachment.name or self.name,
            })

    def action_open_qa_bug(self):
        self.ensure_one()
        if not self.qa_bug_id:
            return False
        action = self.env.ref('qa_bug_management.action_qa_bug_ticket').sudo().read()[0]
        action.update({
            'views': [(self.env.ref('qa_bug_management.view_qa_bug_ticket_form').id, 'form')],
            'res_id': self.qa_bug_id.id,
            'target': 'current',
        })
        return action
