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

    def test_create_qa_bug_from_assigned_helpdesk_ticket_creates_developer_task(self):
        ticket = self._create_helpdesk_ticket()
        ticket.with_user(self.qa_manager).write({'user_id': self.developer.id})

        ticket.with_user(self.qa_manager).action_create_qa_bug()

        self.assertEqual(ticket.qa_bug_id.assignee_id, self.developer)
        self.assertTrue(ticket.qa_bug_id.project_task_id)
        self.assertEqual(ticket.qa_bug_id.project_task_id.user_ids, self.developer)

    def test_helpdesk_assignee_syncs_to_existing_qa_bug_and_project_task(self):
        ticket = self._create_helpdesk_ticket()
        ticket.action_create_qa_bug()
        bug = ticket.qa_bug_id

        ticket.with_user(self.qa_manager).write({'user_id': self.developer.id})

        self.assertEqual(bug.assignee_id, self.developer)
        self.assertTrue(bug.project_task_id)
        self.assertEqual(bug.project_task_id.user_ids, self.developer)

    def test_create_qa_bug_links_helpdesk_attachments_as_typed_evidence(self):
        ticket = self._create_helpdesk_ticket()
        image_attachment = self.env['ir.attachment'].sudo().create({
            'name': 'customer-screenshot.png',
            'datas': base64.b64encode(b'fake image bytes'),
            'mimetype': 'image/png',
            'res_model': 'helpdesk.ticket',
            'res_id': ticket.id,
        })
        log_attachment = self.env['ir.attachment'].sudo().create({
            'name': 'customer-log.txt',
            'datas': base64.b64encode(b'not an image'),
            'mimetype': 'text/plain',
            'res_model': 'helpdesk.ticket',
            'res_id': ticket.id,
        })

        ticket.action_create_qa_bug()

        evidence = ticket.qa_bug_id.evidence_ids
        self.assertEqual(len(evidence), 2)
        self.assertTrue(image_attachment.access_token)
        self.assertTrue(log_attachment.access_token)
        self.assertEqual(
            evidence.filtered(lambda ev: ev.attachment_id == image_attachment).kind,
            'image/png',
        )
        self.assertEqual(
            evidence.filtered(lambda ev: ev.attachment_id == log_attachment).kind,
            'text/plain',
        )
        self.assertIn(
            f'/web/content/{image_attachment.id}?download=false&access_token={image_attachment.access_token}',
            ticket.qa_bug_id.evidence_gallery_html,
        )
        self.assertNotIn(
            f'/web/content/{log_attachment.id}?download=false&access_token={log_attachment.access_token}',
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

    def test_assigning_bug_auto_creates_project_task_for_developer(self):
        bug = self.env['qa.bug.ticket'].sudo().create({
            'title': 'Assign creates task',
            'project_id': self.project.id,
        })

        bug.with_user(self.qa_manager).write({'assignee_id': self.developer.id})

        self.assertTrue(bug.project_task_id)
        self.assertEqual(bug.project_task_id.project_id, self.project)
        self.assertEqual(bug.project_task_id.user_ids, self.developer)

    def test_reassigning_bug_syncs_existing_project_task(self):
        other_developer = new_test_user(
            self.env,
            login='phase4-other-developer',
            groups='qa_bug_management.group_qa_user,project.group_project_user',
        )
        bug = self.env['qa.bug.ticket'].sudo().create({
            'title': 'Reassign syncs task',
            'project_id': self.project.id,
            'assignee_id': self.developer.id,
        })
        bug.with_user(self.qa_manager).action_create_project_task()

        bug.with_user(self.qa_manager).write({'assignee_id': other_developer.id})

        self.assertEqual(bug.project_task_id.user_ids, other_developer)

    def test_project_task_assignee_syncs_back_to_qa_bug(self):
        bug = self.env['qa.bug.ticket'].sudo().create({
            'title': 'Task syncs back to bug',
            'project_id': self.project.id,
        })
        bug.with_user(self.qa_manager).action_create_project_task()

        bug.project_task_id.with_user(self.qa_manager).write({
            'user_ids': [(6, 0, [self.developer.id])],
        })

        self.assertEqual(bug.assignee_id, self.developer)

    def test_developer_opens_qa_bug_after_project_task_assignment(self):
        bug = self.env['qa.bug.ticket'].sudo().create({
            'title': 'Open bug from assigned task',
            'project_id': self.project.id,
        })
        bug.with_user(self.qa_manager).action_create_project_task()
        bug.project_task_id.with_user(self.qa_manager).write({
            'user_ids': [(6, 0, [self.developer.id])],
        })

        action = bug.project_task_id.with_user(self.developer).action_open_qa_bug()

        self.assertEqual(action['res_model'], 'qa.bug.ticket')
        self.assertEqual(action['res_id'], bug.id)
        self.assertEqual(
            self.env['qa.bug.ticket'].with_user(self.developer).browse(bug.id).read(['name'])[0]['id'],
            bug.id,
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

    def test_developer_reads_only_assigned_qa_bugs(self):
        assigned_bug = self.env['qa.bug.ticket'].sudo().create({
            'title': 'Assigned to developer',
            'project_id': self.project.id,
            'assignee_id': self.developer.id,
        })
        unassigned_bug = self.env['qa.bug.ticket'].sudo().create({
            'title': 'Unassigned bug',
            'project_id': self.project.id,
        })
        other_bug = self.env['qa.bug.ticket'].sudo().create({
            'title': 'Assigned elsewhere',
            'project_id': self.project.id,
            'assignee_id': self.qa_manager.id,
        })

        visible = self.env['qa.bug.ticket'].with_user(self.developer).search([])

        self.assertIn(assigned_bug, visible)
        self.assertNotIn(unassigned_bug, visible)
        self.assertNotIn(other_bug, visible)

    def test_developer_reads_only_assigned_bug_evidence(self):
        assigned_bug = self.env['qa.bug.ticket'].sudo().create({
            'title': 'Assigned evidence',
            'project_id': self.project.id,
            'assignee_id': self.developer.id,
        })
        assigned_evidence = self.env['qa.bug.evidence'].sudo().create({
            'ticket_id': assigned_bug.id,
            'kind': 'image/png',
            'url': 'https://example.com/assigned.png',
        })
        other_bug = self.env['qa.bug.ticket'].sudo().create({
            'title': 'Hidden evidence',
            'project_id': self.project.id,
        })
        other_evidence = self.env['qa.bug.evidence'].sudo().create({
            'ticket_id': other_bug.id,
            'kind': 'image/png',
            'url': 'https://example.com/hidden.png',
        })

        visible = self.env['qa.bug.evidence'].with_user(self.developer).search([])

        self.assertIn(assigned_evidence, visible)
        self.assertNotIn(other_evidence, visible)

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
