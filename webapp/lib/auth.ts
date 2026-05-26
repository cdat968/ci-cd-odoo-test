import { sql } from './db';

export async function verifyShareToken(
  reportId: string,
  token: string | null,
): Promise<boolean> {
  if (!token) return false;
  const rows = await sql`
    SELECT 1 FROM report WHERE id = ${reportId} AND share_token = ${token}
  `;
  return rows.length > 0;
}
