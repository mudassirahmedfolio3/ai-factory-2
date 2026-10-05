import { INestApplication, ValidationPipe } from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import request from 'supertest';
import { AppModule } from '../app.module';
import { PrismaService } from '../prisma/prisma.service';

describe('HealthController (e2e)', () => {
  let app: INestApplication;
  let pingDatabase: jest.Mock;

  beforeAll(async () => {
    pingDatabase = jest.fn().mockResolvedValue(undefined);

    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(PrismaService)
      .useValue({
        onModuleInit: jest.fn().mockResolvedValue(undefined),
        onModuleDestroy: jest.fn().mockResolvedValue(undefined),
        pingDatabase,
      })
      .compile();

    app = moduleFixture.createNestApplication();
    app.setGlobalPrefix('api/v1');
    app.useGlobalPipes(
      new ValidationPipe({
        whitelist: true,
        forbidNonWhitelisted: true,
        transform: true,
      }),
    );
    await app.init();
  });

  afterAll(async () => {
    await app?.close();
  });

  it('getHealth — GET /api/v1/health returns 200 with HealthResponse when DB is up', async () => {
    pingDatabase.mockResolvedValue(undefined);

    const response = await request(app.getHttpServer())
      .get('/api/v1/health')
      .expect(200);

    expect(response.body).toMatchObject({
      status: 'ok',
      database: 'up',
    });
    expect(response.body.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T/);
  });

  it('getHealth — GET /api/v1/health returns 503 when DB is down', async () => {
    pingDatabase.mockRejectedValue(new Error('connection refused'));

    const response = await request(app.getHttpServer())
      .get('/api/v1/health')
      .expect(503);

    expect(response.body).toMatchObject({
      statusCode: 503,
      error: 'Service Unavailable',
      message: 'Database unreachable',
    });
  });
});
