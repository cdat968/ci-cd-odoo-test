import { NextRequest, NextResponse } from 'next/server';
import { verifyShareToken } from '@/lib/auth';
import { sql } from '@/lib/db';

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ reportId: string }> },
) {
  const { reportId } = await params;
  const token = req.nextUrl.searchParams.get('t');

  const valid = await verifyShareToken(reportId, token);
  if (!valid) return NextResponse.json({ error: 'Not found' }, { status: 404 });

  const patches = await sql`
    SELECT bug_id, note, resolution, status, updated_at
    FROM bug_patch
    WHERE report_id = ${reportId}
  `;

  return NextResponse.json({ patches });
}
