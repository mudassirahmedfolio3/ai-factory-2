import { INestApplication } from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import request from 'supertest';
import { AppModule } from '../app.module';
import { setupOpenApi } from './openapi.setup';
import { loadContractOpenApiDocument } from './openapi.contract';
import { M3_API_OPERATIONS } from './m3-api.operations';
import { PrismaService } from '../prisma/prisma.service';

describe('OpenAPI contract publication (e2e)', () => {
  let app: INestApplication;
  const committed = loadContractOpenApiDocument();

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(PrismaService)
      .useValue({
        onModuleInit: jest.fn().mockResolvedValue(undefined),
        onModuleDestroy: jest.fn().mockResolvedValue(undefined),
        pingDatabase: jest.fn().mockResolvedValue(undefined),
      })
      .compile();

    app = moduleFixture.createNestApplication();
    app.setGlobalPrefix('api/v1');
    setupOpenApi(app);
    await app.init();
  });

  afterAll(async () => {
    await app?.close();
  });

  it('GET /api/docs-json mirrors committed openapi.yaml paths and operationIds', async () => {
    const response = await request(app.getHttpServer())
      .get('/api/docs-json')
      .expect(200);

    const publishedPaths = response.body.paths as Record<
      string,
      Record<string, { operationId?: string }>
    >;
    const committedPaths = committed.paths as Record<
      string,
      Record<string, { operationId?: string }>
    >;

    expect(Object.keys(publishedPaths).sort()).toEqual(
      Object.keys(committedPaths).sort(),
    );

    for (const { path, method, operationId } of M3_API_OPERATIONS) {
      expect(publishedPaths[path][method].operationId).toBe(operationId);
      expect(committedPaths[path][method].operationId).toBe(operationId);
    }
  });

  it('documents bearerAuth for future protected operations', async () => {
    const response = await request(app.getHttpServer())
      .get('/api/docs-json')
      .expect(200);

    expect(response.body.components.securitySchemes.bearerAuth.type).toBe(
      'http',
    );
  });
});
