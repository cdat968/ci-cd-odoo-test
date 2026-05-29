# Design

## Evidence Storage

`qa.bug.evidence` now supports either:

- `url`: existing Cloudinary/external URL evidence.
- `attachment_id`: Odoo `ir.attachment` evidence linked from Helpdesk.

Attachment-backed evidence renders through:

```text
/web/image/ir.attachment/<id>/datas
```

## Bridge Behavior

`helpdesk.ticket.action_create_qa_bug()` creates a QA bug and then links any
image attachments from the Helpdesk ticket into `qa.bug.evidence`.

Only attachments with `mimetype` starting with `image/` are linked.

## Ownership

OCA Helpdesk remains responsible for customer upload and `ir.attachment`
creation. The custom bridge only references those attachments from QA Bug
evidence.
