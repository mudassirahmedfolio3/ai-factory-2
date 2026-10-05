import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const serverRoot = join(dirname(fileURLToPath(import.meta.url)), '../..');
const repoRoot = join(serverRoot, '..');

describe('WI-005 infra artifacts (BUG-002)', () => {
  it('ships Dockerfile, dockerignore, and root compose with Postgres 16', () => {
    expect(existsSync(join(serverRoot, 'Dockerfile'))).toBe(true);
    expect(existsSync(join(serverRoot, '.dockerignore'))).toBe(true);
    expect(existsSync(join(repoRoot, 'docker-compose.yml'))).toBe(true);
  });

  it('ships Prisma migrations and seed pipeline', () => {
    expect(
      existsSync(
        join(serverRoot, 'prisma/migrations/20261003120000_init/migration.sql'),
      ),
    ).toBe(true);
    expect(existsSync(join(serverRoot, 'prisma/seed.ts'))).toBe(true);
  });

  it('ships CI workflow covering server build/test with Postgres', () => {
    expect(
      existsSync(join(repoRoot, '.github/workflows/server-ci.yml')),
    ).toBe(true);
  });

  it('ships Nest health/catalog/prisma bootstrap modules', () => {
    expect(existsSync(join(serverRoot, 'src/app.setup.ts'))).toBe(true);
    expect(existsSync(join(serverRoot, 'src/health/health.module.ts'))).toBe(
      true,
    );
    expect(existsSync(join(serverRoot, 'src/catalog/catalog.module.ts'))).toBe(
      true,
    );
    expect(existsSync(join(serverRoot, 'src/prisma/prisma.module.ts'))).toBe(
      true,
    );
  });
});
