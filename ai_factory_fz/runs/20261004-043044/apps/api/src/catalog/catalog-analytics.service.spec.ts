import { ConfigService } from '@nestjs/config';
import { CatalogAnalyticsService } from './catalog-analytics.service';
import { PrismaService } from '../prisma/prisma.service';

describe('CatalogAnalyticsService', () => {
  const productId = 'p1111111-1111-4111-8111-111111111101';
  let productViewEventCreate: jest.Mock;
  let service: CatalogAnalyticsService;

  const buildService = (persist: boolean) => {
    productViewEventCreate = jest.fn().mockResolvedValue({ id: 'evt-1' });
    const prisma = {
      productViewEvent: { create: productViewEventCreate },
    };
    const configService = {
      get: jest.fn((key: string) =>
        key === 'ANALYTICS_PERSIST_PRODUCT_VIEWS' ? (persist ? 1 : 0) : undefined,
      ),
    };
    service = new CatalogAnalyticsService(
      prisma as unknown as PrismaService,
      configService as unknown as ConfigService,
    );
    jest.spyOn(service['logger'], 'log').mockImplementation();
    jest.spyOn(service['logger'], 'warn').mockImplementation();
  };

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('logs product_view without persisting when ANALYTICS_PERSIST_PRODUCT_VIEWS is off', () => {
    buildService(false);
    service.recordProductView(productId, {
      userId: 'u1',
      sessionId: 'guest-cart-id',
    });

    expect(productViewEventCreate).not.toHaveBeenCalled();
    expect(service['logger'].log).toHaveBeenCalledWith(
      expect.stringContaining('[Analytics] product_view'),
    );
  });

  it('persists ProductViewEvent when persistence is enabled', async () => {
    buildService(true);
    service.recordProductView(productId, {
      userId: null,
      sessionId: '  abc-session  ',
    });

    await new Promise((resolve) => setImmediate(resolve));

    expect(productViewEventCreate).toHaveBeenCalledWith({
      data: {
        productId,
        userId: undefined,
        sessionId: 'abc-session',
      },
    });
  });

  it('warns and does not throw when persistence fails', async () => {
    buildService(true);
    productViewEventCreate.mockRejectedValue(new Error('db down'));

    service.recordProductView(productId);

    await new Promise((resolve) => setImmediate(resolve));

    expect(service['logger'].warn).toHaveBeenCalledWith(
      expect.stringContaining('persistence failed'),
    );
  });
});
