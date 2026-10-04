import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { M3_OPERATION_IDS } from './m3-operation-ids.js';

describe('docs/openapi.yaml M3 operation surface (WI-010 / WI-020)', () => {
  it('declares exactly 24 counted operations plus getHealth', () => {
    const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '../../..');
    const contract = readFileSync(
      join(repoRoot, 'docs/openapi.yaml'),
      'utf8',
    );

    for (const operationId of M3_OPERATION_IDS) {
      expect(contract).toContain(`operationId: ${operationId}`);
    }

    const matches = contract.match(/operationId: /g);
    expect(matches?.length).toBe(M3_OPERATION_IDS.length);
  });
});
