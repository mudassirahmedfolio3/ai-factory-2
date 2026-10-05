import { CatalogSeedService } from '../catalog/catalog-seed.service';
import { OrdersSeedService } from '../orders/orders-seed.service';
import { PrismaService } from '../prisma/prisma.service';

/** Idempotent M3 catalog + demo orders seed (used by Prisma seed and Docker entrypoint). */
export async function runDatabaseSeed(): Promise<void> {
  const prisma = new PrismaService();
  await prisma.$connect();
  const catalogSeed = new CatalogSeedService(prisma);
  const ordersSeed = new OrdersSeedService(prisma);
  try {
    await catalogSeed.seedCatalog();
    await ordersSeed.seedDemoOrders();
  } finally {
    await prisma.$disconnect();
  }
}

async function main(): Promise<void> {
  await runDatabaseSeed();
  console.log('Database seed completed (M3 catalog + demo orders).');
}

if (require.main === module) {
  main().catch((error: unknown) => {
    console.error(error);
    process.exit(1);
  });
}
