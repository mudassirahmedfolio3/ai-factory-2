/**
 * Resolves DATABASE_URL for e2e from environment variables only (no committed credentials).
 * CI exports DATABASE_URL or sets POSTGRES_*; local runs may use .env or docker-compose env.
 */
export function resolveE2eDatabaseUrl(): string {
  const explicit = process.env.DATABASE_URL?.trim();
  if (explicit) {
    return explicit;
  }

  const user = process.env.POSTGRES_USER ?? process.env.E2E_PG_USER;
  const password =
    process.env.POSTGRES_PASSWORD ?? process.env.E2E_PG_PASSWORD;
  const host = process.env.E2E_PG_HOST ?? 'localhost';
  const port = process.env.E2E_PG_PORT ?? '5432';
  const database =
    process.env.POSTGRES_DB ?? process.env.E2E_PG_DATABASE ?? 'retail';

  if (user && password) {
    return `postgresql://${encodeURIComponent(user)}:${encodeURIComponent(password)}@${host}:${port}/${database}?schema=public`;
  }

  return `postgresql://${host}:${port}/${database}?schema=public`;
}
