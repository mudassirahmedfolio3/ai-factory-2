import {
  Category,
  HomeBanner,
  LightingSpecification,
  Product,
  ProductImage,
  ProductVariant,
  Review,
} from '@prisma/client';
import { HomeBannerDto } from './dto/home-banner.dto';
import { CategorySummaryDto } from './dto/category-summary.dto';
import { LightingSpecsDto } from './dto/lighting-specs.dto';
import { MoneyDto } from './dto/money.dto';
import { ProductDetailDto } from './dto/product-detail.dto';
import { ProductImageDto } from './dto/product-image.dto';
import { ProductSummaryDto } from './dto/product-summary.dto';
import { ProductVariantDto } from './dto/product-variant.dto';
import { RatingSummaryDto } from './dto/rating-summary.dto';
import { ReviewDto } from './dto/review.dto';

export function variantAvailableQuantity(variant: ProductVariant): number {
  return Math.max(0, variant.stockQuantity - variant.reservedQuantity);
}

export type CategoryRecord = Pick<
  Category,
  'id' | 'name' | 'slug' | 'parentId' | 'imageUrl'
>;

export type ProductWithRelations = Product & {
  brand: { name: string };
  category: CategoryRecord;
  variants: ProductVariant[];
};

export function toMoney(amountCents: number, currency: string): MoneyDto {
  return { amountCents, currency };
}

export function toHomeBannerDto(banner: HomeBanner): HomeBannerDto {
  const dto: HomeBannerDto = {
    id: banner.id,
    title: banner.title,
    imageUrl: banner.imageUrl,
    ctaLabel: banner.ctaLabel,
  };
  if (banner.subtitle) {
    dto.subtitle = banner.subtitle;
  }
  if (banner.categorySlug) {
    dto.categorySlug = banner.categorySlug;
  }
  return dto;
}

export function toCategorySummary(category: CategoryRecord): CategorySummaryDto {
  const summary: CategorySummaryDto = {
    id: category.id,
    name: category.name,
    slug: category.slug,
  };
  if (category.parentId !== null) {
    summary.parentId = category.parentId;
  }
  if (category.imageUrl) {
    summary.imageUrl = category.imageUrl;
  }
  return summary;
}

export function toRatingSummary(
  averageRating: Product['averageRating'],
  reviewCount: number,
): RatingSummaryDto {
  return {
    averageRating: Number(averageRating),
    reviewCount,
  };
}

export function pickListingVariant(
  variants: ProductVariant[],
): ProductVariant | undefined {
  const active = variants.filter((v) => v.isActive);
  if (active.length === 0) {
    return undefined;
  }
  return active.find((v) => v.isDefault) ?? active[0];
}

export function productInStock(variants: ProductVariant[]): boolean {
  return variants.some(
    (v) =>
      v.isActive &&
      v.stockQuantity - v.reservedQuantity > 0,
  );
}

export function toProductSummary(product: ProductWithRelations): ProductSummaryDto {
  const variant = pickListingVariant(product.variants);
  const priceCents = variant?.priceCents ?? 0;
  const currency = variant?.currency ?? 'GBP';

  const summary: ProductSummaryDto = {
    id: product.id,
    name: product.name,
    brand: product.brand.name,
    slug: product.slug,
    category: toCategorySummary(product.category),
    price: toMoney(priceCents, currency),
    primaryImageUrl: product.primaryImageUrl,
    inStock: productInStock(product.variants),
    rating: toRatingSummary(product.averageRating, product.reviewCount),
  };

  if (variant?.compareAtCents != null) {
    summary.compareAtPrice = toMoney(variant.compareAtCents, currency);
  } else {
    summary.compareAtPrice = null;
  }

  if (product.popularityRank != null) {
    summary.popularityRank = product.popularityRank;
  } else {
    summary.popularityRank = null;
  }

  return summary;
}

export type ProductDetailWithRelations = ProductWithRelations & {
  description: string;
  unitsSold90Days: number;
  specs: LightingSpecification | null;
  images: ProductImage[];
};

function assignOptionalSpecField<T extends keyof LightingSpecsDto>(
  target: LightingSpecsDto,
  key: T,
  value: LightingSpecsDto[T] | null | undefined,
): void {
  if (value !== null && value !== undefined) {
    target[key] = value;
  }
}

export function toLightingSpecs(
  specs: LightingSpecification | null,
): LightingSpecsDto {
  const dto: LightingSpecsDto = {};
  if (!specs) {
    return dto;
  }
  assignOptionalSpecField(dto, 'wattageW', specs.wattageW);
  assignOptionalSpecField(dto, 'lumens', specs.lumens);
  assignOptionalSpecField(dto, 'colorTemperatureK', specs.colorTemperatureK);
  assignOptionalSpecField(dto, 'lightType', specs.lightType);
  assignOptionalSpecField(dto, 'voltage', specs.voltage);
  assignOptionalSpecField(dto, 'dimmable', specs.dimmable);
  assignOptionalSpecField(dto, 'material', specs.material);
  assignOptionalSpecField(dto, 'finish', specs.finish);
  assignOptionalSpecField(dto, 'dimensionsMm', specs.dimensionsMm);
  assignOptionalSpecField(dto, 'ipRating', specs.ipRating);
  assignOptionalSpecField(dto, 'bulbIncluded', specs.bulbIncluded);
  assignOptionalSpecField(dto, 'installationType', specs.installationType);
  return dto;
}

export function toProductVariantDto(variant: ProductVariant): ProductVariantDto {
  const dto: ProductVariantDto = {
    id: variant.id,
    sku: variant.sku,
    label: variant.label,
    price: toMoney(variant.priceCents, variant.currency),
    stockQuantity: variant.stockQuantity,
    availableQuantity: variantAvailableQuantity(variant),
    isDefault: variant.isDefault,
  };

  if (variant.compareAtCents != null) {
    dto.compareAtPrice = toMoney(variant.compareAtCents, variant.currency);
  } else {
    dto.compareAtPrice = null;
  }

  if (variant.finish) {
    dto.finish = variant.finish;
  }
  if (variant.wattageW != null) {
    dto.wattageW = variant.wattageW;
  }
  if (variant.colorTemperatureK != null) {
    dto.colorTemperatureK = variant.colorTemperatureK;
  }
  if (variant.imageUrl) {
    dto.imageUrl = variant.imageUrl;
  }

  return dto;
}

export function toProductImageDto(image: ProductImage): ProductImageDto {
  const dto: ProductImageDto = {
    url: image.url,
    sortOrder: image.sortOrder,
  };
  if (image.altText) {
    dto.altText = image.altText;
  }
  return dto;
}

export function toProductDetail(product: ProductDetailWithRelations): ProductDetailDto {
  const summary = toProductSummary(product);
  const activeVariants = product.variants
    .filter((v) => v.isActive)
    .sort((a, b) => {
      if (a.isDefault !== b.isDefault) {
        return a.isDefault ? -1 : 1;
      }
      return a.sku.localeCompare(b.sku);
    });

  const detail: ProductDetailDto = {
    id: summary.id,
    name: summary.name,
    brand: summary.brand,
    slug: summary.slug,
    description: product.description,
    category: summary.category,
    price: summary.price,
    primaryImageUrl: summary.primaryImageUrl,
    inStock: summary.inStock,
    variants: activeVariants.map(toProductVariantDto),
    images: product.images
      .slice()
      .sort((a, b) => a.sortOrder - b.sortOrder)
      .map(toProductImageDto),
    specs: toLightingSpecs(product.specs),
    rating: summary.rating,
  };

  if (summary.compareAtPrice !== undefined) {
    detail.compareAtPrice = summary.compareAtPrice;
  }

  if (summary.popularityRank !== undefined) {
    detail.popularityRank = summary.popularityRank;
  }

  detail.unitsSold90Days = product.unitsSold90Days;

  return detail;
}

export function toReviewDto(review: Review): ReviewDto {
  return {
    id: review.id,
    rating: review.rating,
    title: review.title,
    body: review.body,
    authorDisplayName: review.authorDisplayName,
    createdAt: review.createdAt.toISOString(),
  };
}
