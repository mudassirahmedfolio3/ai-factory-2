import { readFileSync } from 'fs';
import { join } from 'path';
import { loadContractOpenApiDocument } from './openapi.contract';
import {
  M3_API_OPERATIONS,
  M3_COUNTED_OPERATION_IDS,
  M3_COUNTED_OPERATIONS,
  M3_HEALTH_OPERATION,
} from './m3-api.operations';

describe('OpenAPI contract document (unit)', () => {
  const document = loadContractOpenApiDocument();
  const paths = document.paths as Record<
    string,
    Record<string, { operationId?: string }>
  >;

  it('declares all M3 API operationIds including getHealth', () => {
    for (const { method, path, operationId } of M3_API_OPERATIONS) {
      const pathItem = paths[path];
      expect(pathItem).toBeDefined();
      expect(pathItem[method]?.operationId).toBe(operationId);
    }
  });

  it('defines exactly twenty-eight counted operations plus getHealth infrastructure', () => {
    const operationIds = Object.values(paths).flatMap((item) =>
      Object.values(item)
        .map((operation) => operation.operationId)
        .filter((id): id is string => typeof id === 'string'),
    );
    expect(M3_COUNTED_OPERATION_IDS).toHaveLength(28);
    for (const operationId of M3_COUNTED_OPERATION_IDS) {
      expect(operationIds).toContain(operationId);
    }
    expect(operationIds).toContain(M3_HEALTH_OPERATION.operationId);
    expect(operationIds).toHaveLength(M3_COUNTED_OPERATION_IDS.length + 1);
  });

  it('matches counted operation registry paths and methods', () => {
    for (const { method, path, operationId } of M3_COUNTED_OPERATIONS) {
      expect(paths[path][method]?.operationId).toBe(operationId);
    }
  });

  it('models Money as integer pence with GBP example', () => {
    const schemas = document.components as {
      schemas: {
        Money: {
          properties: {
            amountCents: { type: string };
            currency: { example: string };
          };
        };
      };
    };
    expect(schemas.schemas.Money.properties.amountCents.type).toBe('integer');
    expect(schemas.schemas.Money.properties.currency.example).toBe('GBP');
  });

  it('matches the repo docs/openapi.yaml contract (byte parity)', () => {
    const apiYaml = readFileSync(join(process.cwd(), 'openapi.yaml'), 'utf8');
    const docsYaml = readFileSync(
      join(process.cwd(), '..', '..', 'docs', 'openapi.yaml'),
      'utf8',
    );
    expect(apiYaml).toBe(docsYaml);
  });
});
