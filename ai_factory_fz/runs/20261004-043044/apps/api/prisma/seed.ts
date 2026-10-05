import { runDatabaseSeed } from '../src/seed/database-seed';

async function main(): Promise<void> {
  await runDatabaseSeed();
  console.log('Catalog seed completed (M3 production catalog).');
  console.log('Demo order history seed completed (shopper@example.com).');
}

main().catch((error: unknown) => {
  console.error(error);
  process.exit(1);
});
