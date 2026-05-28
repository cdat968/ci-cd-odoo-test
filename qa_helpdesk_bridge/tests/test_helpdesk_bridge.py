from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestHelpdeskBridge(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].sudo().create({
            'name': 'Phase 3 Bridge Project',
        })
        cls.team = cls.env['helpdesk.ticket.team'].sudo().create({
            'name': 'Phase 3 Bridge Team',
            'default_project_id': cls.project.id,
        })
        cls.stage = cls.env.ref('helpdesk_mgmt.helpdesk_ticket_stage_new')
        cls.channel = cls.env.ref('helpdesk_mgmt.helpdesk_ticket_channel_web')

    def _create_helpdesk_ticket(self):
        return self.env['helpdesk.ticket'].sudo().create({
            'name': 'Customer reports checkout failure',
            'description': 'Checkout button returns a server error.',
            'team_id': self.team.id,
            'stage_id': self.stage.id,
            'channel_id': self.channel.id,
            'project_id': self.project.id,
        })

    def test_create_qa_bug_from_helpdesk_ticket(self):
        ticket = self._create_helpdesk_ticket()

        action = ticket.action_create_qa_bug()

        self.assertTrue(ticket.qa_bug_id)
        self.assertEqual(ticket.qa_bug_id.helpdesk_ticket_id, ticket)
        self.assertEqual(ticket.qa_bug_id.title, ticket.name)
        self.assertEqual(ticket.qa_bug_id.description, ticket.description)
        self.assertEqual(ticket.qa_bug_id.source, 'manual')
        self.assertEqual(action['res_id'], ticket.qa_bug_id.id)

    def test_create_qa_bug_is_idempotent(self):
        ticket = self._create_helpdesk_ticket()

        ticket.action_create_qa_bug()
        first_bug = ticket.qa_bug_id
        ticket.action_create_qa_bug()

        self.assertEqual(ticket.qa_bug_id, first_bug)
        self.assertEqual(
            self.env['qa.bug.ticket'].sudo().search_count([
                ('helpdesk_ticket_id', '=', ticket.id),
            ]),
            1,
        )

    def test_open_actions_return_linked_records(self):
        ticket = self._create_helpdesk_ticket()
        ticket.action_create_qa_bug()
        bug = ticket.qa_bug_id

        qa_action = ticket.action_open_qa_bug()
        helpdesk_action = bug.action_open_helpdesk_ticket()

        self.assertEqual(qa_action['res_model'], 'qa.bug.ticket')
        self.assertEqual(qa_action['res_id'], bug.id)
        self.assertEqual(helpdesk_action['res_model'], 'helpdesk.ticket')
        self.assertEqual(helpdesk_action['res_id'], ticket.id)
