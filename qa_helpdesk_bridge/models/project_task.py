from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    qa_bug_id = fields.Many2one(
        'qa.bug.ticket',
        string='QA Bug',
        copy=False,
        readonly=True,
    )

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
