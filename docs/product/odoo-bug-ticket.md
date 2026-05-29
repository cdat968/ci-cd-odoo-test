# Odoo QA Bug Ticket System

Status: Proposed (US-001, Component B)
Owner: QA tooling

## Goal

Whenever the CI/CD pipeline fails a test against Component A (the QA Report
Web Platform), an actionable bug ticket should appear in Odoo automatically
so the QA Lead can triage it from the same UI used for manual bugs.

## Scope

- Component B does not host the report. It only watches CI and records bugs.
- Component B's CI is the system under test for Component A: it runs Odoo
  Python tests (module integrity, model invariants) and Component A smoke
  tests (`/api/health`, share link round-trip).
- OCA Helpdesk 18.0 is vendored as an integration candidate through
  `addons_oca/helpdesk`, but `qa.bug.ticket` remains the active QA/CI defect
  model until a bridge story explicitly links it with `helpdesk.ticket`.
- CI includes a test-only addon, `qa_helpdesk_smoke_tests`, to prove OCA
  Helpdesk and `qa_bug_management` can install in the same Odoo database.
- `qa_helpdesk_bridge` provides a manual bridge from `helpdesk.ticket` to
  `qa.bug.ticket`: QA creates the bug with a button, the link is stored both
  ways, and existing links open rather than creating duplicates.
- The bridge also lets a QA Manager create one linked `project.task` from a QA
  bug. Project forms expose a Bugs smart button and a Bugs tab when the project
  has QA bugs.
- Helpdesk image attachments are linked into QA Bug evidence as
  attachment-backed screenshots. Existing Cloudinary URL evidence remains
  supported.

## Module layout

```
addons/qa_bug_management/
  __init__.py
  __manifest__.py
  models/
    __init__.py
    qa_bug_ticket.py
    qa_bug_evidence.py
  views/
    qa_bug_ticket_views.xml
    qa_bug_ticket_menu.xml
  security/
    ir.model.access.csv
    qa_bug_security.xml
  data/
    qa_bug_sequence.xml
    qa_bug_stage_data.xml
  controllers/
    __init__.py
    ci_intake.py
  tests/
    __init__.py
    test_qa_bug_ticket.py
    test_ci_intake.py
```

## Models

### `qa.bug.ticket`

| Field | Type | Notes |
|---|---|---|
| name | Char | Auto-sequence `QA-BUG/####` |
| title | Char | required |
| description | Html | failure message + stack |
| severity | Selection | low / medium / high / critical |
| status | Selection | new / triaged / in_progress / fixed / wont_fix / duplicate |
| source | Selection | ci / manual / report_link |
| ci_run_url | Char | GitHub Actions run URL |
| ci_commit_sha | Char | |
| ci_branch | Char | |
| report_share_url | Char | link back into Component A when failure originated there |
| component_a_bug_id | Char | bug id inside the linked report payload |
| evidence_ids | One2many | qa.bug.evidence |
| assignee_id | Many2one(res.users) | |
| reporter | Char | "ci-bot" or user login |
| created_at | Datetime | default now |
| resolved_at | Datetime | set when status moves to fixed/wont_fix/duplicate |

### `qa.bug.evidence`

| Field | Type | Notes |
|---|---|---|
| ticket_id | Many2one(qa.bug.ticket) | required, ondelete=cascade |
| kind | Selection | screenshot / log / link |
| url | Char | Cloudinary URL or any link |
| caption | Char | |

## Controller (CI intake)

Single endpoint, key-gated, JSON-only:

```
POST /qa/ci/bug
  header: X-CI-Key: <env shared secret>
  body: {
    title, description, severity,
    ci_run_url, ci_commit_sha, ci_branch,
    report_share_url?, component_a_bug_id?,
    evidence: [ { kind, url, caption } ]
  }
  resp: { id, name }
```

Dedup rule: if a ticket with the same `ci_commit_sha` + `title` exists and is
not yet `fixed/wont_fix`, append the new run to its description instead of
creating a duplicate.

## Views

- List view: name, title, severity, status, ci_branch, assignee, created_at.
- Form view: header with status statusbar (kanban-style),
  description (Html widget), evidence one2many editable list, link buttons
  for `ci_run_url` and `report_share_url`.
- Kanban grouped by status.
- Search filters: severity, status, branch, "from CI", "from report".

## Security

- Group `group_qa_user`: read all, edit own assignments.
- Group `group_qa_manager`: full CRUD, manage sequence.
- `ir.model.access.csv` rows for both models per group.
- Record rules: managers see all; users see their assignments + unassigned.

## CI/CD flow (GitHub Actions)

```
on: push to any branch, pull_request to main

job: build
  - checkout
  - docker compose up -d  (Odoo 18 + Postgres, uses odoo18.conf)
  - wait for Odoo healthcheck

job: test-odoo
  - docker compose exec odoo odoo --test-enable --stop-after-init
      -d ci -i qa_bug_management
  - parse test output; on failure collect logs

job: test-component-a
  - run smoke test script against staging URL of Component A
      /api/health, create dummy report via X-Pipeline-Key,
      fetch /r/<id>?t=, PATCH a bug, re-fetch, assert persistence
  - capture screenshots via headless Chromium

job: report-failures
  if: failure()
  - for each captured failure, POST to /qa/ci/bug with
      ci_run_url, ci_commit_sha, ci_branch
  - upload screenshots to Cloudinary first, include URLs in evidence
```

Secrets: `CI_KEY`, `CLOUDINARY_URL`, `COMPONENT_A_PIPELINE_KEY`, `COMPONENT_A_BASE_URL`.

## Test strategy

### Unit (Odoo `--test-enable`)

- `test_qa_bug_ticket.py`: sequence assignment, status transitions
  (new → triaged → in_progress → fixed sets resolved_at), dedup rule.
- `test_ci_intake.py`: rejects missing X-CI-Key, parses payload, creates
  evidence rows, idempotent on same commit_sha + title.

### Integration

- `test_component_a_roundtrip.py` (in CI):
  POST report → fetch share link → PATCH bug Note + Resolution=Fixed →
  GET patches → assert status=Closed.

### Manual smoke (after deploy)

- Open share link from a clean browser, change Note, refresh, verify
  persistence. Open from another browser, verify edit visible.

## Out of scope (for now)

- Webhooks back to GitHub closing issues automatically.
- SLA tracking and escalation.
- Email digest of new CI bugs.
