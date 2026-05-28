# US-011 Smoke test DELETE cleanup

## Status

implemented

## Lane

normal

## Product Contract

Every CI smoke test run must leave the production database clean. Test records
created during the smoke test must be deleted before the job finishes, whether
the test passes or fails.

## Relevant Product Docs

- `qa_bug_management/controllers/report_api.py`
- `scripts/smoke_test_webapp.py`
- `.github/workflows/ci.yml`

## Acceptance Criteria

- `DELETE /qa/api/report/<id>` endpoint exists, requires X-CI-Key auth, returns `{status: deleted}`.
- `smoke_test_webapp.py` wraps all steps in try/finally — cleanup always runs.
- After smoke test completes (pass or fail), no `qa.report` or `qa.bug.ticket` record from the run remains in DB.
- Wrong CI key returns 403. Non-existent ID returns 404.

## Design Notes

- Controller: `DELETE /qa/api/report/<int:report_id>` in `report_api.py`, auth via `_ci_auth()`.
- `qa.bug.ticket` auto-cascade deletes via `ondelete='cascade'` on `report_id`.
- Smoke test: `report_id` captured from Step 1 response, deleted in `finally` block.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | — |
| Integration | Manual: trigger CI, verify no record in Odoo after run |
| E2E | Smoke test itself passes without leaving records |

## Harness Delta

Decision 0011 recorded.

## Evidence

Implemented 2026-05-28. DELETE endpoint added to `report_api.py`. `smoke_test_webapp.py` updated with try/finally cleanup.
