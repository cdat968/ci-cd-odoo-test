# Execution Plan

## Step 1

What will change: Add `attachment_id` support to `qa.bug.evidence`.
Why it is necessary: Helpdesk customer uploads are stored as Odoo attachments.
Risk: Existing Cloudinary URL evidence rendering could regress.
Validation: compile, XML parse, bridge evidence tests.
Rollback: remove attachment field and bridge linking.
Owner: Codex.

## Step 2

What will change: Link Helpdesk image attachments when creating QA bugs.
Why it is necessary: QA managers expect customer screenshots to appear on the
created QA bug.
Risk: Non-image files could be incorrectly shown as screenshots.
Validation: image-only test coverage.
Rollback: disable `_create_qa_bug_evidence_from_attachments`.
Owner: Codex.
