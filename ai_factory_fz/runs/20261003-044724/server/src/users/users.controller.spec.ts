import { INestApplication } from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import request from 'supertest';
import { App } from 'supertest/types.js';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard.js';
import { UsersController } from './users.controller.js';
import { UsersService } from './users.service.js';

describe('UsersController (Supertest)', () => {
  let app: INestApplication<App>;
  const usersService = {
    deleteAccount: vi.fn(),
  };

  beforeEach(async () => {
    vi.resetAllMocks();
    const moduleFixture: TestingModule = await Test.createTestingModule({
      controllers: [UsersController],
      providers: [{ provide: UsersService, useValue: usersService }],
    })
      .overrideGuard(JwtAuthGuard)
      .useValue({
        canActivate: (context: {
          switchToHttp: () => {
            getRequest: () => { user?: { id: string } };
          };
        }) => {
          const req = context.switchToHttp().getRequest();
          req.user = { id: 'user-1', email: 'shopper@example.com' };
          return true;
        },
      })
      .compile();

    app = moduleFixture.createNestApplication();
    app.setGlobalPrefix('api/v1');
    await app.init();
  });

  afterEach(async () => {
    await app.close();
  });

  it('DELETE /api/v1/users/me returns 204', async () => {
    usersService.deleteAccount.mockResolvedValue(undefined);

    const res = await request(app.getHttpServer())
      .delete('/api/v1/users/me')
      .set('Authorization', 'Bearer test-token');

    expect(res.status).toBe(204);
    expect(usersService.deleteAccount).toHaveBeenCalledWith('user-1');
  });
});
