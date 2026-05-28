from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestHelpdeskCoexistence(TransactionCase):

    def test_helpdesk_and_qa_bug_models_coexist(self):
        for model_name in (
            'helpdesk.ticket',
            'helpdesk.ticket.team',
            'qa.bug.ticket',
            'project.project',
            'project.task',
        ):
            self.assertIn(model_name, self.env.registry.models)

    def test_create_helpdesk_ticket_with_project_and_qa_bug_ticket(self):
        HelpdeskTicket = self.env['helpdesk.ticket'].sudo()
        HelpdeskTeam = self.env['helpdesk.ticket.team'].sudo()
        Project = self.env['project.project'].sudo()
        QaBugTicket = self.env['qa.bug.ticket'].sudo()

        self.assertIn('project_id', HelpdeskTicket._fields)
        self.assertIn('task_id', HelpdeskTicket._fields)
        self.assertIn('default_project_id', HelpdeskTeam._fields)

        project = Project.create({'name': 'Phase 2 Helpdesk Smoke Project'})
        team = HelpdeskTeam.create({
            'name': 'Phase 2 Helpdesk Smoke Team',
            'default_project_id': project.id,
        })
        stage = self.env.ref('helpdesk_mgmt.helpdesk_ticket_stage_new')
        channel = self.env.ref('helpdesk_mgmt.helpdesk_ticket_channel_web')

        helpdesk_ticket = HelpdeskTicket.create({
            'name': 'Phase 2 Helpdesk Smoke Ticket',
            'description': 'Smoke test ticket for same-DB coexistence.',
            'team_id': team.id,
            'stage_id': stage.id,
            'channel_id': channel.id,
            'project_id': project.id,
        })

        qa_bug_ticket = QaBugTicket.create({
            'title': 'Phase 2 QA Bug Smoke Ticket',
            'description': 'QA bug still creates while OCA Helpdesk is installed.',
        })

        self.assertEqual(helpdesk_ticket.project_id, project)
        self.assertEqual(helpdesk_ticket.team_id.default_project_id, project)
        self.assertRegex(qa_bug_ticket.name, r'QA-BUG/\d{4}')
