# Design

## Domain Model

OCA `helpdesk_mgmt` introduces `helpdesk.ticket`, teams, stages, categories,
channels, and related security concepts. `helpdesk_mgmt_project` adds project
selection/linkage behavior for Helpdesk. This story only vendors these models;
it does not link them to `qa.bug.ticket`.

## Application Flow

No application flow changes in this story. Existing CI still installs and tests
`qa_bug_management`.

## Interface Contract

No new routes or public API behavior are introduced by this story. OCA routes
become available only when the corresponding modules are installed in an Odoo
database.

## Data Model

Vendored modules define Odoo models and access rules. Tables are created only
when the modules are installed in a database. No migration of existing custom
QA bug records is performed.

## UI / Platform Impact

Docker Compose mounts an extra addon root for OCA Helpdesk. The Odoo command
adds that root to `--addons-path` so Odoo can discover the vendored addons.

## Observability

CI logs show whether the vendored OCA Helpdesk manifest/dependency check
succeeds before the Odoo Docker test step starts.

## Alternatives Considered

1. Git submodule — rejected for this phase because the user selected vendor
   folder for simpler CI checkout behavior.
2. Vendor entire OCA Helpdesk repo — deferred to keep scope small and reduce
   dependency noise.
3. Install OCA Helpdesk directly from GitHub during CI — rejected for this
   phase because CI should not depend on network source availability.
