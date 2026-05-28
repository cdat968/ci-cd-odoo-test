# OCA Helpdesk Vendor Addons

Source: https://github.com/OCA/helpdesk
Branch: 18.0
Vendored on: 2026-05-28

This folder intentionally vendors only the OCA Helpdesk addons needed for the
first integration slice:

- `helpdesk_mgmt`
- `helpdesk_mgmt_project`

Current scope is addon availability for Odoo/CI. The project-specific bridge
between `helpdesk.ticket`, `qa.bug.ticket`, and `project.task` is not included
in this vendor folder.
