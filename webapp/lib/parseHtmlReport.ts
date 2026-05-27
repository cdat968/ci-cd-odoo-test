import type { BugRecord, ReportMeta } from '@/types';

function extractJsBlock(html: string, varName: string): string | null {
  const marker = `const ${varName} = {`;
  const start = html.indexOf(marker);
  if (start === -1) return null;

  let depth = 0;
  let inString = false;
  let i = start + marker.length - 1; // opening {

  for (; i < html.length; i++) {
    const ch = html[i];
    if (inString) {
      if (ch === '\\') { i++; continue; }
      if (ch === '"') inString = false;
    } else {
      if (ch === '"') inString = true;
      else if (ch === '{') depth++;
      else if (ch === '}') {
        depth--;
        if (depth === 0) return html.slice(start + marker.length - 1, i + 1);
      }
    }
  }
  return null;
}

function jsToJson(js: string): string {
  const placeholders: Record<string, string> = {};
  let counter = 0;

  // Protect string literals so their contents are invisible to key-quoting regex.
  let protected_ = js.replace(/"(?:[^"\\]|\\.)*"/g, (m) => {
    const key = `"__S${counter++}__"`;
    placeholders[key] = m;
    return key;
  });

  // Quote unquoted identifier keys.
  protected_ = protected_.replace(/\b([a-zA-Z_][a-zA-Z0-9_]*)\s*:/g, '"$1":');

  // Remove trailing commas before } or ].
  protected_ = protected_.replace(/,(\s*[}\]])/g, '$1');

  // Restore strings.
  for (const [placeholder, original] of Object.entries(placeholders)) {
    protected_ = protected_.split(placeholder).join(original);
  }

  return protected_;
}

export function parseHtmlReport(html: string): { bugs: BugRecord[]; metadata: ReportMeta } {
  const empty = (): { bugs: BugRecord[]; metadata: ReportMeta } => ({
    bugs: [],
    metadata: { project_name: '', report_date: '', total_bugs: 0, open_bugs: 0, high_priority_count: 0 },
  });

  const jsBlock = extractJsBlock(html, 'bugTickets');
  if (!jsBlock) return empty();

  let data: Record<string, BugRecord>;
  try {
    data = JSON.parse(jsToJson(jsBlock));
  } catch {
    return empty();
  }

  const bugs = Object.values(data);

  const h1Match = html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i);
  const projectName = h1Match ? h1Match[1].replace(/<[^>]+>/g, '').trim() : '';

  const todayMatch = html.match(/const reportToday\s*=\s*"([^"]+)"/);
  const reportDate = todayMatch ? todayMatch[1] : '';

  return {
    bugs,
    metadata: {
      project_name: projectName,
      report_date: reportDate,
      total_bugs: bugs.length,
      open_bugs: bugs.filter(b => b.status !== 'Fixed').length,
      high_priority_count: bugs.filter(b => b.priority?.includes('P2')).length,
    },
  };
}
