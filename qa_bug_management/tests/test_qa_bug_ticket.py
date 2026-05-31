from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestQaBugTicket(TransactionCase):

    def test_sequence_assigned_on_create(self):
        ticket = self.env['qa.bug.ticket'].create({'title': 'Test bug'})
        self.assertRegex(ticket.name, r'QA-BUG/\d{4}')

    def test_resolved_at_set_on_fixed(self):
        ticket = self.env['qa.bug.ticket'].create({'title': 'Fix me'})
        self.assertFalse(ticket.resolved_at)
        ticket.write({'status': 'fixed'})
        self.assertTrue(ticket.resolved_at)

    def test_resolved_at_set_on_rejected(self):
        ticket = self.env['qa.bug.ticket'].create({'title': 'Skip'})
        ticket.write({'status': 'rejected'})
        self.assertTrue(ticket.resolved_at)

    def test_resolved_at_set_on_closed(self):
        ticket = self.env['qa.bug.ticket'].create({'title': 'Dupe'})
        ticket.write({'status': 'closed'})
        self.assertTrue(ticket.resolved_at)

    def test_evidence_cascade_delete(self):
        ticket = self.env['qa.bug.ticket'].create({
            'title': 'With evidence',
            'evidence_ids': [(0, 0, {'kind': 'link', 'url': 'https://example.com'})],
        })
        evidence_id = ticket.evidence_ids.id
        ticket.unlink()
        self.assertFalse(self.env['qa.bug.evidence'].browse(evidence_id).exists())

    def test_default_severity_s3_minor(self):
        ticket = self.env['qa.bug.ticket'].create({'title': 'Default severity'})
        self.assertEqual(ticket.severity, 's3_minor')

    def test_default_status_new(self):
        ticket = self.env['qa.bug.ticket'].create({'title': 'Default status'})
        self.assertEqual(ticket.status, 'new')

    def test_default_source_ci(self):
        ticket = self.env['qa.bug.ticket'].create({'title': 'Default source'})
        self.assertEqual(ticket.source, 'ci')

    def test_resolved_at_not_set_when_in_progress(self):
        ticket = self.env['qa.bug.ticket'].create({'title': 'In progress'})
        ticket.write({'status': 'in_progress'})
        self.assertFalse(ticket.resolved_at)

    # def test_intentional_failure_delete_me(self):
    #     """Intentional fail to test CI → Odoo report pipeline."""
    #     self.assertEqual(1, 2, "This failure is intentional — delete after testing")
