# Validation

## Proof Strategy

Run a dedicated Odoo test service that installs `qa_helpdesk_bridge` and runs
only bridge tests.

## Test Cases

- Create a Helpdesk ticket.
- Call `action_create_qa_bug`.
- Assert `helpdesk.ticket.qa_bug_id` is set.
- Assert `qa.bug.ticket.helpdesk_ticket_id` points back to Helpdesk.
- Assert title, description, source, and reporter mapping are created.
- Call create again and assert no duplicate QA bug is created.
- Assert open actions return the linked records.

## Commands

```text
python3 scripts/verify_oca_helpdesk_vendor.py
bash -n scripts/run_qa_helpdesk_bridge_tests.sh
python3 -m py_compile qa_helpdesk_bridge/models/helpdesk_ticket.py qa_helpdesk_bridge/models/qa_bug_ticket.py qa_helpdesk_bridge/tests/test_helpdesk_bridge.py
docker compose -f docker-compose.test.yml config
bash scripts/run_qa_helpdesk_bridge_tests.sh
```

## Acceptance Evidence

- `python3 scripts/verify_oca_helpdesk_vendor.py` passed.
- `bash -n scripts/run_qa_helpdesk_bridge_tests.sh` passed.
- Existing smoke/Odoo shell syntax checks passed.
- Python manifest parse confirmed `qa_helpdesk_bridge` depends on
  `qa_bug_management`, `helpdesk_mgmt`, `helpdesk_mgmt_project`, and `project`.
- `python3 -m py_compile` passed for bridge models, bridge tests, and vendor
  verification script.
- XML parse passed for bridge Helpdesk and QA Bug inherited views.
- Text check confirmed `docker-compose.test.yml` contains the
  `odoo_helpdesk_bridge` service, installs `qa_helpdesk_bridge`, and runs
  `--test-tags /qa_helpdesk_bridge`.
- `docker compose -f docker-compose.test.yml config` was not runnable on this
  local machine because `docker` is not installed in the shell environment; the
  GitHub Actions runner remains the Docker validation environment.
