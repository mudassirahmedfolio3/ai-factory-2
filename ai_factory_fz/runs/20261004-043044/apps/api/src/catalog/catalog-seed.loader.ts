import { existsSync, readFileSync } from 'fs';
import { join } from 'path';
import { Decimal } from '@prisma/client/runtime/library';
import {
  M3_CATALOG_PARITY,
  M1_SPOT_CHECK_SKUS,
} from './catalog-seed.constants';
import type { CatalogDocument, CatalogReview } from './catalog-seed.types';

export function resolveCatalogJsonPath(): string {
  const envPath = process.env.CATALOG_SEED_PATH;
  if (envPath && existsSync(envPath)) {
    return envPath;
  }

  const bundled = join(process.cwd(), 'prisma/data/catalog.json');
  if (existsSync(bundled)) {
    return bundled;
  }

  const monorepoApp = join(
    process.cwd(),
    '../../app/assets/data/catalog.json',
  );
  if (existsSync(monorepoApp)) {
    return monorepoApp;
  }

  throw new Error(
    'Catalog seed JSON not found. Set CATALOG_SEED_PATH or place catalog.json under prisma/data/.',
  );
}

export function loadCatalogDocument(filePath?: string): CatalogDocument {
  const path = filePath ?? resolveCatalogJsonPath();
  const raw = readFileSync(path, 'utf8');
  return JSON.parse(raw) as CatalogDocument;
}

export function computeAverageRating(reviews: CatalogReview[]): Decimal {
  if (reviews.length === 0) {
    return new Decimal(0);
  }
  const sum = reviews.reduce((acc, review) => acc + review.rating, 0);
  const average = sum / reviews.length;
  return new Decimal(average.toFixed(2));
}

export function variantReservedQuantity(
  stockQuantity: number,
  availableQuantity: number,
): number {
  return Math.max(0, stockQuantity - availableQuantity);
}

export function assertM3CatalogParity(document: CatalogDocument): void {
  const variantCount = document.products.reduce(
    (count, product) => count + product.variants.length,
    0,
  );
  const featuredCount = document.products.filter((p) => p.isFeatured).length;

  if (document.brands.length !== M3_CATALOG_PARITY.brandCount) {
    throw new Error(
      `Expected ${M3_CATALOG_PARITY.brandCount} brands, got ${document.brands.length}`,
    );
  }
  if (document.categories.length !== M3_CATALOG_PARITY.categoryCount) {
    throw new Error(
      `Expected ${M3_CATALOG_PARITY.categoryCount} categories, got ${document.categories.length}`,
    );
  }
  if (
    document.products.length < M3_CATALOG_PARITY.minProductCount ||
    document.products.length > M3_CATALOG_PARITY.maxProductCount
  ) {
    throw new Error(
      `Expected ${M3_CATALOG_PARITY.minProductCount}-${M3_CATALOG_PARITY.maxProductCount} products, got ${document.products.length}`,
    );
  }
  if (document.products.length !== M3_CATALOG_PARITY.productCount) {
    throw new Error(
      `Expected ${M3_CATALOG_PARITY.productCount} products for M3 seed, got ${document.products.length}`,
    );
  }
  if (variantCount !== M3_CATALOG_PARITY.variantCount) {
    throw new Error(
      `Expected ${M3_CATALOG_PARITY.variantCount} variants, got ${variantCount}`,
    );
  }
  if (featuredCount !== M3_CATALOG_PARITY.featuredProductCount) {
    throw new Error(
      `Expected ${M3_CATALOG_PARITY.featuredProductCount} featured products, got ${featuredCount}`,
    );
  }

  const bannerCount = document.homeBanners?.length ?? 0;
  if (bannerCount !== M3_CATALOG_PARITY.homeBannerCount) {
    throw new Error(
      `Expected ${M3_CATALOG_PARITY.homeBannerCount} home banners, got ${bannerCount}`,
    );
  }

  const couponCount = document.coupons?.length ?? 0;
  if (couponCount !== M3_CATALOG_PARITY.couponCount) {
    throw new Error(
      `Expected ${M3_CATALOG_PARITY.couponCount} coupons, got ${couponCount}`,
    );
  }

  assertBundledCatalogImagery(document.products);
  assertSpotCheckSkus(document.products);
  assertCouponCrossRefs(document);
}

/** @deprecated Use assertM3CatalogParity */
export const assertM1CatalogParity = assertM3CatalogParity;

function assertBundledCatalogImagery(
  products: CatalogDocument['products'],
): void {
  for (const product of products) {
    if (!product.primaryImageUrl.startsWith('assets/catalog/images/')) {
      throw new Error(
        `Product ${product.slug} must use bundled assets/catalog/images path`,
      );
    }
    if (product.primaryImageUrl.includes('placeholder')) {
      throw new Error(`Product ${product.slug} still uses placeholder imagery`);
    }
  }
}

function assertCouponCrossRefs(document: CatalogDocument): void {
  const categorySlugs = new Set(document.categories.map((c) => c.slug));
  const productSlugs = new Set(document.products.map((p) => p.slug));

  for (const coupon of document.coupons ?? []) {
    for (const slug of coupon.categorySlugs) {
      if (!categorySlugs.has(slug)) {
        throw new Error(
          `Coupon ${coupon.code} references unknown category slug ${slug}`,
        );
      }
    }
    for (const slug of coupon.productSlugs) {
      if (!productSlugs.has(slug)) {
        throw new Error(
          `Coupon ${coupon.code} references unknown product slug ${slug}`,
        );
      }
    }
  }
}

export function categoryIdBySlug(
  document: CatalogDocument,
  categorySlug: string,
): string {
  const category = document.categories.find((item) => item.slug === categorySlug);
  if (!category) {
    throw new Error(`Unknown category slug: ${categorySlug}`);
  }
  return category.id;
}

export function productIdBySlug(
  document: CatalogDocument,
  productSlug: string,
): string {
  const product = document.products.find((item) => item.slug === productSlug);
  if (!product) {
    throw new Error(`Unknown product slug: ${productSlug}`);
  }
  return product.id;
}

function assertSpotCheckSkus(
  products: CatalogDocument['products'],
): void {
  const bySku = new Map<string, CatalogDocument['products'][0]['variants'][0]>();
  for (const product of products) {
    for (const variant of product.variants) {
      bySku.set(variant.sku, variant);
    }
  }

  const white = bySku.get(M1_SPOT_CHECK_SKUS.CL_1001_WH.sku);
  if (!white) {
    throw new Error(
      `Missing spot-check SKU ${M1_SPOT_CHECK_SKUS.CL_1001_WH.sku}`,
    );
  }
  if (
    white.price.amountCents !== M1_SPOT_CHECK_SKUS.CL_1001_WH.priceCents
  ) {
    throw new Error('CL-1001-WH price mismatch');
  }
  if (white.price.currency !== M1_SPOT_CHECK_SKUS.CL_1001_WH.currency) {
    throw new Error('CL-1001-WH currency mismatch');
  }
  if (!white.isDefault) {
    throw new Error('CL-1001-WH should be default variant');
  }

  const black = bySku.get(M1_SPOT_CHECK_SKUS.CL_1001_BK.sku);
  if (!black) {
    throw new Error(
      `Missing spot-check SKU ${M1_SPOT_CHECK_SKUS.CL_1001_BK.sku}`,
    );
  }
  if (
    black.price.amountCents !== M1_SPOT_CHECK_SKUS.CL_1001_BK.priceCents
  ) {
    throw new Error('CL-1001-BK price mismatch');
  }
  if (
    black.stockQuantity !== M1_SPOT_CHECK_SKUS.CL_1001_BK.stockQuantity
  ) {
    throw new Error('CL-1001-BK stock mismatch');
  }
}

export function brandIdBySlug(
  document: CatalogDocument,
  brandSlug: string,
): string {
  const brand = document.brands.find((item) => item.slug === brandSlug);
  if (!brand) {
    throw new Error(`Unknown brand slug: ${brandSlug}`);
  }
  return brand.id;
}
