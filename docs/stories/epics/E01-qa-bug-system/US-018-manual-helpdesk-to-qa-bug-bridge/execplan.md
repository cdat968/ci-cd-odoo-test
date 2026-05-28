# Execution Plan

## Step 1

What will change: Add `qa_helpdesk_bridge`.
Why it is necessary: The system needs a real bridge after vendor/install proof.
Risk: Model links and view inheritance may break Odoo install.
Validation: Dedicated bridge tests and Odoo install in CI.
Rollback: Remove the bridge addon and CI step.
Owner: Codex.

## Step 2

What will change: Add manual Create/Open QA Bug actions.
Why it is necessary: Not every Helpdesk ticket is a QA defect.
Risk: Duplicate creation or incorrect access assumptions.
Validation: Idempotency tests and action result assertions.
Rollback: Disable buttons/remove addon.
Owner: Codex.
