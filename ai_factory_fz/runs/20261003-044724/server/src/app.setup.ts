import {
  BadRequestException,
  type INestApplication,
  ValidationPipe,
} from '@nestjs/common';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { ErrorResponseFilter } from './common/error-response.filter.js';
import { HealthService } from './health/health.service.js';
import { PrismaService } from './prisma/prisma.service.js';

export async function setupApplication(app: INestApplication): Promise<void> {
  app.setGlobalPrefix('api/v1');

  app.useGlobalFilters(new ErrorResponseFilter());

  app.useGlobalPipes(
    new ValidationPipe({
      transform: true,
      whitelist: true,
      forbidNonWhitelisted: true,
      exceptionFactory: (errors) => {
        const firstConstraint = errors[0]?.constraints;
        const firstMessage =
          firstConstraint === undefined
            ? 'Validation failed'
            : Object.values(firstConstraint)[0];
        return new BadRequestException(firstMessage);
      },
    }),
  );

  const config = new DocumentBuilder()
    .setTitle('ShopEase API')
    .setDescription(
      'ShopEase Release 2 (M3): health probe plus interim catalog endpoints; full 24-operation surface is implemented across subsequent modules.',
    )
    .setVersion('2.0.0')
    .addServer(
      'http://10.0.2.2:3000/api/v1',
      'Android emulator to local staging',
    )
    .addServer(
      'https://api.staging.shopease.example/api/v1',
      'Staging',
    )
    .addBearerAuth()
    .build();

  const document = SwaggerModule.createDocument(app, config, {
    ignoreGlobalPrefix: true,
  });
  SwaggerModule.setup('api/docs', app, document, {
    useGlobalPrefix: false,
    jsonDocumentUrl: 'api/docs-json',
  });

  // Unprefixed infra probe (does not count against the /api/v1 operation cap).
  const healthService = app.get(HealthService);
  const httpAdapter = app.getHttpAdapter();
  httpAdapter.get('/health', async (_req: unknown, res: unknown) => {
    const response = res as {
      status: (code: number) => { json: (body: unknown) => void };
      statusCode?: number;
      json?: (body: unknown) => void;
    };
    try {
      const body = await healthService.getStatus();
      response.status(200).json(body);
    } catch (error) {
      const err = error as {
        getStatus?: () => number;
        getResponse?: () => unknown;
      };
      const status = err.getStatus?.() ?? 503;
      const payload = err.getResponse?.() ?? {
        statusCode: status,
        error: 'Service Unavailable',
        message: 'Database is unreachable',
      };
      response.status(status).json(payload);
    }
  });

  const prismaService = app.get(PrismaService);
  await prismaService.enableShutdownHooks(app);
}
