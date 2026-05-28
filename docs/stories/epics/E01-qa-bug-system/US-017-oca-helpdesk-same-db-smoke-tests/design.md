# Design

## Module

`qa_helpdesk_smoke_tests` is a test-only addon. It is installable in CI and has
no production menus, models, controllers, or data.

## Dependencies

- `qa_bug_management`
- `helpdesk_mgmt`
- `helpdesk_mgmt_project`

Installing the smoke addon forces Odoo to install the custom QA bug module and
the selected OCA Helpdesk addons in the same database.

## Docker Flow

`odoo_helpdesk_smoke` uses the same `ci_test` database name and addons paths as
the existing Odoo test service, but runs a dedicated command:

```text
-i qa_helpdesk_smoke_tests --test-tags /qa_helpdesk_smoke_tests
```

The existing `odoo` service remains responsible for the current
`qa_bug_management` test run.
