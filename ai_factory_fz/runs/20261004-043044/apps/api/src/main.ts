import { ValidationPipe } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { readFileSync } from 'fs';
import { load } from 'js-yaml';
import { join } from 'path';
import { AppModule } from './app.module';

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule);
  app.setGlobalPrefix('api/v1');
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
    }),
  );

  const openApiPath = join(process.cwd(), 'openapi.yaml');
  const openApiDocument = load(readFileSync(openApiPath, 'utf8')) as Record<
    string,
    unknown
  >;

  const expressApp = app.getHttpAdapter().getInstance();
  expressApp.get('/api/docs-json', (_req: unknown, res: { json: (body: unknown) => void }) => {
    res.json(openApiDocument);
  });

  const port = Number(process.env.PORT ?? 3000);
  await app.listen(port, '0.0.0.0');
}

void bootstrap();
