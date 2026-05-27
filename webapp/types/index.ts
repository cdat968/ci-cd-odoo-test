export interface ReportRow {
  id: string;
  share_token: string;
  title: string;
  html: string;
  payload: ReportPayload;
  created_at: Date;
  created_by: string | null;
}

export interface ReportPayload {
  bugs: BugRecord[];
  test_cases: TestCase[];
  evidence_map: Record<string, EvidenceAsset>;
}

export interface BugRecord {
  id: string;
  summary: string;
  description: string;
  steps: string[];
  expected: string;
  observed: string;
  build: string;
  reproducibility: string;
  severity: string;
  frequency: string;
  priority: string;
  keyword: string;
  status: string;
  resolution: string;
  note: string;
  suggestedFix: string;
  feature: string;
  createdAt: string;
  evidence: { src: string; title: string }[];
}

export interface ReportMeta {
  project_name: string;
  report_date: string;
  total_bugs: number;
  open_bugs: number;
  high_priority_count: number;
}

export interface TestCase {
  id: string;
  [key: string]: unknown;
}

export interface EvidenceAsset {
  secure_url: string;
  public_id: string;
}

export interface BugPatchRow {
  id: string;
  report_id: string;
  bug_id: string;
  note: string | null;
  resolution: Resolution | null;
  status: string | null;
  updated_by: string | null;
  updated_at: Date;
}

export type Resolution = 'Open' | 'In Progress' | 'Fixed' | "Won't Fix" | 'Duplicate';

export interface PatchPayload {
  note?: string;
  resolution?: Resolution;
  updated_by?: string;
}
