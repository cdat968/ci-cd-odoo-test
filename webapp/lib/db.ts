import postgres from 'postgres';

const globalForDb = globalThis as unknown as { sql: ReturnType<typeof postgres> };

export const sql =
  globalForDb.sql ??
  postgres(process.env.DATABASE_URL!, {
    max: 10,
    idle_timeout: 30,
  });

if (process.env.NODE_ENV !== 'production') globalForDb.sql = sql;
