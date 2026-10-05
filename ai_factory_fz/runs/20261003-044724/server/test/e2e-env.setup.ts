/**
 * E2E defaults so Nest ConfigModule validation passes without a committed .env.
 * CI sets DATABASE_URL explicitly; local runs may skip DB-dependent cases when Postgres is down.
 */
import { resolveE2eDatabaseUrl } from './e2e-database-url.js';

process.env.JWT_SECRET ??=
  'e2e-test-jwt-secret-minimum-length-do-not-use-in-production';
process.env.DATABASE_URL ??= resolveE2eDatabaseUrl();
