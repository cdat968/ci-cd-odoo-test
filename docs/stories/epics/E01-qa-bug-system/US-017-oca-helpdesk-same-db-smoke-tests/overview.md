# Overview

## Current Behavior

OCA Helpdesk is vendored and visible to Odoo through the Docker addons path.
CI does not yet prove that Helpdesk can install in the same database as
`qa_bug_management`.

## Target Behavior

CI installs a test-only addon that depends on `qa_bug_management`,
`helpdesk_mgmt`, and `helpdesk_mgmt_project`, then runs smoke tests proving
the models can coexist in one Odoo database.

## Non-Goals

- Do not create a bridge from `helpdesk.ticket` to `qa.bug.ticket`.
- Do not map Helpdesk attachments to QA evidence.
- Do not replace the existing QA bug ticket workflow.
