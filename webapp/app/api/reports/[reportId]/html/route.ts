import { NextRequest } from 'next/server';
import { verifyShareToken } from '@/lib/auth';
import { sql } from '@/lib/db';
import { adaptHtml } from '@/lib/templateAdapter';

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ reportId: string }> },
) {
  const { reportId } = await params;
  const token = req.nextUrl.searchParams.get('t');

  const valid = await verifyShareToken(reportId, token);
  if (!valid) {
    return new Response('Not found', { status: 404 });
  }

  const [reportRows, patchRows] = await Promise.all([
    sql`SELECT id, html, share_token FROM report WHERE id = ${reportId}`,
    sql`SELECT bug_id, note, resolution, status FROM bug_patch WHERE report_id = ${reportId}`,
  ]);

  if (reportRows.length === 0) {
    return new Response('Not found', { status: 404 });
  }

  const report = reportRows[0];
  const patches = patchRows as unknown as Array<{
    bug_id: string;
    note: string | null;
    resolution: string | null;
    status: string | null;
  }>;

  const adaptedHtml = adaptHtml({
    html: report.html as string,
    reportId,
    shareToken: report.share_token as string,
    backendUrl: process.env.BASE_URL!,
    patches,
  });

  return new Response(adaptedHtml, {
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'private, no-store',
    },
  });
}
