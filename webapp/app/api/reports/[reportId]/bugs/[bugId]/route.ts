import { NextRequest, NextResponse } from 'next/server';
import { rateLimit } from '@/lib/rateLimit';
import type { PatchPayload } from '@/types';

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ reportId: string; bugId: string }> },
) {
  const { bugId } = await params;
  const token = req.nextUrl.searchParams.get('t');

  const limited = rateLimit(token ?? 'anon', 60, 60_000);
  if (limited) {
    return NextResponse.json({ error: 'Too many requests' }, { status: 429 });
  }

  if (!token) return NextResponse.json({ error: 'Not found' }, { status: 404 });

  const body = (await req.json()) as PatchPayload;

  const odooUrl = process.env.ODOO_URL?.trim().replace(/\/+$/, '');
  if (!odooUrl) {
    return NextResponse.json({ error: 'Server misconfigured' }, { status: 500 });
  }

  let res: Response;
  try {
    res = await fetch(
      `${odooUrl}/qa/api/report/bug/${token}/${bugId}`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          note: body.note ?? null,
          resolution: body.resolution ?? null,
          status: body.resolution === 'Fixed' ? 'closed' : null,
        }),
      },
    );
  } catch {
    return NextResponse.json({ error: 'Odoo relay unavailable' }, { status: 502 });
  }

  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    return NextResponse.json(
      { error: 'Odoo relay rejected request', status: res.status, detail },
      { status: res.status >= 500 ? 502 : res.status },
    );
  }

  const text = await res.text();
  try {
    return NextResponse.json(JSON.parse(text));
  } catch {
    return NextResponse.json(
      { error: 'Odoo relay returned invalid JSON', detail: text },
      { status: 502 },
    );
  }
}
