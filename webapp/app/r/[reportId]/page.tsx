import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import { verifyShareToken } from '@/lib/auth';
import { sql } from '@/lib/db';
import ReportViewer from '@/components/ReportViewer';
import { parseHtmlReport } from '@/lib/parseHtmlReport';
import type { BugRecord, ReportMeta } from '@/types';

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

export default async function ReportPage({ params, searchParams }: Props) {
  const { reportId } = await params;
  const { t: token } = await searchParams;

  const valid = await verifyShareToken(reportId, token ?? null);
  if (!valid) notFound();

  const [reportRows, patchRows] = await Promise.all([
    sql`SELECT title, payload, html FROM report WHERE id = ${reportId}`,
    sql`SELECT bug_id, note, resolution, status FROM bug_patch WHERE report_id = ${reportId}`,
  ]);

  if (reportRows.length === 0) notFound();

  const row = reportRows[0];
  const title = row.title as string;
  const rawPayload = row.payload as { bugs?: BugRecord[]; metadata?: ReportMeta } | null;

  let bugs: BugRecord[] = rawPayload?.bugs ?? [];
  let metadata: ReportMeta = rawPayload?.metadata ?? {
    project_name: title,
    report_date: '',
    total_bugs: 0,
    open_bugs: 0,
    high_priority_count: 0,
  };

  // Legacy reports uploaded before Phase 1: payload is empty, parse HTML on-the-fly.
  if (bugs.length === 0 && row.html) {
    const parsed = parseHtmlReport(row.html as string);
    bugs = parsed.bugs;
    metadata = parsed.metadata.project_name ? parsed.metadata : { ...parsed.metadata, project_name: title };
  }

  // Merge bug_patch overrides (note, resolution, status) into bug data.
  const patches = patchRows as unknown as { bug_id: string; note: string | null; resolution: string | null; status: string | null }[];
  const patchMap = new Map(patches.map(p => [p.bug_id, p]));
  const mergedBugs = bugs.map(bug => {
    const patch = patchMap.get(bug.id);
    if (!patch) return bug;
    return {
      ...bug,
      ...(patch.note !== null && { note: patch.note }),
      ...(patch.resolution !== null && { resolution: patch.resolution }),
      ...(patch.status !== null && { status: patch.status }),
    };
  });

  return (
    <ReportViewer
      bugs={mergedBugs}
      metadata={metadata}
      reportId={reportId}
      shareToken={token ?? ''}
    />
  );
}
