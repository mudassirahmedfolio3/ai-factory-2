import { existsSync, readFileSync } from 'fs';
import { join } from 'path';
import { loadCatalogDocument } from './catalog-seed.loader';

describe('catalog-image-manifest', () => {
  const manifestPath = join(process.cwd(), 'prisma/data/catalog-image-manifest.json');
  const repoRoot = join(process.cwd(), '../..');
  const flutterImages = join(repoRoot, 'app/assets/catalog/images');
  const apiStaticImages = join(process.cwd(), 'static/catalog/images');

  it('lists bundled files for every catalog product slug', () => {
    const catalog = loadCatalogDocument();
    const manifest = JSON.parse(readFileSync(manifestPath, 'utf8')) as {
      images: Array<{ productSlug: string | null; filename: string }>;
    };
    const slugsInManifest = new Set(
      manifest.images
        .map((row) => row.productSlug)
        .filter((slug): slug is string => slug != null),
    );

    for (const product of catalog.products) {
      expect(slugsInManifest.has(product.slug)).toBe(true);
      const filename = `${product.slug}.jpg`;
      expect(existsSync(join(flutterImages, filename))).toBe(true);
      expect(existsSync(join(apiStaticImages, filename))).toBe(true);
    }
  });
});
