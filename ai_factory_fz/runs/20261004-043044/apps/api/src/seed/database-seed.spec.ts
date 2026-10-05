import { runDatabaseSeed } from './database-seed';

const seedCatalog = jest.fn().mockResolvedValue(undefined);
const seedDemoOrders = jest.fn().mockResolvedValue(undefined);
const connect = jest.fn().mockResolvedValue(undefined);
const disconnect = jest.fn().mockResolvedValue(undefined);

jest.mock('../catalog/catalog-seed.service', () => ({
  CatalogSeedService: jest.fn().mockImplementation(() => ({ seedCatalog })),
}));

jest.mock('../orders/orders-seed.service', () => ({
  OrdersSeedService: jest.fn().mockImplementation(() => ({ seedDemoOrders })),
}));

jest.mock('../prisma/prisma.service', () => ({
  PrismaService: jest.fn().mockImplementation(() => ({
    $connect: connect,
    $disconnect: disconnect,
  })),
}));

describe('runDatabaseSeed', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('seeds catalog then demo orders and disconnects Prisma', async () => {
    await runDatabaseSeed();

    expect(connect).toHaveBeenCalledTimes(1);
    expect(seedCatalog).toHaveBeenCalledTimes(1);
    expect(seedDemoOrders).toHaveBeenCalledTimes(1);
    expect(disconnect).toHaveBeenCalledTimes(1);
  });
});
