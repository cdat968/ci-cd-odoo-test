# US-015 CI Docker Phase 1 Optimization

## Status

implemented

## Lane

normal

## Product Contract

The Odoo CI test job should keep the same pass/fail behavior while making
runtime bottlenecks easier to measure and reducing avoidable startup overhead.

## Relevant Product Docs

- `SYSTEM_OVERVIEW.md`
- `docs/product/odoo-bug-ticket.md`

## Acceptance Criteria

- Docker Compose healthcheck waits for Postgres readiness with lower latency.
- Odoo test execution is scoped to the `qa_bug_management` module tests.
- Test cleanup runs even when the Odoo container exits with failure.
- CI logs include separate timing for Docker image pull and Odoo test run.
- GitHub Actions caches pip downloads used by report upload/failure reporting.

## Design Notes

- Commands: `docker compose -f docker-compose.test.yml pull`, `bash scripts/run_odoo_tests.sh`.
- Queries: none.
- API: none.
- Tables: none.
- Domain rules: CI must still fail the job when Odoo tests fail.
- UI surfaces: none.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Shell syntax check for `scripts/run_odoo_tests.sh` |
| Integration | Docker Compose config render when Docker is available |
| E2E | GitHub Actions `test-odoo` job runs and reports timing |
| Platform | Docker image pull duration and Odoo test run duration appear in CI logs |
| Release | Harness trace records this maintenance change |

## Harness Delta

No Harness behavior changed. This story records the CI/Docker maintenance slice.

## Evidence

- `bash -n scripts/run_odoo_tests.sh` passed locally.
- `docker compose -f docker-compose.test.yml config` could not be run in the current shell because `docker` is not installed or not on `PATH`.
