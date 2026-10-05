import { Injectable } from '@nestjs/common';
import { Prisma } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import {
  assertM3CatalogParity,
  brandIdBySlug,
  categoryIdBySlug,
  computeAverageRating,
  loadCatalogDocument,
  productIdBySlug,
  variantReservedQuantity,
} from './catalog-seed.loader';
import type { CatalogDocument } from './catalog-seed.types';

type CatalogTransaction = Prisma.TransactionClient;

@Injectable()
export class CatalogSeedService {
  constructor(private readonly prisma: PrismaService) {}

  loadAndValidateDocument(): CatalogDocument {
    const document = loadCatalogDocument();
    assertM3CatalogParity(document);
    return document;
  }

  async seedCatalog(document?: CatalogDocument): Promise<void> {
    const catalog = document ?? this.loadAndValidateDocument();
    await this.prisma.$transaction(async (tx) => {
      await this.clearCatalog(tx);
      await this.insertCatalog(tx, catalog);
    });
  }

  async clearCatalog(tx: CatalogTransaction): Promise<void> {
    await tx.couponRedemption.deleteMany();
    await tx.couponCategory.deleteMany();
    await tx.couponProduct.deleteMany();
    await tx.coupon.deleteMany();
    await tx.homeBanner.deleteMany();
    await tx.review.deleteMany();
    await tx.productImage.deleteMany();
    await tx.lightingSpecification.deleteMany();
    await tx.productVariant.deleteMany();
    await tx.productViewEvent.deleteMany();
    await tx.wishlistItem.deleteMany();
    await tx.product.deleteMany();
    await tx.category.deleteMany();
    await tx.brand.deleteMany();
  }

  async insertCatalog(
    tx: CatalogTransaction,
    catalog: CatalogDocument,
  ): Promise<void> {
    for (const brand of catalog.brands) {
      await tx.brand.create({
        data: {
          id: brand.id,
          name: brand.name,
          slug: brand.slug,
        },
      });
    }

    const rootCategories = catalog.categories.filter((c) => c.parentId === null);
    const childCategories = catalog.categories.filter(
      (c) => c.parentId !== null,
    );

    for (const category of rootCategories) {
      await tx.category.create({
        data: {
          id: category.id,
          name: category.name,
          slug: category.slug,
          parentId: null,
          description: category.description,
          imageUrl: category.imageUrl,
          sortOrder: category.sortOrder,
        },
      });
    }

    for (const category of childCategories) {
      await tx.category.create({
        data: {
          id: category.id,
          name: category.name,
          slug: category.slug,
          parentId: category.parentId,
          description: category.description,
          imageUrl: category.imageUrl,
          sortOrder: category.sortOrder,
        },
      });
    }

    for (const product of catalog.products) {
      const brandId = brandIdBySlug(catalog, product.brandSlug);
      const averageRating = computeAverageRating(product.reviews);

      await tx.product.create({
        data: {
          id: product.id,
          categoryId: product.categoryId,
          brandId,
          name: product.name,
          slug: product.slug,
          description: product.description,
          primaryImageUrl: product.primaryImageUrl,
          isFeatured: product.isFeatured,
          popularityRank: product.popularityRank,
          unitsSold90Days: product.unitsSold90Days,
          averageRating,
          reviewCount: product.reviews.length,
          createdAt: new Date(product.createdAt),
          variants: {
            create: product.variants.map((variant) => ({
              id: variant.id,
              sku: variant.sku,
              label: variant.label,
              priceCents: variant.price.amountCents,
              compareAtCents: variant.compareAtPrice?.amountCents ?? null,
              currency: variant.price.currency,
              stockQuantity: variant.stockQuantity,
              reservedQuantity: variantReservedQuantity(
                variant.stockQuantity,
                variant.availableQuantity,
              ),
              finish: variant.finish,
              wattageW: variant.wattageW,
              colorTemperatureK: variant.colorTemperatureK,
              imageUrl: variant.imageUrl,
              isDefault: variant.isDefault,
            })),
          },
          images: {
            create: product.images.map((image) => ({
              url: image.url,
              altText: image.altText ?? null,
              sortOrder: image.sortOrder,
            })),
          },
          specs: {
            create: {
              wattageW: product.specs.wattageW ?? null,
              lumens: product.specs.lumens ?? null,
              colorTemperatureK: product.specs.colorTemperatureK ?? null,
              lightType: product.specs.lightType ?? null,
              voltage: product.specs.voltage ?? null,
              dimmable: product.specs.dimmable ?? null,
              material: product.specs.material ?? null,
              finish: product.specs.finish ?? null,
              dimensionsMm: product.specs.dimensionsMm ?? null,
              ipRating: product.specs.ipRating ?? null,
              bulbIncluded: product.specs.bulbIncluded ?? null,
              installationType: product.specs.installationType ?? null,
            },
          },
          reviews: {
            create: product.reviews.map((review) => ({
              id: review.id,
              rating: review.rating,
              title: review.title,
              body: review.body,
              authorDisplayName: review.authorDisplayName,
              createdAt: new Date(review.createdAt),
            })),
          },
        },
      });
    }

    for (const banner of catalog.homeBanners ?? []) {
      await tx.homeBanner.create({
        data: {
          id: banner.id,
          title: banner.title,
          subtitle: banner.subtitle ?? null,
          imageUrl: banner.imageUrl,
          ctaLabel: banner.ctaLabel,
          categorySlug: banner.categorySlug ?? null,
          sortOrder: banner.sortOrder,
        },
      });
    }

    await this.insertCoupons(tx, catalog);
  }

  async insertCoupons(
    tx: CatalogTransaction,
    catalog: CatalogDocument,
  ): Promise<void> {
    for (const coupon of catalog.coupons ?? []) {
      await tx.coupon.create({
        data: {
          id: coupon.id,
          code: coupon.code,
          description: coupon.description ?? null,
          percentOff: coupon.percentOff ?? null,
          amountOffCents: coupon.amountOffCents ?? null,
          currency: coupon.currency,
          minSubtotalCents: coupon.minSubtotalCents ?? null,
          expiresAt: coupon.expiresAt ? new Date(coupon.expiresAt) : null,
          singleUsePerEmail: coupon.singleUsePerEmail,
          excludeSaleItems: coupon.excludeSaleItems,
          isActive: coupon.isActive,
          categories: {
            create: coupon.categorySlugs.map((slug) => ({
              categoryId: categoryIdBySlug(catalog, slug),
            })),
          },
          products: {
            create: coupon.productSlugs.map((slug) => ({
              productId: productIdBySlug(catalog, slug),
            })),
          },
        },
      });
    }
  }
}
