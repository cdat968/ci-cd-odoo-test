# Overview

## Current Behavior

The project has a custom `qa_bug_management` Odoo module for QA/CI defect
tracking. OCA Helpdesk is not present in the repository and Docker only mounts
`qa_bug_management` as an extra addon.

## Target Behavior

The repository vendors the selected OCA Helpdesk 18.0 addons and CI/Odoo can
discover them through the configured addons path. The current QA bug workflow
continues to run unchanged.

## Affected Users

- QA engineer maintaining Odoo bug workflow.
- Developer running CI for Odoo module tests.
- Future support user who will use OCA Helpdesk after bridge work.

## Affected Product Docs

- `SYSTEM_OVERVIEW.md`
- `docs/product/odoo-bug-ticket.md`

## Non-Goals

- Do not create Helpdesk-to-QA Bug bridge behavior in this story.
- Do not replace `qa.bug.ticket`.
- Do not migrate existing QA bug data.
