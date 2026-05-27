# 0006 QA Report Web Platform Tech Stack

Date: 2026-05-26

## Status

Accepted

## Context

The QA team has an HTML report generator (13-skill pipeline ending in a
fully interactive HTML file) that today is shared by zipping the file
together with an evidence image folder and emailing it. This produces three
problems:

1. Evidence images are hardcoded in the HTML (base64 or relative paths),
   making reports heavy and brittle.
2. Sharing requires a multi-megabyte zip plus instructions for unzipping.
3. Recipients' edits to Note and Resolution are stored only in their own
   browser localStorage and disappear when the file is deleted.

The team wants a single shareable URL, free cloud image hosting, server-side
edit persistence, and no rebuild of existing interactive HTML features.

## Decision

- **Frontend**: keep existing rendered HTML + thin vanilla-JS client (`/static/client.js`) injected by backend. No React/Next/Vue/Svelte.
- **Backend**: FastAPI (Python 3.11+), Uvicorn, deployed on Render.
- **Image storage**: Cloudinary free tier (25 GB storage, 25 GB/mo bandwidth).
- **Database**: Supabase Postgres free tier (500 MB, JSONB for report payload).
- **Deploy**: Render Web Service free tier (750 hrs/mo).
- **Access**: unguessable share token in URL; no login system.
- **Pipeline**: two new optional steps in `testing_report_runner.py` — upload evidence to Cloudinary, POST to backend, receive share URL.

## Alternatives Considered

1. **Next.js full rewrite** — Rejected. HTML already implements all interactive features. Porting to React risks regressions with zero new user value.
2. **Express/Node backend** — Rejected. Pipeline is Python; one language end-to-end avoids a second toolchain.
3. **Supabase Storage for images** — Rejected. 1 GB too small for evidence-heavy reports; no on-the-fly transformations.
4. **Cloudflare R2** — Rejected as default. Requires Worker or custom domain for clean public URLs; more setup than Cloudinary.
5. **Neon Postgres** — Rejected. Autosuspend adds latency on first request; recipient experience matters.
6. **Vercel deploy** — Rejected. FastAPI on Vercel runs as serverless functions, complicating connection pooling and static file serving.
7. **Railway/Fly.io** — Rejected. Railway removed indefinite free tier; Fly.io requires credit card.
8. **Login instead of share tokens** — Rejected for v1. Stakeholders should not need accounts to read a bug report.
9. **Keep zip + email, only add cloud images** — Rejected. Solves file-size but leaves edits stranded in localStorage.

## Consequences

Positive:
- Authors share one URL; recipients see live server-backed state.
- Zero JS framework rebuild risk; all interactivity keeps working.
- Single language (Python) from skill 1 through backend.
- All four infra dependencies stay on free tiers with comfortable headroom.

Tradeoffs:
- Render free tier sleeps after 15 min idle (~30 s cold start on first request).
- Supabase DB pauses after 7 days inactivity; weekly `/api/health` ping from CI keeps it warm.
- Cloudinary lock-in for evidence URLs; migration requires rewriting historical payloads.
- Share-token-only access: anyone with URL can read and edit.

## Follow-Up

- Add `--no-publish` flag to `testing_report_runner.py` for offline use.
- Implement SlowAPI rate-limiting on PATCH endpoints.
- Add weekly cron (GitHub Actions schedule) hitting `/api/health` to keep Supabase warm.
- Track Cloudinary quota; add retention policy if usage > 50% free tier.
