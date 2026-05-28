# US-014 Evidence gallery with lightbox viewer

## Status

implemented

## Lane

normal

## Product Contract

The Evidence tab on a bug ticket displays uploaded screenshots as a responsive
3-column thumbnail gallery. Clicking any thumbnail opens a fullscreen lightbox
with caption, prev/next navigation (keyboard and button), counter, and ESC/close.

## Relevant Product Docs

- `qa_bug_management/models/qa_bug_ticket.py`
- `qa_bug_management/static/src/js/evidence_lightbox.js`
- `qa_bug_management/static/src/css/evidence_gallery.css`
- `qa_bug_management/views/qa_bug_ticket_views.xml`

## Acceptance Criteria

- Screenshots display as 3-column responsive thumbnail grid (1 column on mobile).
- Clicking a thumbnail opens lightbox overlay with dark background.
- Caption shown above image in lightbox.
- `←` `→` arrow keys navigate between images.
- Prev/Next buttons on sides of image, disabled at boundary.
- Counter shows `current / total` (e.g. `2 / 6`).
- ESC key or ✕ button closes lightbox.
- Click outside panel closes lightbox.
- Non-screenshot evidence (log, link) shown in editable list below gallery.
- Empty state: "No evidence images attached." when no screenshots exist.

## Design Notes

- Computed field `evidence_gallery_html` (Html, sanitize=False) on `qa.bug.ticket`.
- Renders `<div class="qa-evidence-gallery"><div class="qa-evidence-grid">` with `<img src alt>` cards.
- Uses standard `src`/`alt` attributes (not `data-*`) to avoid Odoo HTML sanitizer stripping.
- `evidence_lightbox.js`: global singleton lightbox via document event delegation — works with Odoo dynamic views.
- OWL widget rejected: One2many widget too complex, editing conflicts with existing list.
- Assets registered in `web.assets_backend` bundle in `__manifest__.py`.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | — |
| Integration | Upload 3+ images → verify gallery renders 3-column grid |
| E2E | Click thumbnail → lightbox opens; ← → keys navigate; ESC closes |

## Harness Delta

Decision 0014 recorded.

## Evidence

Implemented 2026-05-28. Computed field + JS lightbox + CSS added. Assets registered in manifest.
