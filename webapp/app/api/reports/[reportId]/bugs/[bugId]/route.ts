import { NextRequest, NextResponse } from 'next/server';
import { verifyShareToken } from '@/lib/auth';
import { sql } from '@/lib/db';
import { rateLimit } from '@/lib/rateLimit';
import type { PatchPayload } from '@/types';

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ reportId: string; bugId: string }> },
) {
  const { reportId, bugId } = await params;
  const token = req.nextUrl.searchParams.get('t');

  // Rate limit: 60 req/min per share token (fall back to 'anon' key)
  const limited = rateLimit(token ?? 'anon', 60, 60_000);
  if (limited) {
    return NextResponse.json({ error: 'Too many requests' }, { status: 429 });
  }

  const valid = await verifyShareToken(reportId, token);
  if (!valid) return NextResponse.json({ error: 'Not found' }, { status: 404 });

  const body = (await req.json()) as PatchPayload;
  const { note, resolution, updated_by } = body;

  const status = resolution === 'Fixed' ? 'Closed' : null;

  const rows = await sql`
    INSERT INTO bug_patch (report_id, bug_id, note, resolution, status, updated_by)
    VALUES (${reportId}, ${bugId}, ${note ?? null}, ${resolution ?? null}, ${status}, ${updated_by ?? null})
    ON CONFLICT (report_id, bug_id) DO UPDATE
    SET note       = COALESCE(EXCLUDED.note, bug_patch.note),
        resolution = COALESCE(EXCLUDED.resolution, bug_patch.resolution),
        status     = COALESCE(EXCLUDED.status, bug_patch.status),
        updated_by = EXCLUDED.updated_by,
        updated_at = now()
    RETURNING bug_id, note, resolution, status, updated_at
  `;

  // Append audit log entry (best-effort — do not block response)
  await sql`
    INSERT INTO audit_log (report_id, bug_id, field, new_value, actor)
    VALUES (${reportId}, ${bugId}, 'resolution', ${resolution ?? null}, ${updated_by ?? 'anon'})
  `;

  return NextResponse.json(rows[0]);
}
