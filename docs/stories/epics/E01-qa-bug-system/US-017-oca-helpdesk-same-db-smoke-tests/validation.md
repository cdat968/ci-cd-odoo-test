# Validation

## Proof Strategy

Prove that OCA Helpdesk and the custom QA bug module install into one Odoo
database and can create their core records without bridge behavior.

## Test Cases

- Registry contains `helpdesk.ticket`.
- Registry contains `helpdesk.ticket.team`.
- Registry contains `qa.bug.ticket`.
- Registry contains `project.project` and `project.task`.
- `helpdesk_mgmt_project` fields are loaded on Helpdesk models.
- Create a `helpdesk.ticket` linked to a `project.project`.
- Create a `qa.bug.ticket` in the same database.

## Commands

```text
python3 scripts/verify_oca_helpdesk_vendor.py
bash -n scripts/run_oca_helpdesk_smoke_tests.sh
bash -n scripts/run_odoo_tests.sh
docker compose -f docker-compose.test.yml config
bash scripts/run_oca_helpdesk_smoke_tests.sh
```

## Acceptance Evidence

- `python3 scripts/verify_oca_helpdesk_vendor.py` passed.
- `bash -n scripts/run_oca_helpdesk_smoke_tests.sh` passed.
- `bash -n scripts/run_odoo_tests.sh` passed.
- Python manifest parse confirmed `qa_helpdesk_smoke_tests` depends on
  `qa_bug_management`, `helpdesk_mgmt`, and `helpdesk_mgmt_project`.
- Text check confirmed `docker-compose.test.yml` contains the
  `odoo_helpdesk_smoke` service, installs `qa_helpdesk_smoke_tests`, and runs
  `--test-tags /qa_helpdesk_smoke_tests`.
- `docker compose -f docker-compose.test.yml config` was not runnable on this
  local machine because `docker` is not installed in the shell environment; the
  GitHub Actions runner remains the Docker validation environment.
