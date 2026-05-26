import { NextRequest, NextResponse } from 'next/server';
import { sql } from '@/lib/db';
import crypto from 'node:crypto';

export async function POST(req: NextRequest) {
  const key = req.headers.get('x-pipeline-key');
  if (key !== process.env.PIPELINE_KEY) {
    return NextResponse.json({ error: 'Not found' }, { status: 404 });
  }

  const body = (await req.json()) as {
    title: string;
    html: string;
    payload: unknown;
    created_by?: string;
  };
  const { title, html, payload, created_by } = body;

  const id = crypto.randomUUID();
  const shareToken = crypto.randomBytes(24).toString('base64url');

  await sql`
    INSERT INTO report (id, share_token, title, html, payload, created_by)
    VALUES (${id}, ${shareToken}, ${title}, ${html}, ${JSON.stringify(payload)}, ${created_by ?? null})
  `;

  const shareUrl = `${process.env.BASE_URL}/r/${id}?t=${shareToken}`;
  return NextResponse.json({ id, share_url: shareUrl }, { status: 201 });
}
