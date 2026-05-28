# US-012 report_share_url populate fix

## Status

implemented

## Lane

normal

## Product Contract

Every `qa.bug.ticket` created via `POST /qa/ci/report` must have `report_share_url`
set to the external webapp URL (`/r/{report_id}?t={share_token}`) so QA users
can click through to the landing page report directly from the bug ticket.

## Relevant Product Docs

- `qa_bug_management/controllers/ci_intake.py`
- `qa_bug_management/views/qa_bug_ticket_views.xml`

## Acceptance Criteria

- `share_url` is computed from `BASE_WEBAPP_URL` env var immediately after `qa.report.create()`.
- Every `qa.bug.ticket` created in the loop receives `report_share_url = share_url`.
- "Open Report" button in CI Info tab navigates to the webapp report page.
- If `BASE_WEBAPP_URL` is not set, `report_share_url` is empty string (no crash).

## Design Notes

- Fix location: `ci_intake.py → ci_report()`, compute `share_url` before the bug loop.
- `BASE_WEBAPP_URL` must be exported in the terminal running Odoo before startup.
- Existing tickets created before this fix retain empty `report_share_url`.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | — |
| Integration | Trigger CI with test failure → verify `report_share_url` populated on new ticket |
| E2E | Click "Open Report" in CI Info tab → webapp report page loads |

## Harness Delta

Decision 0012 recorded.

## Evidence

Implemented 2026-05-28. `share_url` computation moved before bug ticket creation loop in `ci_intake.py`.
