import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

/**
 * Backend convention: "DTOs use class-validator; responses match the
 * OpenAPI schemas exactly. The OpenAPI document is the contract; the code
 * follows it."
 *
 * server/openapi.yaml is shipped alongside the server (e.g. as the input to
 * the Dart client generator / for anyone browsing the repo without the
 * `docs/` folder). Nothing enforced that this copy stays in sync with
 * docs/openapi.yaml, the actual contract. If the two ever diverge, a
 * generated client or a reviewer could silently work from a stale copy.
 * This pins them to be byte-identical so a future edit to one without the
 * other fails CI instead of drifting unnoticed.
 */
describe('server/openapi.yaml stays byte-identical to docs/openapi.yaml (the contract)', () => {
  it('matches docs/openapi.yaml exactly', () => {
    const serverRoot = join(dirname(fileURLToPath(import.meta.url)), '../..');
    const repoRoot = join(serverRoot, '..');

    const serverCopy = readFileSync(join(serverRoot, 'openapi.yaml'), 'utf8');
    const docsContract = readFileSync(
      join(repoRoot, 'docs/openapi.yaml'),
      'utf8',
    );

    expect(serverCopy).toBe(docsContract);
  });
});
