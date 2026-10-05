import { INestApplication, ValidationPipe } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { Test, TestingModule } from '@nestjs/testing';
import request from 'supertest';
import { AppModule } from '../app.module';
import { PrismaService } from '../prisma/prisma.service';

const userId = '11111111-1111-4111-8111-111111111111';

describe('UsersController (e2e)', () => {
  let app: INestApplication;
  let jwtService: JwtService;
  let userFindFirst: jest.Mock;
  let userFindFirstOrThrow: jest.Mock;
  let userUpdate: jest.Mock;
  let refreshUpdateMany: jest.Mock;
  let transaction: jest.Mock;

  beforeAll(async () => {
    userFindFirst = jest.fn();
    userFindFirstOrThrow = jest.fn();
    userUpdate = jest.fn();
    refreshUpdateMany = jest.fn();
    transaction = jest.fn((ops: unknown[]) => Promise.all(ops));

    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(PrismaService)
      .useValue({
        onModuleInit: jest.fn().mockResolvedValue(undefined),
        onModuleDestroy: jest.fn().mockResolvedValue(undefined),
        pingDatabase: jest.fn(),
        user: {
          findFirst: userFindFirst,
          findFirstOrThrow: userFindFirstOrThrow,
          update: userUpdate,
        },
        refreshToken: {
          updateMany: refreshUpdateMany,
        },
        $transaction: transaction,
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

    jwtService = moduleFixture.get(JwtService);
  });

  afterAll(async () => {
    await app?.close();
  });

  function bearerToken(): string {
    return jwtService.sign({ sub: userId, typ: 'access' });
  }

  it('getCurrentUser — GET /api/v1/users/me returns profile', async () => {
    userFindFirst.mockResolvedValue({
      id: userId,
      email: 'shopper@example.com',
      displayName: 'Alex Morgan',
    });
    userFindFirstOrThrow.mockResolvedValue({
      id: userId,
      email: 'shopper@example.com',
      displayName: 'Alex Morgan',
    });

    const response = await request(app.getHttpServer())
      .get('/api/v1/users/me')
      .set('Authorization', `Bearer ${bearerToken()}`)
      .expect(200);

    expect(response.body).toEqual({
      id: userId,
      email: 'shopper@example.com',
      displayName: 'Alex Morgan',
    });
  });

  it('deleteCurrentUser — DELETE /api/v1/users/me returns 204', async () => {
    userFindFirst.mockResolvedValue({
      id: userId,
      email: 'shopper@example.com',
      displayName: 'Alex Morgan',
    });

    await request(app.getHttpServer())
      .delete('/api/v1/users/me')
      .set('Authorization', `Bearer ${bearerToken()}`)
      .expect(204);

    expect(transaction).toHaveBeenCalled();
    expect(userUpdate).toHaveBeenCalledWith({
      where: { id: userId },
      data: expect.objectContaining({
        email: `deleted+${userId}@deleted.invalid`,
        passwordHash: null,
        displayName: null,
      }),
    });
  });

  it('getCurrentUser — returns 401 without bearer token', async () => {
    await request(app.getHttpServer()).get('/api/v1/users/me').expect(401);
  });
});
