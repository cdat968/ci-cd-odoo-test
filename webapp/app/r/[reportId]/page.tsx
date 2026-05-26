import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import { verifyShareToken } from '@/lib/auth';
import { sql } from '@/lib/db';
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

export default async function ReportPage({ params, searchParams }: Props) {
  const { reportId } = await params;
  const { t: token } = await searchParams;

  const valid = await verifyShareToken(reportId, token ?? null);
  if (!valid) notFound();

  const rows = await sql`SELECT title FROM report WHERE id = ${reportId}`;
  if (rows.length === 0) notFound();

  const title = rows[0].title as string;
  const htmlUrl = `/api/reports/${reportId}/html?t=${encodeURIComponent(token ?? '')}`;

  return <ReportViewer url={htmlUrl} title={title} />;
}
