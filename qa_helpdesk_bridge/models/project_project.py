from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    qa_bug_ids = fields.One2many(
        'qa.bug.ticket',
        'project_id',
        string='QA Bugs',
    )
    qa_bug_count = fields.Integer(
        string='QA Bug Count',
        compute='_compute_qa_bug_counts',
    )
    open_qa_bug_count = fields.Integer(
        string='Open QA Bug Count',
        compute='_compute_qa_bug_counts',
    )

    def _compute_qa_bug_counts(self):
        grouped = self.env['qa.bug.ticket']._read_group(
            [('project_id', 'in', self.ids)],
            ['project_id', 'status'],
            ['__count'],
        )
        counts = {project.id: {'total': 0, 'open': 0} for project in self}
        closed_statuses = {'fixed', 'closed', 'rejected'}
        for project, status, count in grouped:
            if not project:
                continue
            counts.setdefault(project.id, {'total': 0, 'open': 0})
            counts[project.id]['total'] += count
            if status not in closed_statuses:
                counts[project.id]['open'] += count

        for project in self:
            project.qa_bug_count = counts.get(project.id, {}).get('total', 0)
            project.open_qa_bug_count = counts.get(project.id, {}).get('open', 0)

    def action_view_qa_bugs(self):
        self.ensure_one()
        action = self.env.ref('qa_bug_management.action_qa_bug_ticket').sudo().read()[0]
        action.update({
            'display_name': f'{self.name} QA Bugs',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
                'search_default_project_id': self.id,
            },
        })
        return action
