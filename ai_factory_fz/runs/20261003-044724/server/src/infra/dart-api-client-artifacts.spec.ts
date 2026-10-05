import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { M3_OPERATION_IDS } from './m3-operation-ids.js';

/**
 * WI-015 / WI-020: committed dart-dio client artifacts stay aligned with
 * app/openapi.yaml (M3 contract operationIds and generated API classes).
 */
const GENERATED_M3_API_FILES = [
  'app/packages/api_client/lib/src/api/health_api.dart',
  'app/packages/api_client/lib/src/api/auth_api.dart',
  'app/packages/api_client/lib/src/api/users_api.dart',
  'app/packages/api_client/lib/src/api/catalog_api.dart',
  'app/packages/api_client/lib/src/api/home_api.dart',
  'app/packages/api_client/lib/src/api/cart_api.dart',
  'app/packages/api_client/lib/src/api/wishlist_api.dart',
  'app/packages/api_client/lib/src/api/checkout_api.dart',
  'app/packages/api_client/lib/src/api/orders_api.dart',
  'app/packages/api_client/lib/src/api/support_api.dart',
] as const;

function repoRootFromHere(): string {
  const serverRoot = join(dirname(fileURLToPath(import.meta.url)), '../..');
  return join(serverRoot, '..');
}

describe('Dart OpenAPI client artifacts (M3 / WI-020)', () => {
  const repoRoot = repoRootFromHere();

  it('keeps generator scripts and config beside the contract copies', () => {
    for (const relativePath of [
      'scripts/generate-dart-api-client.sh',
      'scripts/generate-dart-api-client.ps1',
      'app/openapi-generator-config.yaml',
      'app/openapi.yaml',
      'docs/openapi.yaml',
      'server/openapi.yaml',
    ]) {
      expect(existsSync(join(repoRoot, relativePath))).toBe(true);
    }
  });

  it('keeps server/openapi.yaml byte-identical to docs/openapi.yaml', () => {
    const docsCopy = readFileSync(join(repoRoot, 'docs/openapi.yaml'), 'utf8');
    const serverCopy = readFileSync(
      join(repoRoot, 'server/openapi.yaml'),
      'utf8',
    );
    expect(serverCopy).toBe(docsCopy);
  });

  it('ships generated dart-dio API classes for the M3 surface', () => {
    for (const relativePath of GENERATED_M3_API_FILES) {
      expect(existsSync(join(repoRoot, relativePath))).toBe(true);
    }

    const contract = readFileSync(join(repoRoot, 'app/openapi.yaml'), 'utf8');
    for (const operationId of M3_OPERATION_IDS) {
      expect(contract).toContain(`operationId: ${operationId}`);
    }
    const matches = contract.match(/operationId: /g);
    expect(matches?.length).toBe(M3_OPERATION_IDS.length);
  });
});
