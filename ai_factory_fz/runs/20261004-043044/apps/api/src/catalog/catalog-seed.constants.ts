/** Release 2 (M3) production catalog parity targets for bundled seed JSON. */
export const M3_CATALOG_PARITY = {
  brandCount: 5,
  categoryCount: 8,
  productCount: 24,
  variantCount: 29,
  featuredProductCount: 4,
  newArrivalProductCount: 4,
  homeBannerCount: 2,
  couponCount: 3,
  minProductCount: 18,
  maxProductCount: 30,
} as const;

/** @deprecated Use M3_CATALOG_PARITY — kept for existing test imports. */
export const M1_CATALOG_PARITY = M3_CATALOG_PARITY;

export const M1_SPOT_CHECK_SKUS = {
  CL_1001_WH: {
    sku: 'CL-1001-WH',
    priceCents: 4999,
    currency: 'GBP',
    isDefault: true,
  },
  CL_1001_BK: {
    sku: 'CL-1001-BK',
    priceCents: 5299,
    currency: 'GBP',
    stockQuantity: 0,
  },
} as const;
