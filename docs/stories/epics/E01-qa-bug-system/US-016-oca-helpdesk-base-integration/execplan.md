# Exec Plan

## Goal

Vendor the initial OCA Helpdesk 18.0 addons into the project and make them
visible to Odoo/CI without changing the current QA bug workflow.

## Scope

In scope:

- Add selected OCA Helpdesk addons under `addons_oca/helpdesk/`.
- Include `helpdesk_mgmt` and `helpdesk_mgmt_project` only.
- Update Docker Compose addon mounts and Odoo addons path.
- Add CI visibility/install checks that prove the vendored modules can be found.

Out of scope:

- No bridge module between `helpdesk.ticket`, `qa.bug.ticket`, and `project.task`.
- No customer workflow changes.
- No data migration.
- No production Odoo install.

## Risk Classification

Risk flags:

- Data model — OCA Helpdesk introduces new Odoo models/tables when installed.
- Authorization — OCA Helpdesk includes groups, record rules, and portal access.
- External systems — source is vendored from the OCA GitHub repository.
- Existing behavior — Docker/CI addon paths change.
- Weak proof — the environment may lack Docker locally; CI must prove full install.

Hard gates:

- Data model.
- Authorization.

## Work Phases

1. Discovery.
2. Design.
3. Validation planning.
4. Implementation.
5. Verification.
6. Harness update.

## Stop Conditions

Pause for human confirmation if:

- OCA addon dependencies require vendoring many additional addons.
- Existing QA bug tests require product behavior changes to pass.
- OCA license or dependency shape changes the intended integration direction.
- Validation requirements need to be weakened.
