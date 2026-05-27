import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import ReportViewer from '@/components/ReportViewer';
import type { BugRecord, ReportMeta } from '@/types';

type Props = {
  params: Promise<{ reportId: string }>;
  searchParams: Promise<{ t?: string }>;
};

type OdooReportResponse = {
  id: number;
  title: string;
  project_name: string;
  report_date: string;
  total_bugs: number;
  open_bugs: number;
  high_priority_count: number;
  bugs: BugRecord[];
  error?: string;
};

async function fetchReport(shareToken: string): Promise<OdooReportResponse | null> {
  const odooUrl = process.env.ODOO_URL?.replace(/\/$/, '');
  if (!odooUrl) return null;

  try {
    const res = await fetch(`${odooUrl}/qa/api/report/${shareToken}`, {
      cache: 'no-store',
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function generateMetadata({ params, searchParams }: Props): Promise<Metadata> {
  const { t: token } = await searchParams;
  if (!token) return { title: 'Report Not Found' };

  const data = await fetchReport(token);
  if (!data || data.error) return { title: 'Report Not Found' };

  return { title: data.title };
}

export default async function ReportPage({ params, searchParams }: Props) {
  const { reportId } = await params;
  const { t: token } = await searchParams;

  if (!token) notFound();

  const data = await fetchReport(token);
  if (!data || data.error) notFound();

  const bugs: BugRecord[] = data.bugs ?? [];

  const metadata: ReportMeta = {
    project_name: data.project_name || data.title,
    report_date: data.report_date || '',
    total_bugs: data.total_bugs ?? bugs.length,
    open_bugs: data.open_bugs ?? 0,
    high_priority_count: data.high_priority_count ?? 0,
  };

  return (
    <ReportViewer
      bugs={bugs}
      metadata={metadata}
      reportId={reportId}
      shareToken={token}
    />
  );
}
