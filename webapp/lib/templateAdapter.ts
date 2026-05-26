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

export function adaptHtml({
  html,
  reportId,
  shareToken,
  backendUrl,
  patches,
}: AdapterParams): string {
  const meta = { report_id: reportId, share_token: shareToken, backend_url: backendUrl };
  const injection = `
<script>window.__REPORT_META__ = ${JSON.stringify(meta)};</script>
<script>window.__REPORT_PATCHES__ = ${JSON.stringify(patches)};</script>
<script src="/static/client.js"></script>`;

  // Add data-bug-id to bug <tr> rows that have a matching data-id attribute
  const result = html.replace(
    /<tr[^>]*class="[^"]*ticket-row[^"]*"[^>]*data-id="([^"]+)"/g,
    (match, bugId) =>
      match.includes('data-bug-id') ? match : match.replace('>', ` data-bug-id="${bugId}">`),
  );

  return result.replace('</body>', `${injection}\n</body>`);
}
