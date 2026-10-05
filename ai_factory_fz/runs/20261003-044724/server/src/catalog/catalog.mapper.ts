import type {
  CategoryResponse,
  ProductDetailResponse,
  ProductSummaryResponse,
} from './dto/catalog.responses.js';
import { AvailabilityStatus } from './dto/catalog.responses.js';

export type CatalogVariantRow = {
  id: string;
  sku: string;
  name: string;
  priceCents: number;
  currency: string;
  stockQuantity: number;
  reservedQuantity: number;
  imageUrl: string | null;
  isDefault: boolean;
  isActive: boolean;
};

export type CatalogProductRow = {
  id: string;
  name: string;
  brand: string;
  description: string;
  primaryImageUrl: string;
  createdAt: Date;
  category: { id: string; slug: string; name: string };
  variants: CatalogVariantRow[];
};

export function stockAvailable(variant: {
  stockQuantity: number;
  reservedQuantity: number;
}): number {
  return Math.max(0, variant.stockQuantity - variant.reservedQuantity);
}

export function productAvailability(
  variants: Array<{ stockQuantity: number; reservedQuantity: number }>,
  lowStockThreshold: number,
): AvailabilityStatus {
  const maxAvailable = variants.reduce(
    (max, variant) => Math.max(max, stockAvailable(variant)),
    0,
  );
  if (maxAvailable <= 0) {
    return AvailabilityStatus.OUT_OF_STOCK;
  }
  if (maxAvailable <= lowStockThreshold) {
    return AvailabilityStatus.LOW_STOCK;
  }
  return AvailabilityStatus.IN_STOCK;
}

function activeVariants(variants: CatalogVariantRow[]): CatalogVariantRow[] {
  const active = variants.filter((variant) => variant.isActive);
  return active.length > 0 ? active : variants;
}

export function pickDisplayVariant(
  variants: CatalogVariantRow[],
): CatalogVariantRow | undefined {
  const pool = activeVariants(variants);
  return pool.find((variant) => variant.isDefault) ?? pool[0];
}

export function toCategoryResponse(
  category: { id: string; slug: string; name: string },
): CategoryResponse {
  return { id: category.id, slug: category.slug, name: category.name };
}

export function toProductSummary(
  product: CatalogProductRow,
  lowStockThreshold: number,
): ProductSummaryResponse {
  const variants = activeVariants(product.variants);
  const displayVariant = pickDisplayVariant(product.variants);
  const availability = productAvailability(variants, lowStockThreshold);

  return {
    id: product.id,
    name: product.name,
    brand: product.brand,
    category: toCategoryResponse(product.category),
    primaryImageUrl: product.primaryImageUrl,
    price: {
      amountCents: displayVariant?.priceCents ?? 0,
      currency: displayVariant?.currency ?? 'USD',
    },
    availability,
  };
}

export function toProductDetail(
  product: CatalogProductRow,
  lowStockThreshold: number,
): ProductDetailResponse {
  const variants = activeVariants(product.variants);
  const displayVariant = pickDisplayVariant(product.variants);
  const availability = productAvailability(variants, lowStockThreshold);

  return {
    id: product.id,
    name: product.name,
    brand: product.brand,
    description: product.description,
    category: toCategoryResponse(product.category),
    primaryImageUrl: product.primaryImageUrl,
    price: {
      amountCents: displayVariant?.priceCents ?? 0,
      currency: displayVariant?.currency ?? 'USD',
    },
    availability,
    variants: variants.map((variant) => ({
      id: variant.id,
      sku: variant.sku,
      name: variant.name,
      price: {
        amountCents: variant.priceCents,
        currency: variant.currency,
      },
      stockAvailable: stockAvailable(variant),
      ...(variant.imageUrl ? { imageUrl: variant.imageUrl } : {}),
      isDefault: variant.isDefault,
    })),
  };
}
