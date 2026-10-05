import { LightingSpecification } from '@prisma/client';
import { ListProductsQueryDto, ProductSort } from './dto/list-products-query.dto';
import { ProductSummaryDto } from './dto/product-summary.dto';
import {
  ProductWithRelations,
  pickListingVariant,
  productInStock,
  toProductSummary,
} from './catalog.mapper';

export type ProductForFiltering = ProductWithRelations & {
  specs: LightingSpecification | null;
  createdAt: Date;
  unitsSold90Days: number;
};

function productWattageValues(product: ProductForFiltering): number[] {
  const values: number[] = [];
  if (product.specs?.wattageW != null) {
    values.push(product.specs.wattageW);
  }
  for (const variant of product.variants) {
    if (variant.isActive && variant.wattageW != null) {
      values.push(variant.wattageW);
    }
  }
  return values;
}

function productFinishValues(product: ProductForFiltering): string[] {
  const finishes = new Set<string>();
  if (product.specs?.finish) {
    finishes.add(product.specs.finish.toLowerCase());
  }
  for (const variant of product.variants) {
    if (variant.isActive && variant.finish) {
      finishes.add(variant.finish.toLowerCase());
    }
  }
  return [...finishes];
}

function listingPriceCents(product: ProductForFiltering): number {
  const variant = pickListingVariant(product.variants);
  return variant?.priceCents ?? 0;
}

export function productMatchesListQuery(
  product: ProductForFiltering,
  query: ListProductsQueryDto,
  categoryIds: string[] | undefined,
): boolean {
  if (categoryIds && !categoryIds.includes(product.category.id)) {
    return false;
  }

  if (query.brand?.length) {
    const allowed = new Set(query.brand.map((b) => b.toLowerCase()));
    if (!allowed.has(product.brand.name.toLowerCase())) {
      return false;
    }
  }

  if (query.q) {
    const term = query.q.toLowerCase();
    const matchesText =
      product.name.toLowerCase().includes(term) ||
      product.description.toLowerCase().includes(term) ||
      product.brand.name.toLowerCase().includes(term) ||
      product.variants.some(
        (v) => v.isActive && v.sku.toLowerCase().includes(term),
      );
    if (!matchesText) {
      return false;
    }
  }

  const price = listingPriceCents(product);
  if (query.minPriceCents != null && price < query.minPriceCents) {
    return false;
  }
  if (query.maxPriceCents != null && price > query.maxPriceCents) {
    return false;
  }

  if (query.minWattage != null || query.maxWattage != null) {
    const wattages = productWattageValues(product);
    if (wattages.length === 0) {
      return false;
    }
    const minW = query.minWattage ?? 0;
    const maxW = query.maxWattage ?? Number.MAX_SAFE_INTEGER;
    if (!wattages.some((w) => w >= minW && w <= maxW)) {
      return false;
    }
  }

  if (query.finish) {
    const target = query.finish.toLowerCase();
    if (!productFinishValues(product).includes(target)) {
      return false;
    }
  }

  if (query.inStockOnly && !productInStock(product.variants)) {
    return false;
  }

  return true;
}

export function sortProductsForListing(
  products: ProductForFiltering[],
  sort: ProductSort,
): ProductSummaryDto[] {
  const summaries = products.map((p) => toProductSummary(p));

  if (sort === ProductSort.PriceAsc) {
    return summaries.sort((a, b) => a.price.amountCents - b.price.amountCents);
  }
  if (sort === ProductSort.PriceDesc) {
    return summaries.sort((a, b) => b.price.amountCents - a.price.amountCents);
  }
  if (sort === ProductSort.Newest) {
    return products
      .slice()
      .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime())
      .map((p) => toProductSummary(p));
  }

  return products
    .slice()
    .sort((a, b) => {
      const rankA = a.popularityRank ?? Number.MAX_SAFE_INTEGER;
      const rankB = b.popularityRank ?? Number.MAX_SAFE_INTEGER;
      if (rankA !== rankB) {
        return rankA - rankB;
      }
      return b.unitsSold90Days - a.unitsSold90Days;
    })
    .map((p) => toProductSummary(p));
}

export function paginateItems<T>(
  items: T[],
  page: number,
  pageSize: number,
): { items: T[]; total: number; page: number; pageSize: number } {
  const total = items.length;
  const start = (page - 1) * pageSize;
  return {
    items: items.slice(start, start + pageSize),
    total,
    page,
    pageSize,
  };
}

export function listingPriceBounds(products: ProductForFiltering[]): {
  minPriceCents: number;
  maxPriceCents: number;
} {
  if (products.length === 0) {
    return { minPriceCents: 0, maxPriceCents: 0 };
  }
  const prices = products.map(listingPriceCents);
  return {
    minPriceCents: Math.min(...prices),
    maxPriceCents: Math.max(...prices),
  };
}

export function wattageBounds(products: ProductForFiltering[]): {
  minW: number;
  maxW: number;
} {
  const values = products.flatMap(productWattageValues);
  if (values.length === 0) {
    return { minW: 0, maxW: 0 };
  }
  return { minW: Math.min(...values), maxW: Math.max(...values) };
}

export function collectFinishes(products: ProductForFiltering[]): string[] {
  const finishes = new Set<string>();
  for (const product of products) {
    if (product.specs?.finish) {
      finishes.add(product.specs.finish);
    }
    for (const variant of product.variants) {
      if (variant.isActive && variant.finish) {
        finishes.add(variant.finish);
      }
    }
  }
  return [...finishes].sort((a, b) => a.localeCompare(b));
}
