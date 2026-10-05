import { INestApplication } from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import { App } from 'supertest/types.js';
import { AppModule } from '../src/app.module.js';
import { setupApplication } from '../src/app.setup.js';
import { PrismaService } from '../src/prisma/prisma.service.js';

export function isE2eDatabaseAvailable(): boolean {
  return process.env.E2E_DATABASE_AVAILABLE === '1';
}

/** Minimal Prisma stub so Nest bootstraps and Swagger is emitted without Postgres. */
export function healthyPrismaStub(): Pick<
  PrismaService,
  '$queryRawUnsafe' | 'onModuleInit' | 'enableShutdownHooks'
> {
  return {
    $queryRawUnsafe: () => Promise.resolve([{ '?column?': 1 }]),
    onModuleInit: () => Promise.resolve(),
    enableShutdownHooks: () => Promise.resolve(),
  };
}

/** Prisma stub that simulates an unreachable database for health 503 cases. */
export function unreachableDatabasePrismaStub(): Pick<
  PrismaService,
  '$queryRawUnsafe' | 'onModuleInit' | 'enableShutdownHooks'
> {
  return {
    $queryRawUnsafe: () =>
      Promise.reject(new Error('connection terminated unexpectedly')),
    onModuleInit: () => Promise.resolve(),
    enableShutdownHooks: () => Promise.resolve(),
  };
}

type CreateE2eAppOptions = {
  prisma?: Partial<PrismaService>;
};

export async function createE2eApp(
  options: CreateE2eAppOptions = {},
): Promise<INestApplication<App>> {
  const prismaOverride = options.prisma ?? healthyPrismaStub();

  const moduleFixture: TestingModule = await Test.createTestingModule({
    imports: [AppModule],
  })
    .overrideProvider(PrismaService)
    .useValue(prismaOverride)
    .compile();

  const app = moduleFixture.createNestApplication();
  await setupApplication(app);
  await app.init();
  return app;
}

export async function createE2eAppWithRealPrisma(): Promise<
  INestApplication<App>
> {
  const moduleFixture: TestingModule = await Test.createTestingModule({
    imports: [AppModule],
  }).compile();

  const app = moduleFixture.createNestApplication();
  await setupApplication(app);
  await app.init();
  return app;
}
