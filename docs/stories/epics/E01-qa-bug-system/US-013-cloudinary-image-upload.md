# US-013 Image upload to Cloudinary from Odoo form

## Status

implemented

## Lane

normal

## Product Contract

QA users logged into Odoo can upload evidence screenshots directly from the
bug ticket Evidence tab. Images are stored on Cloudinary; only the URL and
Cloudinary public_id are persisted in the Odoo database.

## Relevant Product Docs

- `qa_bug_management/models/qa_bug_evidence.py`
- `qa_bug_management/wizard/qa_evidence_upload_wizard.py`
- `qa_bug_management/views/qa_evidence_upload_wizard_views.xml`
- `qa_bug_management/views/qa_bug_ticket_views.xml`

## Acceptance Criteria

- "Upload Image" button visible in Evidence tab when ticket is saved (has id).
- Clicking opens a wizard with file picker and caption field.
- On submit: file uploaded to Cloudinary folder `qa-evidence`, `qa.bug.evidence` record created with `kind=screenshot`, `url=secure_url`, `cloudinary_public_id`.
- If `CLOUDINARY_URL` env var is missing → `UserError` with clear message.
- If `cloudinary` Python package not installed → `UserError` with install instruction.

## Design Notes

- TransientModel `qa.evidence.upload.wizard`: fields `ticket_id`, `file_data` (Binary), `file_name`, `caption`.
- `action_upload()`: decode base64 → `cloudinary.uploader.upload()` → create evidence record → close wizard.
- Auth: Odoo session (`auth='user'`), no share_token needed.
- `CLOUDINARY_URL` format: `cloudinary://api_key:api_secret@cloud_name`.
- Must install `cloudinary` package in Odoo `.venv`: `pip install cloudinary`.
- `CLOUDINARY_URL` must be exported before starting Odoo.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | — |
| Integration | Upload image via wizard → verify `qa.bug.evidence` record created with Cloudinary URL |
| E2E | Image appears in Evidence gallery after upload |

## Harness Delta

Decision 0013 recorded.

## Evidence

Implemented 2026-05-28. Wizard model + view created. `cloudinary_public_id` field added to `qa.bug.evidence`.
