import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { M3_COUNTED_OPERATION_IDS as REGISTRY_IDS } from '../openapi/m3-api.operations';

const repoRoot = join(__dirname, '..', '..', '..', '..');

describe('Staging / CI infrastructure (WI-026)', () => {
  it('docker-compose files expose JWT secrets and optional DB seed flag', () => {
    for (const file of ['docker-compose.yml', 'docker-compose.staging.yml']) {
      const content = readFileSync(join(repoRoot, file), 'utf8');
      expect(content).toContain('JWT_ACCESS_SECRET');
      expect(content).toContain('JWT_REFRESH_SECRET');
      expect(content).toContain('RUN_DB_SEED');
    }
  });

  it('API Dockerfile uses entrypoint that migrates and seeds before boot', () => {
    const dockerfile = readFileSync(
      join(repoRoot, 'apps', 'api', 'Dockerfile'),
      'utf8',
    );
    expect(dockerfile).toContain('docker-entrypoint.sh');
    const entrypoint = readFileSync(
      join(repoRoot, 'apps', 'api', 'docker-entrypoint.sh'),
      'utf8',
    );
    expect(entrypoint).toContain('prisma migrate deploy');
    expect(entrypoint).toContain('dist/seed/database-seed.js');
  });

  it('staging smoke script targets M3 catalog parity and operation registry', () => {
    const smoke = readFileSync(
      join(repoRoot, 'scripts', 'staging-smoke.mjs'),
      'utf8',
    );
    expect(smoke).toContain('m3-smoke-constants.mjs');
    expect(smoke).toContain('M3_CATALOG_PARITY.minProductCount');

    const constants = readFileSync(
      join(repoRoot, 'scripts', 'm3-smoke-constants.mjs'),
      'utf8',
    );
    for (const operationId of REGISTRY_IDS) {
      expect(constants).toContain(`'${operationId}'`);
    }
    expect(REGISTRY_IDS).toHaveLength(28);
  });

  it('GitHub Actions CI runs backend Jest and Flutter in app/', () => {
    const ci = readFileSync(
      join(repoRoot, '.github', 'workflows', 'ci.yml'),
      'utf8',
    );
    expect(ci).toContain('working-directory: apps/api');
    expect(ci).toContain('working-directory: app');
    expect(ci).toContain('npm test');
    expect(ci).toContain('flutter analyze');
    expect(ci).toContain('compose-config');
    expect(ci).toContain('docker-compose.staging.yml');
  });

  it('deploy workflow probes getHealth after staging/production compose up', () => {
    const deploy = readFileSync(
      join(repoRoot, '.github', 'workflows', 'deploy.yml'),
      'utf8',
    );
    expect(deploy).toContain('/api/v1/health');
    expect(deploy).toContain('"status":"ok"');
    expect(deploy).toContain('JWT_ACCESS_SECRET');
  });
});
