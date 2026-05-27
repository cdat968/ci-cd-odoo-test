# QA Report Web Platform

Status: Proposed (US-001)
Owner: QA tooling

## Goal

Replace today's "zip the HTML + image folder + email it" flow with a single
shareable link. The recipient should see the same interactive report (bug
modal, evidence viewer with zoom/red-box/arrows/step-callouts, editable Note
and Resolution, auto-status when Resolution=Fixed, zebra rows, failed-TC
highlight, navbar) and any edit they make should persist server-side so other
recipients see it too.

The Python pipeline (`testing_report_runner.py`) must continue to be the
single source of truth that emits the HTML. The platform only adds:

1. An image upload step before HTML generation.
2. A submit step that ships the HTML + structured report to the backend.
3. A backend that hosts the report, exposes edit endpoints, and serves the
   HTML with the latest edits merged in.

## Non-goals

- No login system. Access is by unguessable share token in the URL.
- No real-time collaboration. Last-write-wins per field is enough.
- No HTML rebuild in a JS framework. The existing template is kept.
- No paid infrastructure.

## Personas and primary flows

### Author (QA engineer running the pipeline)

```
run skills 1..12 → testing_report_runner.py
  → for each evidence image:
      POST image to Cloudinary (signed upload preset)
      receive secure_url
  → render HTML using cloud URLs (no base64, no relative paths)
  → POST /api/reports
      body: { report_id, title, html, payload (TCs, bugs, evidence map) }
  → backend returns share_url
  → author emails share_url to stakeholders
```

### Recipient (developer / PM / stakeholder)

```
open share_url
  → backend looks up report by id + token
  → returns HTML with the most recent edits server-side merged in
  → user clicks a bug row → modal opens (unchanged JS)
  → user changes Resolution → existing JS now calls
      PATCH /api/reports/{id}/bugs/{bug_id}
      with { resolution, note, updated_by_label }
  → backend persists, returns new computed status
  → JS updates the row in place
```

## Data model

Postgres (Supabase). Tables are intentionally few; bug-level edits are stored
as patches so we never overwrite the immutable original report payload.

```
report
  id            uuid       primary key
  share_token   text       random 32 chars, unique
  title         text
  html          text       rendered HTML from pipeline (immutable)
  payload      jsonb       structured report (TC list, bug list, evidence map)
  created_at    timestamptz
  created_by    text       free-form label from pipeline

bug_patch
  id            uuid       primary key
  report_id     uuid       fk report(id)
  bug_id        text       matches bug id inside payload
  note          text       nullable
  resolution    text       nullable; one of: Open, In Progress, Fixed,
                           Won't Fix, Duplicate
  status        text       derived; "Closed" when resolution = "Fixed",
                           else original
  updated_by    text       free-form label from cookie or query param
  updated_at    timestamptz

audit_log
  id            bigserial  primary key
  report_id     uuid
  bug_id        text
  field         text
  old_value     text
  new_value     text
  actor         text
  at            timestamptz
```

`bug_patch` has a unique index on `(report_id, bug_id)` and is upserted on
each edit. `audit_log` keeps the history.

## API endpoints

All under `/api`. Pydantic models validate every body.

```
POST   /api/reports
  auth: shared secret header X-Pipeline-Key (env var)
  body: { title, html, payload, created_by }
  resp: { id, share_url }

GET    /r/{report_id}?t={share_token}
  returns the stored HTML with a <script> block injecting current bug_patch
  state, plus a small client.js that rewires the existing Note/Resolution
  inputs to PATCH endpoints instead of localStorage.

GET    /api/reports/{report_id}/patches?t={share_token}
  resp: { patches: [ { bug_id, note, resolution, status, updated_at } ] }

PATCH  /api/reports/{report_id}/bugs/{bug_id}?t={share_token}
  body: { note?, resolution?, updated_by? }
  resp: { bug_id, note, resolution, status, updated_at }

GET    /api/health
  resp: { ok: true }
```

The share_token is required for every read and write. A missing or wrong
token returns 404 (not 401) so URLs cannot be enumerated.

## Image storage strategy

- Pipeline calls Cloudinary's signed upload from Python.
- Folder convention: `qa-reports/<report_id>/<step_id>-<n>.png`.
- Pipeline records `{ original_path, secure_url, public_id }` per evidence
  asset in the report payload's `evidence_map`.
- HTML template reads `secure_url` instead of base64 or relative path.
- Cloudinary transformations (`w_1600,q_auto,f_auto`) keep bandwidth low
  while preserving the zoom feature (full-resolution version fetched on
  demand by the evidence viewer).
- Deletion: a future `DELETE /api/reports/{id}` will call Cloudinary
  `destroy` per public_id to free quota.

## Free tier comparison

### Image storage

| Service | Free storage | Free bandwidth/mo | Transformations | Python SDK | Notes |
|---|---|---|---|---|---|
| Cloudinary | 25 GB | 25 GB | Yes (URL params) | Yes | Best for image-heavy QA reports. **Selected.** |
| Supabase Storage | 1 GB | 5 GB | No (manual) | Yes (supabase-py) | Too small; ties storage to DB project. |
| Cloudflare R2 | 10 GB | Free egress via Workers/public bucket | No | s3-compatible | Requires bucket public config + custom domain. More setup. |
| imgbb / Imgur | small / TOS risk | unknown | No | Unofficial | Not durable enough for QA evidence. |

### Database

| Service | Free DB | Egress | Cold start | Notes |
|---|---|---|---|---|
| Supabase Postgres | 500 MB | 5 GB | None (always on for active projects; paused after 7 days inactivity) | **Selected.** JSONB-friendly. |
| Neon | 3 GB | unlimited within fair use | Yes (autosuspend) | More storage, but suspend lag annoys recipients. |
| PlanetScale | n/a free | n/a | n/a | Removed free tier. Skip. |

### Deploy platform

| Service | Free compute | Cold start | Docker / Python | Notes |
|---|---|---|---|---|
| Render Web Service | 750 hrs/mo | ~30 s after 15 min idle | Native FastAPI + Dockerfile | **Selected.** Simplest for FastAPI. |
| Vercel | Generous JS | Functions only | Python via serverless functions (limits + cold start) | JS-first; awkward for FastAPI. |
| Railway | Trial credit only | n/a | Good | No longer indefinitely free. |
| Fly.io | 3 small machines | minimal | Good | Requires credit card; more ops. |

## Pipeline integration changes

`testing_report_runner.py` gains two small steps. The existing 13-skill chain
is unchanged.

```
existing:
  ... → skill 12 (HTML report) → write report.html locally

new:
  skill 12.5 (upload_evidence): for each image in evidence_map,
    cloudinary.uploader.upload(file, folder=..., public_id=...)
    rewrite evidence_map[i].url = response['secure_url']

  skill 12.6 (publish_report): requests.post(
    f"{BACKEND_URL}/api/reports",
    headers={"X-Pipeline-Key": env.PIPELINE_KEY},
    json={ "title": ..., "html": rendered, "payload": ..., "created_by": ... }
  )
  print share_url for the operator to copy into the email.
```

Both steps are skippable in offline mode (`--no-publish` flag) so local QA
authors can still produce an HTML-only report when needed.

## HTML template changes

Minimal. The existing JavaScript that today writes to `localStorage` is
replaced with a thin client (`/static/client.js`) the backend injects. The
client:

- On load: reads injected `window.__REPORT_PATCHES__` and applies note +
  resolution + status to each bug row.
- On Note blur / Resolution change: PATCHes the backend, then applies the
  returned status (auto "Closed" when resolution=Fixed) to the row.
- Keeps the bug modal, zoom, red-box, arrows, and step-callout behavior
  untouched.

A `data-bug-id` attribute is added to each bug row by the Python template so
the client can target rows reliably.

## Security and abuse

- Share token: 32 random chars (`secrets.token_urlsafe(24)`), stored as plain
  text in DB (low value; revocation is by rotation).
- `X-Pipeline-Key`: env-only shared secret for `POST /api/reports`.
- Rate limit PATCH: 60 / minute / share_token via SlowAPI in FastAPI.
- CORS: PATCH and GET are same-origin (served from the same Render app), so
  CORS stays restrictive.
- Audit log captures every field change.

## Open questions

- Should we let recipients identify themselves by typing a name once
  (stored in a cookie) so audit_log.actor is meaningful? Lean yes.
- Long-term image retention: do we expire reports after N days to stay under
  Cloudinary quota? Track in backlog.
