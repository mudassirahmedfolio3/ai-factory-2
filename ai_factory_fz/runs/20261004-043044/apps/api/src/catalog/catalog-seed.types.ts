export interface CatalogMoney {
  amountCents: number;
  currency: string;
}

export interface CatalogBrand {
  id: string;
  name: string;
  slug: string;
}

export interface CatalogCategory {
  id: string;
  name: string;
  slug: string;
  parentId: string | null;
  imageUrl: string | null;
  description: string | null;
  sortOrder: number;
}

export interface CatalogVariant {
  id: string;
  sku: string;
  label: string;
  price: CatalogMoney;
  compareAtPrice: CatalogMoney | null;
  stockQuantity: number;
  availableQuantity: number;
  finish: string | null;
  wattageW: number | null;
  colorTemperatureK: number | null;
  imageUrl: string | null;
  isDefault: boolean;
}

export interface CatalogImage {
  url: string;
  sortOrder: number;
  altText?: string | null;
}

export interface CatalogLightingSpecs {
  wattageW?: number | null;
  lumens?: number | null;
  colorTemperatureK?: number | null;
  lightType?: string | null;
  voltage?: string | null;
  dimmable?: boolean | null;
  material?: string | null;
  finish?: string | null;
  dimensionsMm?: string | null;
  ipRating?: string | null;
  bulbIncluded?: boolean | null;
  installationType?: string | null;
}

export interface CatalogReview {
  id: string;
  rating: number;
  title: string;
  body: string;
  authorDisplayName: string;
  createdAt: string;
}

export interface CatalogProduct {
  id: string;
  name: string;
  brand: string;
  brandSlug: string;
  slug: string;
  description: string;
  categoryId: string;
  primaryImageUrl: string;
  variants: CatalogVariant[];
  images: CatalogImage[];
  specs: CatalogLightingSpecs;
  reviews: CatalogReview[];
  popularityRank: number | null;
  unitsSold90Days: number;
  isFeatured: boolean;
  keywords?: string[];
  createdAt: string;
}

export interface CatalogHomeBanner {
  id: string;
  title: string;
  subtitle?: string | null;
  imageUrl: string;
  ctaLabel: string;
  categorySlug?: string | null;
  sortOrder: number;
}

export interface CatalogCoupon {
  id: string;
  code: string;
  description?: string | null;
  percentOff?: number | null;
  amountOffCents?: number | null;
  currency: string;
  minSubtotalCents?: number | null;
  expiresAt?: string | null;
  singleUsePerEmail: boolean;
  excludeSaleItems: boolean;
  isActive: boolean;
  categorySlugs: string[];
  productSlugs: string[];
}

export interface CatalogDocument {
  brands: CatalogBrand[];
  categories: CatalogCategory[];
  products: CatalogProduct[];
  homeBanners?: CatalogHomeBanner[];
  coupons?: CatalogCoupon[];
}
