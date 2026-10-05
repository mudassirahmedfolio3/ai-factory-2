import { loadContractOpenApiDocument } from './openapi.contract';

describe('loadContractOpenApiDocument', () => {
  it('loads OpenAPI 3.1 contract with getHealth and bearerAuth', () => {
    const doc = loadContractOpenApiDocument() as {
      openapi: string;
      info: { title: string };
      paths: Record<string, { get?: { operationId?: string; security?: unknown[] } }>;
      components?: {
        securitySchemes?: { bearerAuth?: Record<string, unknown> };
        schemas?: { HealthResponse?: { required?: string[] } };
      };
    };

    expect(doc.openapi).toMatch(/^3\.1/);
    expect(doc.info.title).toBe('Lumen Lighting Retail API');

    const getHealth = doc.paths['/health']?.get;
    expect(getHealth?.operationId).toBe('getHealth');
    expect(getHealth?.security).toEqual([]);

    expect(doc.components?.securitySchemes?.bearerAuth).toEqual(
      expect.objectContaining({
        type: 'http',
        scheme: 'bearer',
        bearerFormat: 'JWT',
      }),
    );

    expect(doc.components?.schemas?.HealthResponse?.required).toEqual(
      expect.arrayContaining(['status', 'database', 'timestamp']),
    );
  });
});
