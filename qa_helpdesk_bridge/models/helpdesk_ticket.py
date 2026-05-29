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
            })
            self.sudo().qa_bug_id = bug.id
        return self.action_open_qa_bug()

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
