import base64

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


PNG_1X1 = base64.b64decode(
    b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII='
)


@tagged('post_install', '-at_install')
class TestQaEvidenceUploadWizard(TransactionCase):

    def test_rejects_non_image_attachment(self):
        ticket = self.env['qa.bug.ticket'].create({'title': 'Reject non image'})
        attachment = self.env['ir.attachment'].create({
            'name': 'payload.json',
            'datas': base64.b64encode(b'{"ok": true}'),
            'mimetype': 'application/json',
        })
        wizard = self.env['qa.evidence.upload.wizard'].create({
            'ticket_id': ticket.id,
            'attachment_ids': [(6, 0, [attachment.id])],
        })

        with self.assertRaises(UserError):
            wizard._get_validated_image_bytes(attachment, 128 * 1024 * 1024)

    def test_accepts_image_attachment(self):
        ticket = self.env['qa.bug.ticket'].create({'title': 'Accept image'})
        attachment = self.env['ir.attachment'].create({
            'name': 'screenshot.png',
            'datas': base64.b64encode(PNG_1X1),
            'mimetype': 'image/png',
        })
        wizard = self.env['qa.evidence.upload.wizard'].create({
            'ticket_id': ticket.id,
            'attachment_ids': [(6, 0, [attachment.id])],
        })

        file_bytes, mimetype = wizard._get_validated_image_bytes(
            attachment,
            128 * 1024 * 1024,
        )

        self.assertTrue(file_bytes)
        self.assertEqual(mimetype, 'image/png')
