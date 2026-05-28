# Execution Plan

## Step 1

What will change: Add a test-only Odoo addon for same-DB smoke tests.
Why it is necessary: Phase 1 only proved source/path availability.
Risk: Odoo dependency loading or test tags can be misconfigured.
Validation: Manifest parse and CI install.
Rollback: Remove `qa_helpdesk_smoke_tests`.
Owner: Codex.

## Step 2

What will change: Add Docker/CI command path for Helpdesk smoke tests.
Why it is necessary: GitHub Actions must prove install behavior.
Risk: Extra Docker service could affect existing `odoo` test service.
Validation: Existing script targets `odoo`; new script targets
`odoo_helpdesk_smoke`.
Rollback: Remove the CI step and service.
Owner: Codex.
