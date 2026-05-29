# Validation

## Proof Strategy

Extend bridge tests to create image and non-image Helpdesk attachments, then
create a QA bug and assert only the image becomes QA evidence.

## Test Cases

- Helpdesk image attachment becomes `qa.bug.evidence`.
- Non-image Helpdesk attachment is ignored.
- Attachment-backed evidence has no Cloudinary URL.
- Existing evidence gallery renders `/web/image/ir.attachment/<id>/datas`.

## Acceptance Evidence

- Python compile passed for evidence model, ticket gallery, bridge logic, and
  bridge tests.
- XML parse passed for QA Bug view.
- Static search confirmed `attachment_id` support and bridge logic.
- Docker validation is expected on GitHub Actions because local `docker` is not
  available in this shell environment.
