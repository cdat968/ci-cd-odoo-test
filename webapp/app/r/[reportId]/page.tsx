import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import { verifyShareToken } from '@/lib/auth';
import { sql } from '@/lib/db';
import { adaptHtml } from '@/lib/templateAdapter';
import ReportViewer from '@/components/ReportViewer';

type Props = {
  params: Promise<{ reportId: string }>;
  searchParams: Promise<{ t?: string }>;
};

export async function generateMetadata({ params, searchParams }: Props): Promise<Metadata> {
  const { reportId } = await params;
  const { t: token } = await searchParams;

  const valid = await verifyShareToken(reportId, token ?? null);
  if (!valid) return { title: 'Report Not Found' };

  const rows = await sql`SELECT title FROM report WHERE id = ${reportId}`;
  if (rows.length === 0) return { title: 'Report Not Found' };

  return { title: rows[0].title as string };
}

// Next.js 15: params and searchParams are Promises
export default async function ReportPage({ params, searchParams }: Props) {
  const { reportId } = await params;
  const { t: token } = await searchParams;

  const valid = await verifyShareToken(reportId, token ?? null);
  if (!valid) notFound();

  // Parallel fetch to avoid waterfall
  const [reportRows, patchRows] = await Promise.all([
    sql`SELECT id, title, html, share_token FROM report WHERE id = ${reportId}`,
    sql`SELECT bug_id, note, resolution, status FROM bug_patch WHERE report_id = ${reportId}`,
  ]);

  if (reportRows.length === 0) notFound();

  const report = reportRows[0];

  const patches = (patchRows as unknown as Array<{
    bug_id: string;
    note: string | null;
    resolution: string | null;
    status: string | null;
  }>);

  const adaptedHtml = adaptHtml({
    html: report.html as string,
    reportId,
    shareToken: report.share_token as string,
    backendUrl: process.env.BASE_URL!,
    patches,
  });

  return <ReportViewer html={adaptedHtml} title={report.title as string} />;
}
