from odoo import Command, fields, models, _
from odoo.exceptions import AccessError, UserError


class QaBugTicket(models.Model):
    _inherit = 'qa.bug.ticket'

    helpdesk_ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Helpdesk Ticket',
        copy=False,
        readonly=True,
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        copy=False,
    )
    project_task_id = fields.Many2one(
        'project.task',
        string='Project Task',
        copy=False,
        readonly=True,
    )

    def action_open_helpdesk_ticket(self):
        self.ensure_one()
        if not self.helpdesk_ticket_id:
            return False
        action = self.env.ref('helpdesk_mgmt.helpdesk_ticket_action').sudo().read()[0]
        action.update({
            'views': [(self.env.ref('helpdesk_mgmt.ticket_view_form').id, 'form')],
            'res_id': self.helpdesk_ticket_id.id,
            'target': 'current',
        })
        return action

    def _get_project_for_task(self):
        self.ensure_one()
        project = self.project_id or self.helpdesk_ticket_id.project_id
        if project and not self.project_id:
            self.project_id = project.id
        return project

    def action_create_project_task(self):
        self.ensure_one()
        if not self.env.user.has_group('qa_bug_management.group_qa_manager'):
            raise AccessError(_('Only QA Managers can create project tasks from QA bugs.'))

        if self.project_task_id:
            self._sync_project_task_assignee()
            return self.action_open_project_task()

        project = self._get_project_for_task()
        if not project:
            raise UserError(_('Select a project before creating a project task.'))

        vals = {
            'name': self.title,
            'description': self.description or '',
            'project_id': project.id,
            'qa_bug_id': self.id,
        }
        if self.assignee_id:
            vals['user_ids'] = [Command.set([self.assignee_id.id])]

        task = self.env['project.task'].create(vals)
        self.project_task_id = task.id
        return self.action_open_project_task()

    def _sync_project_task_assignee(self):
        if self.env.context.get('skip_qa_task_sync'):
            return
        for bug in self.filtered('project_task_id'):
            user_ids = bug.assignee_id.ids if bug.assignee_id else []
            bug.project_task_id.with_context(skip_qa_bug_sync=True).user_ids = [
                Command.set(user_ids)
            ]

    def _auto_create_or_sync_project_task(self):
        for bug in self:
            if bug.project_task_id:
                bug._sync_project_task_assignee()
                continue
            if not bug.assignee_id:
                continue
            project = bug._get_project_for_task()
            if project:
                bug.action_create_project_task()

    def write(self, vals):
        res = super().write(vals)
        if (
            'assignee_id' in vals
            and self.env.user.has_group('qa_bug_management.group_qa_manager')
            and not self.env.context.get('skip_qa_task_sync')
        ):
            self._auto_create_or_sync_project_task()
        return res

    def action_open_project_task(self):
        self.ensure_one()
        if not self.project_task_id:
            return False
        action = self.env.ref('project.action_view_task').sudo().read()[0]
        action.update({
            'views': [(False, 'form')],
            'res_id': self.project_task_id.id,
            'target': 'current',
        })
        return action
