import { INestApplication } from '@nestjs/common';
import { OpenAPIObject, SwaggerModule } from '@nestjs/swagger';
import { loadContractOpenApiDocument } from './openapi.contract';

export { loadContractOpenApiDocument } from './openapi.contract';

/**
 * Publishes the contract-first OpenAPI document at GET /api/docs-json via @nestjs/swagger.
 * Infrastructure route; excluded from the twelve-operation delivery cap.
 */
export function setupOpenApi(app: INestApplication): OpenAPIObject {
  const document = loadContractOpenApiDocument() as unknown as OpenAPIObject;

  SwaggerModule.setup('api/docs', app, document, {
    jsonDocumentUrl: 'api/docs-json',
    ui: false,
    raw: ['json'],
  });

  return document;
}
