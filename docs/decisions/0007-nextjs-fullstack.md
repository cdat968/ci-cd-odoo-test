# 0007 Next.js 15 Fullstack (App Router) — Frontend + Backend

Date: 2026-05-26

## Status

Accepted — supersedes 0006 (Hono.js + vanilla JS client)

## Decision

Use **Next.js 15 (App Router, TypeScript)** as the single framework for
both frontend and backend. Deploy on **Vercel** (free tier). Database:
**Supabase PostgreSQL** (existing decision, unchanged). Image storage:
**Cloudinary** (unchanged).

- No separate Hono.js backend service.
- No standalone vanilla-JS / standalone TypeScript client.
- One Next.js app handles RSC pages, Route Handlers (API), and static assets.
- Apply `next-best-practices` skill throughout.

## Consequences

- Simpler infra: one Vercel project, one deploy.
- Route Handlers replace FastAPI/Hono endpoints 1-to-1.
- Report viewer page is a React Server Component that fetches HTML + patches,
  passes to a `'use client'` ReportViewer for interactive rendering.
- `dangerouslySetInnerHTML` used for the stored report HTML to preserve all
  existing interactive features without a full React rewrite.
