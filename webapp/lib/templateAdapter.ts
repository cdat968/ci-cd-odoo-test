export interface AdapterParams {
  html: string;
  reportId: string;
  shareToken: string;
  backendUrl: string;
  patches: Array<{
    bug_id: string;
    note: string | null;
    resolution: string | null;
    status: string | null;
  }>;
}

function scriptJson(value: unknown): string {
  return JSON.stringify(value).replace(/</g, '\\u003c');
}

function injectBeforeClosingBody(html: string, injection: string): string {
  const closingBody = /<\/body\s*>/gi;
  let lastMatch: RegExpExecArray | null = null;
  let match: RegExpExecArray | null;

  while ((match = closingBody.exec(html)) !== null) {
    lastMatch = match;
  }

  if (!lastMatch) {
    return `${html}${injection}`;
  }

  const index = lastMatch.index;
  return `${html.slice(0, index)}${injection}\n${html.slice(index)}`;
}

export function adaptHtml({
  html,
  reportId,
  shareToken,
  backendUrl,
  patches,
}: AdapterParams): string {
  const meta = { report_id: reportId, share_token: shareToken, backend_url: backendUrl };
  const injection = `
<script>window.__REPORT_META__ = ${scriptJson(meta)};</script>
<script>window.__REPORT_PATCHES__ = ${scriptJson(patches)};</script>
<script src="/static/client.js"></script>`;

  // Add data-bug-id to bug <tr> rows that have a matching data-id attribute
  const result = html.replace(
    /<tr[^>]*class="[^"]*ticket-row[^"]*"[^>]*data-id="([^"]+)"/g,
    (match, bugId) =>
      match.includes('data-bug-id') ? match : match.replace('>', ` data-bug-id="${bugId}">`),
  );

  return injectBeforeClosingBody(result, injection);
}
