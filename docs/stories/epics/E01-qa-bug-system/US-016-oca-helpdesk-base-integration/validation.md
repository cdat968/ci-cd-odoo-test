# Validation

## Proof Strategy

Prove that the selected OCA Helpdesk addons are vendored, discoverable by Odoo,
and do not break the existing QA bug test command.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Manifest files exist for vendored addons |
| Integration | Odoo addons path includes OCA Helpdesk root |
| E2E | CI can install/test `qa_bug_management` with the expanded addons path |
| Platform | GitHub Actions Docker Compose job mounts the OCA Helpdesk addon root |
| Performance | Compare CI timing with US-015 baseline |
| Logs/Audit | Harness trace records this integration slice |

## Fixtures

- Vendored OCA Helpdesk 18.0 source for `helpdesk_mgmt`.
- Vendored OCA Helpdesk 18.0 source for `helpdesk_mgmt_project`.
- Existing `qa_bug_management` module and tests.

## Commands

```text
find addons_oca/helpdesk -maxdepth 2 -name __manifest__.py -print
bash -n scripts/run_odoo_tests.sh
docker compose -f docker-compose.test.yml config
bash scripts/run_odoo_tests.sh
```

## Acceptance Evidence

- `python3 scripts/verify_oca_helpdesk_vendor.py` passed:
  `helpdesk_mgmt 18.0.1.16.12: ok`,
  `helpdesk_mgmt_project 18.0.1.3.0: ok`.
- `bash -n scripts/run_odoo_tests.sh` passed.
- Text check confirmed `docker-compose.test.yml` mounts
  `./addons_oca/helpdesk:/mnt/oca-helpdesk:ro` and includes
  `/mnt/oca-helpdesk` in `--addons-path`.
- `docker compose -f docker-compose.test.yml config` was not runnable on this
  local machine because `docker` is not installed in the shell environment; the
  GitHub Actions runner remains the validation environment for Docker.
