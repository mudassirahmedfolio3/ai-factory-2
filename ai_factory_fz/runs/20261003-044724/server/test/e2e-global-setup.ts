import { PrismaClient } from '@prisma/client';
import { resolveE2eDatabaseUrl } from './e2e-database-url.js';

/**
 * Probes Postgres once per vitest e2e run so DB-backed cases can skip locally
 * while CI (with the postgres service) executes the full M3 HTTP matrix.
 */
export default async function e2eGlobalSetup(): Promise<void> {
  process.env.JWT_SECRET ??=
    'e2e-test-jwt-secret-minimum-length-do-not-use-in-production';
  process.env.DATABASE_URL ??= resolveE2eDatabaseUrl();

  let available = false;
  const client = new PrismaClient();
  try {
    await client.$connect();
    await client.$queryRawUnsafe('SELECT 1');
    available = true;
  } catch {
    available = false;
  } finally {
    await client.$disconnect();
  }
  process.env.E2E_DATABASE_AVAILABLE = available ? '1' : '0';
}
