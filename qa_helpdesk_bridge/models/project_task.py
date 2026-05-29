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

    def _sync_qa_bug_assignee(self):
        if self.env.context.get('skip_qa_bug_sync'):
            return
        if not self.env.user.has_group('qa_bug_management.group_qa_manager'):
            return
        for task in self.filtered('qa_bug_id'):
            assignee = task.user_ids[:1]
            task.qa_bug_id.with_context(skip_qa_task_sync=True).write({
                'assignee_id': assignee.id if assignee else False,
            })

    def write(self, vals):
        res = super().write(vals)
        if 'user_ids' in vals:
            self._sync_qa_bug_assignee()
        return res
