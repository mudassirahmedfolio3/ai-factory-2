import { createHash } from 'node:crypto';
import bcrypt from 'bcrypt';
import {
  CouponExclusionKind,
  CouponType,
  OrderStatus,
  PaymentProvider,
  PaymentStatus,
  PrismaClient,
} from '@prisma/client';

const prisma = new PrismaClient();

function seedUuid(key: string): string {
  const hash = createHash('sha256').update(`demo-retail:${key}`).digest('hex');
  return [
    hash.slice(0, 8),
    hash.slice(8, 12),
    `4${hash.slice(13, 16)}`,
    `${((parseInt(hash.slice(16, 18), 16) & 0x3f) | 0x80).toString(16)}${hash.slice(18, 20)}`,
    hash.slice(20, 32),
  ].join('-');
}

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

/** US-004 launch category entry points (design_system CategoryChip). */
const CATEGORIES = [
  { slug: 'clothing', name: 'Clothing', sortOrder: 1 },
  { slug: 'electronics', name: 'Electronics', sortOrder: 2 },
  { slug: 'home-kitchen', name: 'Home & Kitchen', sortOrder: 3 },
  { slug: 'beauty', name: 'Beauty', sortOrder: 4 },
  { slug: 'sports-outdoors', name: 'Sports & Outdoors', sortOrder: 5 },
] as const;

const DEMO_IMAGE_URLS = [
  'https://images.unsplash.com/photo-1584464491033-06628f3a6b7b?auto=format&fit=crop&w=1000&q=80',
  'https://images.unsplash.com/photo-1603006905003-be475563bc59?auto=format&fit=crop&w=1000&q=80',
  'https://images.unsplash.com/photo-1583947581924-a09ef8d9020c?auto=format&fit=crop&w=1000&q=80',
  'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=1000&q=80',
  'https://images.unsplash.com/photo-1571781926291-c477ebfd024b?auto=format&fit=crop&w=1000&q=80',
  'https://images.unsplash.com/photo-1616628182509-6f228f77f3f6?auto=format&fit=crop&w=1000&q=80',
  'https://images.unsplash.com/photo-1512909006721-3d6018887383?auto=format&fit=crop&w=1000&q=80',
  'https://images.unsplash.com/photo-1478145046317-39f10e56b5e9?auto=format&fit=crop&w=1000&q=80',
  'https://images.unsplash.com/photo-1601506521937-0121fc6b9ee9?auto=format&fit=crop&w=1000&q=80',
  'https://images.unsplash.com/photo-1621607512214-68297480165e?auto=format&fit=crop&w=1000&q=80',
  'https://images.unsplash.com/photo-1549465220-1a8b9238cd48?auto=format&fit=crop&w=1000&q=80',
  'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=1000&q=80',
] as const;

const PRODUCT_BRANDS = [
  'PureNest',
  'Lumen & Co',
  'TerraKind',
  'Northwind Goods',
  'Evergreen Supply',
  'BrightRoom',
  'KindRoot',
  'Summit Home',
  'Harbor & Hearth',
  'Velvet Lane',
  'Studio Oak',
  'GiftTheory',
] as const;

type SeedProduct = {
  key: string;
  name: string;
  description: string;
  categorySlug: string;
  brand: string;
  isFeatured: boolean;
  isNewArrival: boolean;
  imageUrl: string;
  variants: Array<{
    key: string;
    sku: string;
    name: string;
    priceCents: number;
    currency: string;
    stockQuantity: number;
    isDefault?: boolean;
  }>;
};

const CORE_PRODUCTS: SeedProduct[] = [
  {
    key: 'seed-product-1',
    name: 'Citrus Hand Soap',
    description:
      'A gentle citrus hand soap for everyday use, with a clean rinse and bright scent.',
    categorySlug: 'beauty',
    brand: PRODUCT_BRANDS[0],
    isFeatured: true,
    isNewArrival: false,
    imageUrl:
      'https://images.unsplash.com/photo-1584464491033-06628f3a6b7b?auto=format&fit=crop&w=1000&q=80',
    variants: [
      { key: 'seed-product-1-variant-1', sku: 'SHO-SOAP-300', name: '300 ml', priceCents: 799, currency: 'USD', stockQuantity: 16, isDefault: true },
      { key: 'seed-product-1-variant-2', sku: 'SHO-SOAP-500', name: '500 ml', priceCents: 1099, currency: 'USD', stockQuantity: 8 },
    ],
  },
  {
    key: 'seed-product-2',
    name: 'Aroma Candle',
    description: 'A long-burning aroma candle designed to add a warm, relaxed mood at home.',
    categorySlug: 'home-kitchen',
    brand: PRODUCT_BRANDS[1],
    isFeatured: true,
    isNewArrival: false,
    imageUrl:
      'https://images.unsplash.com/photo-1603006905003-be475563bc59?auto=format&fit=crop&w=1000&q=80',
    variants: [
      { key: 'seed-product-2-variant-1', sku: 'SHO-CAN-01', name: 'Standard', priceCents: 2499, currency: 'USD', stockQuantity: 24, isDefault: true },
    ],
  },
  {
    key: 'seed-product-3',
    name: 'Bamboo Toothbrush Set',
    description: 'A pair of bamboo toothbrushes for everyday sustainable brushing.',
    categorySlug: 'beauty',
    brand: PRODUCT_BRANDS[2],
    isFeatured: false,
    isNewArrival: true,
    imageUrl:
      'https://images.unsplash.com/photo-1583947581924-a09ef8d9020c?auto=format&fit=crop&w=1000&q=80',
    variants: [
      { key: 'seed-product-3-variant-1', sku: 'SHO-TB-SET', name: '2-pack', priceCents: 1299, currency: 'USD', stockQuantity: 40, isDefault: true },
    ],
  },
  {
    key: 'seed-product-4',
    name: 'Silk Sleep Mask',
    description: 'Soft silk sleep mask for travel and restful nights.',
    categorySlug: 'clothing',
    brand: PRODUCT_BRANDS[3],
    isFeatured: false,
    isNewArrival: false,
    imageUrl:
      'https://images.unsplash.com/photo-1641533444891-f1b645dd5bb6?auto=format&fit=crop&w=1000&q=80',
    variants: [
      { key: 'seed-product-4-variant-1', sku: 'SHO-MASK-01', name: 'Standard', priceCents: 1899, currency: 'USD', stockQuantity: 22, isDefault: true },
    ],
  },
  {
    key: 'seed-product-5',
    name: 'Ceramic Pour-Over Kit',
    description: 'Home barista pour-over kit with ceramic dripper and filters.',
    categorySlug: 'home-kitchen',
    brand: PRODUCT_BRANDS[4],
    isFeatured: true,
    isNewArrival: false,
    imageUrl:
      'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=1000&q=80',
    variants: [
      { key: 'seed-product-5-variant-1', sku: 'SHO-POUR-01', name: 'Kit', priceCents: 4599, currency: 'USD', stockQuantity: 12, isDefault: true },
    ],
  },
  {
    key: 'seed-product-6',
    name: 'Hydrating Face Serum',
    description: 'Lightweight hydrating face serum for daily personal care.',
    categorySlug: 'beauty',
    brand: PRODUCT_BRANDS[5],
    isFeatured: false,
    isNewArrival: true,
    imageUrl:
      'https://images.unsplash.com/photo-1571781926291-c477ebfd024b?auto=format&fit=crop&w=1000&q=80',
    variants: [
      { key: 'seed-product-6-variant-1', sku: 'SHO-SER-30', name: '30 ml', priceCents: 5299, currency: 'USD', stockQuantity: 18, isDefault: true },
    ],
  },
  {
    key: 'seed-product-7',
    name: 'Linen Table Runner',
    description: 'Natural linen table runner for everyday dining and gatherings.',
    categorySlug: 'home-kitchen',
    brand: PRODUCT_BRANDS[6],
    isFeatured: false,
    isNewArrival: false,
    imageUrl:
      'https://images.unsplash.com/photo-1616628182509-6f228f77f3f6?auto=format&fit=crop&w=1000&q=80',
    variants: [
      { key: 'seed-product-7-variant-1', sku: 'SHO-LIN-01', name: 'Standard', priceCents: 3199, currency: 'USD', stockQuantity: 15, isDefault: true },
    ],
  },
  {
    key: 'seed-product-8',
    name: 'Travel Wellness Gift Box',
    description: 'Curated travel wellness essentials in a gift-ready box.',
    categorySlug: 'beauty',
    brand: PRODUCT_BRANDS[7],
    isFeatured: true,
    isNewArrival: false,
    imageUrl:
      'https://images.unsplash.com/photo-1512909006721-3d6018887383?auto=format&fit=crop&w=1000&q=80',
    variants: [
      { key: 'seed-product-8-variant-1', sku: 'SHO-GIFT-TW', name: 'Box', priceCents: 6899, currency: 'USD', stockQuantity: 9, isDefault: true },
    ],
  },
  {
    key: 'seed-product-9',
    name: 'Compact Picnic Set',
    description: 'Compact picnic set for outdoor meals and weekend gifts.',
    categorySlug: 'sports-outdoors',
    brand: PRODUCT_BRANDS[8],
    isFeatured: false,
    isNewArrival: true,
    imageUrl:
      'https://images.unsplash.com/photo-1478145046317-39f10e56b5e9?auto=format&fit=crop&w=1000&q=80',
    variants: [
      { key: 'seed-product-9-variant-1', sku: 'SHO-PIC-01', name: 'Set', priceCents: 7999, currency: 'USD', stockQuantity: 7, isDefault: true },
    ],
  },
  {
    key: 'seed-product-10',
    name: 'Premium Scented Diffuser',
    description:
      'Premium diffuser with a refined scent profile for living spaces and offices.',
    categorySlug: 'home-kitchen',
    brand: PRODUCT_BRANDS[9],
    isFeatured: true,
    isNewArrival: false,
    imageUrl:
      'https://images.unsplash.com/photo-1601506521937-0121fc6b9ee9?auto=format&fit=crop&w=1000&q=80',
    variants: [
      { key: 'seed-product-10-variant-1', sku: 'SHO-DIF-XL', name: 'XL', priceCents: 9999, currency: 'USD', stockQuantity: 0, isDefault: true },
    ],
  },
  {
    key: 'seed-product-11',
    name: 'Deluxe Grooming Kit',
    description: 'Deluxe grooming kit with premium personal-care essentials.',
    categorySlug: 'beauty',
    brand: PRODUCT_BRANDS[10],
    isFeatured: false,
    isNewArrival: true,
    imageUrl:
      'https://images.unsplash.com/photo-1621607512214-68297480165e?auto=format&fit=crop&w=1000&q=80',
    variants: [
      { key: 'seed-product-11-variant-1', sku: 'SHO-GRM-DLX', name: 'Kit', priceCents: 11999, currency: 'USD', stockQuantity: 6, isDefault: true },
    ],
  },
  {
    key: 'seed-product-12',
    name: 'Signature Celebration Hamper',
    description: 'Signature celebration hamper packed with gift-friendly bestsellers.',
    categorySlug: 'home-kitchen',
    brand: PRODUCT_BRANDS[11],
    isFeatured: false,
    isNewArrival: false,
    imageUrl:
      'https://images.unsplash.com/photo-1549465220-1a8b9238cd48?auto=format&fit=crop&w=1000&q=80',
    variants: [
      { key: 'seed-product-12-variant-1', sku: 'SHO-HAMP-01', name: 'Hamper', priceCents: 14999, currency: 'USD', stockQuantity: 4, isDefault: true },
    ],
  },
];

/** US-005: ~50–100 demo SKUs across launch categories, brands, and stock states. */
const EXPANDED_CATALOG_NAMES: Array<{ categorySlug: string; names: string[] }> = [
  {
    categorySlug: 'clothing',
    names: [
      'Classic Cotton Tee',
      'Relaxed Fit Denim Jacket',
      'Merino Wool Sweater',
      'Everyday Chino Pants',
      'Lightweight Running Shorts',
      'Organic Cotton Hoodie',
      'Linen Button-Down Shirt',
      'Packable Rain Windbreaker',
      'High-Rise Leggings',
      'Weekend Flannel Shirt',
    ],
  },
  {
    categorySlug: 'electronics',
    names: [
      'Wireless Earbuds Pro',
      'USB-C Fast Charger 45W',
      'Portable Bluetooth Speaker',
      'Smart Watch Fitness Band',
      'Noise-Canceling Headphones',
      'Compact Power Bank 10K',
      'Mechanical Keyboard Mini',
      '4K Webcam Stream Kit',
      'Tablet Stand with Hub',
      'Smart Home Light Bulb 2-Pack',
    ],
  },
  {
    categorySlug: 'home-kitchen',
    names: [
      'Stainless Steel Mixing Bowls',
      'Nonstick Skillet 10 inch',
      'Glass Food Storage Set',
      'Bamboo Cutting Board Large',
      'Electric Kettle 1.7L',
      'Cast Iron Dutch Oven',
      'Microfiber Dish Towel 6-Pack',
      'Adjustable Measuring Cups',
      'Ceramic Dinner Plate Set',
      'Vacuum-Seal Container Kit',
    ],
  },
  {
    categorySlug: 'beauty',
    names: [
      'Daily SPF Moisturizer',
      'Gentle Gel Cleanser',
      'Hydrating Lip Balm Duo',
      'Volumizing Shampoo',
      'Restorative Hair Mask',
      'Aluminum-Free Deodorant',
      'Body Lotion Shea Blend',
      'Exfoliating Face Scrub',
      'Night Repair Cream',
      'Cedarwood Beard Oil',
    ],
  },
  {
    categorySlug: 'sports-outdoors',
    names: [
      'Insulated Water Bottle 32oz',
      'Trail Running Hydration Pack',
      'Camping Headlamp USB',
      'Foldable Camp Chair',
      'Yoga Mat 5mm Grip',
      'Resistance Band Set',
      'Trekking Poles Pair',
      'Cooler Backpack 24L',
      'Cycling Gloves Gel Pad',
      'Quick-Dry Hiking Socks 3-Pack',
    ],
  },
];

function stockQuantityForDemoIndex(index: number): number {
  if (index % 11 === 0) {
    return 0;
  }
  if (index % 6 === 0) {
    return 3;
  }
  return 12 + (index % 9);
}

function buildExpandedCatalog(baseProducts: SeedProduct[]): SeedProduct[] {
  const products: SeedProduct[] = [...baseProducts];
  let index = baseProducts.length + 1;

  for (const group of EXPANDED_CATALOG_NAMES) {
    for (const name of group.names) {
      const brand = PRODUCT_BRANDS[(index - 1) % PRODUCT_BRANDS.length]!;
      const imageUrl = DEMO_IMAGE_URLS[index % DEMO_IMAGE_URLS.length]!;
      const priceBase = 899 + (index % 17) * 350;
      const stockQuantity = stockQuantityForDemoIndex(index);
      const variants: SeedProduct['variants'] = [
        {
          key: `seed-product-${index}-variant-1`,
          sku: `SHO-${String(index).padStart(3, '0')}-STD`,
          name: 'Standard',
          priceCents: priceBase,
          currency: 'USD',
          stockQuantity,
          isDefault: true,
        },
      ];
      if (index % 4 === 0) {
        variants.push({
          key: `seed-product-${index}-variant-2`,
          sku: `SHO-${String(index).padStart(3, '0')}-ALT`,
          name: 'Alternate',
          priceCents: priceBase + 400,
          currency: 'USD',
          stockQuantity: stockQuantityForDemoIndex(index + 100),
        });
      }

      products.push({
        key: `seed-product-${index}`,
        name,
        description: `${name} for demo search, filter, and merchandising scenarios.`,
        categorySlug: group.categorySlug,
        brand,
        isFeatured: index % 9 === 0,
        isNewArrival: index % 7 === 0,
        imageUrl,
        variants,
      });
      index += 1;
    }
  }

  return products;
}

const PRODUCTS = buildExpandedCatalog(CORE_PRODUCTS);

async function resetDatabase(): Promise<void> {
  await prisma.supportMessage.deleteMany();
  await prisma.payment.deleteMany();
  await prisma.orderItem.deleteMany();
  await prisma.order.deleteMany();
  await prisma.couponExclusion.deleteMany();
  await prisma.coupon.deleteMany();
  await prisma.wishlistItem.deleteMany();
  await prisma.wishlist.deleteMany();
  await prisma.cartItem.deleteMany();
  await prisma.cart.deleteMany();
  await prisma.passwordResetToken.deleteMany();
  await prisma.refreshToken.deleteMany();
  await prisma.address.deleteMany();
  await prisma.user.deleteMany();
  await prisma.homeBanner.deleteMany();
  await prisma.productVariant.deleteMany();
  await prisma.product.deleteMany();
  await prisma.category.deleteMany();
}

async function seedCatalog(): Promise<Map<string, string>> {
  const categoryIds = new Map<string, string>();
  for (const category of CATEGORIES) {
    const created = await prisma.category.create({
      data: {
        id: seedUuid(`category:${category.slug}`),
        slug: category.slug,
        name: category.name,
        sortOrder: category.sortOrder,
      },
    });
    categoryIds.set(category.slug, created.id);
  }

  for (const product of PRODUCTS) {
    const categoryId = categoryIds.get(product.categorySlug);
    if (!categoryId) {
      throw new Error(`Missing category for slug ${product.categorySlug}`);
    }

    await prisma.product.create({
      data: {
        id: seedUuid(product.key),
        name: product.name,
        slug: slugify(product.name),
        brand: product.brand,
        description: product.description,
        primaryImageUrl: product.imageUrl,
        isFeatured: product.isFeatured,
        isNewArrival: product.isNewArrival,
        categoryId,
        variants: {
          create: product.variants.map((variant) => ({
            id: seedUuid(variant.key),
            sku: variant.sku,
            name: variant.name,
            priceCents: variant.priceCents,
            currency: variant.currency,
            stockQuantity: variant.stockQuantity,
            imageUrl: product.imageUrl,
            isDefault: variant.isDefault ?? false,
          })),
        },
      },
    });
  }

  return categoryIds;
}

async function seedStoreConfigAndMerchandising(): Promise<void> {
  await prisma.storeConfig.upsert({
    where: { id: 1 },
    create: {
      id: 1,
      currency: 'USD',
      freeShippingThresholdCents: 7500,
      flatShippingCents: 599,
      taxRateBps: 800,
      lowStockThreshold: 5,
      supportEmail: 'support@shopease-demo.com',
    },
    update: {
      freeShippingThresholdCents: 7500,
      flatShippingCents: 599,
      taxRateBps: 800,
      lowStockThreshold: 5,
      supportEmail: 'support@shopease-demo.com',
    },
  });

  const banners = [
    {
      key: 'banner-spring-home',
      title: 'Refresh your space',
      subtitle: 'Kitchen and home picks with free shipping over $75',
      imageUrl:
        'https://images.unsplash.com/photo-1616628182509-6f228f77f3f6?auto=format&fit=crop&w=1200&q=80',
      ctaLabel: 'Shop home',
      categorySlug: 'home-kitchen',
      sortOrder: 0,
    },
    {
      key: 'banner-gift-season',
      title: 'New season styles',
      subtitle: 'Fresh clothing arrivals for every day',
      imageUrl:
        'https://images.unsplash.com/photo-1512909006721-3d6018887383?auto=format&fit=crop&w=1200&q=80',
      ctaLabel: 'Shop clothing',
      categorySlug: 'clothing',
      sortOrder: 1,
    },
    {
      key: 'banner-self-care',
      title: 'Beauty essentials',
      subtitle: 'Skincare and grooming ships in 2–3 days',
      imageUrl:
        'https://images.unsplash.com/photo-1571781926291-c477ebfd024b?auto=format&fit=crop&w=1200&q=80',
      ctaLabel: 'Shop beauty',
      categorySlug: 'beauty',
      sortOrder: 2,
    },
  ];

  for (const banner of banners) {
    await prisma.homeBanner.create({
      data: {
        id: seedUuid(banner.key),
        title: banner.title,
        subtitle: banner.subtitle,
        imageUrl: banner.imageUrl,
        ctaLabel: banner.ctaLabel,
        categorySlug: banner.categorySlug,
        sortOrder: banner.sortOrder,
        isActive: true,
      },
    });
  }
}

async function seedCoupons(categoryIds: Map<string, string>): Promise<void> {
  const welcomeId = seedUuid('coupon:welcome10');
  const save500Id = seedUuid('coupon:save500');
  const giftExclId = seedUuid('coupon:giftexcl');

  await prisma.coupon.createMany({
    data: [
      {
        id: welcomeId,
        code: 'WELCOME10',
        type: CouponType.PERCENT,
        percentOff: 10,
        minSubtotalCents: 2500,
        expiresAt: new Date('2027-12-31T23:59:59.000Z'),
        isActive: true,
      },
      {
        id: save500Id,
        code: 'SAVE500',
        type: CouponType.FIXED_AMOUNT,
        amountOffCents: 500,
        minSubtotalCents: 5000,
        expiresAt: new Date('2027-06-30T23:59:59.000Z'),
        isActive: true,
      },
      {
        id: giftExclId,
        code: 'GIFTEXCL15',
        type: CouponType.PERCENT,
        percentOff: 15,
        minSubtotalCents: 3000,
        expiresAt: new Date('2027-09-30T23:59:59.000Z'),
        isActive: true,
      },
    ],
  });

  const electronicsCategoryId = categoryIds.get('electronics');
  if (electronicsCategoryId) {
    await prisma.couponExclusion.create({
      data: {
        id: seedUuid('coupon-excl:electronics-category'),
        couponId: giftExclId,
        kind: CouponExclusionKind.CATEGORY,
        categoryId: electronicsCategoryId,
      },
    });
  }

  await prisma.couponExclusion.create({
    data: {
      id: seedUuid('coupon-excl:hamper-product'),
      couponId: save500Id,
      kind: CouponExclusionKind.PRODUCT,
      productId: seedUuid('seed-product-12'),
    },
  });
}

async function seedDemoOrders(): Promise<void> {
  const demoUserId = seedUuid('user:demo-shopper');
  const demoPasswordHash = await bcrypt.hash('DemoPass123!', 12);
  const addressId = seedUuid('address:demo-home');
  const shippedOrderId = seedUuid('order:demo-shipped');
  const deliveredOrderId = seedUuid('order:demo-delivered');
  const soapVariantId = seedUuid('seed-product-1-variant-1');

  await prisma.user.create({
    data: {
      id: demoUserId,
      email: 'demo@shopease.test',
      passwordHash: demoPasswordHash,
      displayName: 'Demo Shopper',
    },
  });

  await prisma.address.create({
    data: {
      id: addressId,
      userId: demoUserId,
      fullName: 'Demo Shopper',
      line1: '123 Market Street',
      city: 'Austin',
      region: 'TX',
      postalCode: '78701',
      country: 'US',
      isDefault: true,
    },
  });

  const shippingSnapshot = {
    fullName: 'Demo Shopper',
    line1: '123 Market Street',
    city: 'Austin',
    region: 'TX',
    postalCode: '78701',
    country: 'US',
  };

  await prisma.order.create({
    data: {
      id: shippedOrderId,
      userId: demoUserId,
      orderNumber: 'SE-20261004-SHIP01',
      status: OrderStatus.fulfilled,
      subtotalCents: 799,
      discountCents: 0,
      shippingCents: 599,
      taxCents: 64,
      totalCents: 1462,
      shippingAddressSnapshot: shippingSnapshot,
      carrierName: 'UPS',
      trackingNumber: '1Z999AA10123456784',
      paidAt: new Date('2026-10-01T14:00:00.000Z'),
      fulfilledAt: new Date('2026-10-02T09:00:00.000Z'),
      items: {
        create: [
          {
            id: seedUuid('order-item:shipped-soap'),
            variantId: soapVariantId,
            productName: 'Citrus Hand Soap',
            variantName: '300 ml',
            sku: 'SHO-SOAP-300',
            quantity: 1,
            unitPriceCents: 799,
            currency: 'USD',
            lineTotalCents: 799,
          },
        ],
      },
      payment: {
        create: {
          id: seedUuid('payment:shipped'),
          provider: PaymentProvider.MOCK,
          status: PaymentStatus.succeeded,
          amountCents: 1462,
          currency: 'USD',
          mockReference: 'MOCK-SHIP-001',
        },
      },
    },
  });

  await prisma.order.create({
    data: {
      id: deliveredOrderId,
      userId: demoUserId,
      orderNumber: 'SE-20261004-DEL01',
      status: OrderStatus.delivered,
      subtotalCents: 2499,
      discountCents: 0,
      shippingCents: 0,
      taxCents: 200,
      totalCents: 2699,
      shippingAddressSnapshot: shippingSnapshot,
      carrierName: 'FedEx',
      trackingNumber: '7946 1234 5678',
      paidAt: new Date('2026-09-20T11:00:00.000Z'),
      fulfilledAt: new Date('2026-09-21T08:00:00.000Z'),
      deliveredAt: new Date('2026-09-23T16:30:00.000Z'),
      items: {
        create: [
          {
            id: seedUuid('order-item:delivered-candle'),
            variantId: seedUuid('seed-product-2-variant-1'),
            productName: 'Aroma Candle',
            variantName: 'Standard',
            sku: 'SHO-CAN-01',
            quantity: 1,
            unitPriceCents: 2499,
            currency: 'USD',
            lineTotalCents: 2499,
          },
        ],
      },
      payment: {
        create: {
          id: seedUuid('payment:delivered'),
          provider: PaymentProvider.MOCK,
          status: PaymentStatus.succeeded,
          amountCents: 2699,
          currency: 'USD',
          mockReference: 'MOCK-DEL-001',
        },
      },
    },
  });
}

async function main(): Promise<void> {
  await resetDatabase();
  const categoryIds = await seedCatalog();
  await seedStoreConfigAndMerchandising();
  await seedCoupons(categoryIds);
  await seedDemoOrders();

  const variantCount = PRODUCTS.reduce((sum, product) => sum + product.variants.length, 0);
  console.log(
    `Seeded M3 catalog (${PRODUCTS.length} products, ${variantCount} SKUs), store config, coupons, banners, and demo fulfillment orders.`,
  );
}

main()
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
