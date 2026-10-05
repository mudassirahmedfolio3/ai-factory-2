import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { M3_OPERATION_IDS } from './m3-operation-ids.js';

function repoRootFromHere(): string {
  const serverRoot = join(dirname(fileURLToPath(import.meta.url)), '../..');
  return join(serverRoot, '..');
}

function collectControllerOperationIds(serverRoot: string): string[] {
  const srcRoot = join(serverRoot, 'src');
  const modules = readdirSync(srcRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name);

  const operationIds: string[] = [];
  for (const moduleName of modules) {
    const moduleDir = join(srcRoot, moduleName);
    for (const file of readdirSync(moduleDir)) {
      if (!file.endsWith('.controller.ts')) {
        continue;
      }
      const source = readFileSync(join(moduleDir, file), 'utf8');
      const matches = source.matchAll(/operationId:\s*['"]([\w]+)['"]/g);
      for (const match of matches) {
        operationIds.push(match[1]);
      }
    }
  }
  return operationIds.sort();
}

describe('Nest controllers declare every M3 OpenAPI operationId (WI-020)', () => {
  const serverRoot = join(dirname(fileURLToPath(import.meta.url)), '../..');
  const contract = readFileSync(
    join(repoRootFromHere(), 'docs/openapi.yaml'),
    'utf8',
  );

  it('docs/openapi.yaml declares exactly 25 operationIds', () => {
    for (const operationId of M3_OPERATION_IDS) {
      expect(contract).toContain(`operationId: ${operationId}`);
    }
    const matches = contract.match(/operationId: /g);
    expect(matches?.length).toBe(M3_OPERATION_IDS.length);
  });

  it('controller @ApiOperation operationIds match the contract set', () => {
    const implemented = collectControllerOperationIds(serverRoot);
    expect(implemented.sort()).toEqual([...M3_OPERATION_IDS].sort());
  });
});
