import base64

from odoo.tests import tagged
from odoo.tests import new_test_user
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError, UserError


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
        cls.qa_manager = new_test_user(
            cls.env,
            login='phase4-qa-manager',
            groups=(
                'qa_bug_management.group_qa_manager,'
                'helpdesk_mgmt.group_helpdesk_manager,'
                'project.group_project_manager'
            ),
        )
        cls.developer = new_test_user(
            cls.env,
            login='phase4-developer',
            groups='qa_bug_management.group_qa_user,project.group_project_user',
        )
        cls.customer = new_test_user(
            cls.env,
            login='phase4-customer',
            groups='base.group_portal',
        )

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
        self.assertEqual(ticket.qa_bug_id.project_id, self.project)
        self.assertEqual(action['res_id'], ticket.qa_bug_id.id)

    def test_create_qa_bug_links_helpdesk_image_attachments_as_evidence(self):
        ticket = self._create_helpdesk_ticket()
        image_attachment = self.env['ir.attachment'].sudo().create({
            'name': 'customer-screenshot.png',
            'datas': base64.b64encode(b'fake image bytes'),
            'mimetype': 'image/png',
            'res_model': 'helpdesk.ticket',
            'res_id': ticket.id,
        })
        self.env['ir.attachment'].sudo().create({
            'name': 'customer-log.txt',
            'datas': base64.b64encode(b'not an image'),
            'mimetype': 'text/plain',
            'res_model': 'helpdesk.ticket',
            'res_id': ticket.id,
        })

        ticket.action_create_qa_bug()

        evidence = ticket.qa_bug_id.evidence_ids
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence.attachment_id, image_attachment)
        self.assertFalse(evidence.url)
        self.assertIn(
            f'/web/image/ir.attachment/{image_attachment.id}/datas',
            ticket.qa_bug_id.evidence_gallery_html,
        )

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

    def test_create_project_task_from_manual_project(self):
        bug = self.env['qa.bug.ticket'].sudo().create({
            'title': 'Manual project bug',
            'description': 'Create a task from a manually selected project.',
            'project_id': self.project.id,
        })

        action = bug.with_user(self.qa_manager).action_create_project_task()

        self.assertTrue(bug.project_task_id)
        self.assertEqual(bug.project_task_id.project_id, self.project)
        self.assertEqual(bug.project_task_id.qa_bug_id, bug)
        self.assertEqual(action['res_model'], 'project.task')
        self.assertEqual(action['res_id'], bug.project_task_id.id)

    def test_create_project_task_uses_helpdesk_project(self):
        ticket = self._create_helpdesk_ticket()
        ticket.action_create_qa_bug()
        bug = ticket.qa_bug_id
        bug.project_id = False

        bug.with_user(self.qa_manager).action_create_project_task()

        self.assertEqual(bug.project_id, self.project)
        self.assertEqual(bug.project_task_id.project_id, self.project)

    def test_create_project_task_is_idempotent(self):
        bug = self.env['qa.bug.ticket'].sudo().create({
            'title': 'Idempotent task bug',
            'project_id': self.project.id,
        })

        bug.with_user(self.qa_manager).action_create_project_task()
        first_task = bug.project_task_id
        bug.with_user(self.qa_manager).action_create_project_task()

        self.assertEqual(bug.project_task_id, first_task)
        self.assertEqual(
            self.env['project.task'].sudo().search_count([('qa_bug_id', '=', bug.id)]),
            1,
        )

    def test_create_project_task_requires_project(self):
        bug = self.env['qa.bug.ticket'].sudo().create({
            'title': 'Bug without project',
        })

        with self.assertRaises(UserError):
            bug.with_user(self.qa_manager).action_create_project_task()

    def test_developer_cannot_create_project_task_from_qa_bug(self):
        bug = self.env['qa.bug.ticket'].sudo().create({
            'title': 'Developer cannot create task',
            'project_id': self.project.id,
            'assignee_id': self.developer.id,
        })

        with self.assertRaises(AccessError):
            bug.with_user(self.developer).action_create_project_task()

    def test_customer_cannot_read_qa_bug(self):
        bug = self.env['qa.bug.ticket'].sudo().create({
            'title': 'Customer cannot read bug',
            'project_id': self.project.id,
        })

        with self.assertRaises(AccessError):
            bug.with_user(self.customer).read(['name'])

    def test_project_bug_counts_and_open_action(self):
        open_bug = self.env['qa.bug.ticket'].sudo().create({
            'title': 'Open project bug',
            'project_id': self.project.id,
        })
        self.env['qa.bug.ticket'].sudo().create({
            'title': 'Closed project bug',
            'project_id': self.project.id,
            'status': 'closed',
        })

        self.project.invalidate_recordset(['qa_bug_count', 'open_qa_bug_count'])
        action = self.project.action_view_qa_bugs()

        self.assertEqual(self.project.qa_bug_count, 2)
        self.assertEqual(self.project.open_qa_bug_count, 1)
        self.assertEqual(action['res_model'], 'qa.bug.ticket')
        self.assertIn(('project_id', '=', self.project.id), action['domain'])
        self.assertIn(open_bug, self.project.qa_bug_ids)
