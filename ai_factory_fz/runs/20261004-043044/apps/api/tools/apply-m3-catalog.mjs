import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../..');
const catalogPath = path.join(repoRoot, 'apps/api/prisma/data/catalog.json');
const manifestPath = path.join(
  repoRoot,
  'apps/api/prisma/data/catalog-image-manifest.json',
);
const flutterCatalogPath = path.join(repoRoot, 'app/assets/data/catalog.json');

const catalog = JSON.parse(fs.readFileSync(catalogPath, 'utf8'));
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));

const imageBySlug = new Map(
  manifest.images
    .filter((i) => i.productSlug)
    .map((i) => [
      i.productSlug,
      `assets/catalog/images/${i.filename}`,
    ]),
);

function imageForSlug(slug) {
  return imageBySlug.get(slug) ?? 'assets/images/products/placeholder.png';
}

for (const product of catalog.products) {
  const img = imageForSlug(product.slug);
  product.primaryImageUrl = img;
  for (const variant of product.variants) {
    variant.imageUrl = img;
  }
  for (const image of product.images) {
    image.url = img;
  }
}

for (const category of catalog.categories) {
  if (category.imageUrl?.includes('placeholder')) {
    category.imageUrl = 'assets/catalog/images/modern-led-ceiling-light.jpg';
  }
}

if (catalog.homeBanners) {
  catalog.homeBanners[0].imageUrl =
    'assets/catalog/images/winter-sale-banner.jpg';
  catalog.homeBanners[1].imageUrl =
    'assets/catalog/images/outdoor-security-banner.jpg';
}

const newProducts = [
  {
    id: 'p1111111-1111-4111-8111-111111111117',
    name: 'Industrial IP65 Bulkhead',
    brand: 'Voltara',
    brandSlug: 'voltara',
    slug: 'industrial-bulkhead-light',
    description:
      'Robust IP65 bulkhead for garages, plant rooms, and service corridors.',
    categoryId: 'c1111111-1111-4111-8111-111111111103',
    primaryImageUrl: imageForSlug('industrial-bulkhead-light'),
    variants: [
      {
        id: 'v1111111-1111-4111-8111-111111111117',
        sku: 'OS-4003-GY',
        label: 'Grey / 4000K / 18W',
        price: { amountCents: 4299, currency: 'GBP' },
        compareAtPrice: null,
        stockQuantity: 28,
        availableQuantity: 28,
        finish: 'Grey',
        wattageW: 18,
        colorTemperatureK: 4000,
        imageUrl: imageForSlug('industrial-bulkhead-light'),
        isDefault: true,
      },
    ],
    images: [
      {
        url: imageForSlug('industrial-bulkhead-light'),
        sortOrder: 0,
        altText: 'Industrial bulkhead light',
      },
    ],
    specs: {
      wattageW: 18,
      lumens: 1800,
      colorTemperatureK: 4000,
      lightType: 'LED',
      voltage: '220-240V',
      dimmable: false,
      material: 'Polycarbonate',
      finish: 'Grey',
      dimensionsMm: '280 mm diameter',
      ipRating: 'IP65',
      bulbIncluded: true,
      installationType: 'Surface mount',
    },
    reviews: [
      {
        id: 'r1111111-1111-4111-8111-111111111117',
        rating: 4,
        title: 'Solid for the garage',
        body: 'Bright and easy to wire. Good seal against damp.',
        authorDisplayName: 'Verified Buyer',
        createdAt: '2025-11-05T00:00:00.000Z',
      },
    ],
    popularityRank: 12,
    unitsSold90Days: 95,
    isFeatured: false,
    keywords: ['bulkhead', 'garage', 'ip65'],
    createdAt: '2025-11-01T00:00:00.000Z',
  },
  {
    id: 'p1111111-1111-4111-8111-111111111118',
    name: 'Minimalist 3-Spot Track Kit',
    brand: 'Luminex',
    brandSlug: 'luminex',
    slug: 'minimalist-track-spot-3',
    description: 'Three-spot track kit for kitchens and retail displays.',
    categoryId: 'c1111111-1111-4111-8111-111111111101',
    primaryImageUrl: imageForSlug('minimalist-track-spot-3'),
    variants: [
      {
        id: 'v1111111-1111-4111-8111-111111111118',
        sku: 'CL-1003-BK',
        label: 'Matte Black / 3000K / 3x7W',
        price: { amountCents: 7499, currency: 'GBP' },
        compareAtPrice: { amountCents: 8499, currency: 'GBP' },
        stockQuantity: 16,
        availableQuantity: 16,
        finish: 'Matte Black',
        wattageW: 21,
        colorTemperatureK: 3000,
        imageUrl: imageForSlug('minimalist-track-spot-3'),
        isDefault: true,
      },
    ],
    images: [
      {
        url: imageForSlug('minimalist-track-spot-3'),
        sortOrder: 0,
        altText: 'Track lighting kit',
      },
    ],
    specs: {
      wattageW: 21,
      lumens: 2100,
      colorTemperatureK: 3000,
      lightType: 'LED',
      voltage: '220-240V',
      dimmable: true,
      material: 'Aluminium',
      finish: 'Matte Black',
      dimensionsMm: '1000 mm track',
      ipRating: 'IP20',
      bulbIncluded: true,
      installationType: 'Ceiling mounted',
    },
    reviews: [],
    popularityRank: 8,
    unitsSold90Days: 140,
    isFeatured: false,
    keywords: ['track', 'spot', 'kitchen'],
    createdAt: '2025-11-10T00:00:00.000Z',
  },
  {
    id: 'p1111111-1111-4111-8111-111111111119',
    name: 'Glass Globe Pendant',
    brand: 'BrightHive',
    brandSlug: 'brighthive',
    slug: 'glass-globe-pendant',
    description: 'Smoked glass globe pendant for hallways and bedrooms.',
    categoryId: 'c1111111-1111-4111-8111-111111111108',
    primaryImageUrl: imageForSlug('glass-globe-pendant'),
    variants: [
      {
        id: 'v1111111-1111-4111-8111-111111111119',
        sku: 'PD-2202-SM',
        label: 'Smoked glass / 2700K / 12W',
        price: { amountCents: 6499, currency: 'GBP' },
        compareAtPrice: null,
        stockQuantity: 22,
        availableQuantity: 22,
        finish: 'Smoked glass',
        wattageW: 12,
        colorTemperatureK: 2700,
        imageUrl: imageForSlug('glass-globe-pendant'),
        isDefault: true,
      },
    ],
    images: [
      {
        url: imageForSlug('glass-globe-pendant'),
        sortOrder: 0,
        altText: 'Glass globe pendant',
      },
    ],
    specs: {
      wattageW: 12,
      lumens: 1100,
      colorTemperatureK: 2700,
      lightType: 'LED',
      voltage: '220-240V',
      dimmable: true,
      material: 'Glass and steel',
      finish: 'Smoked glass',
      dimensionsMm: '250 mm globe',
      ipRating: 'IP20',
      bulbIncluded: true,
      installationType: 'Pendant',
    },
    reviews: [],
    popularityRank: 15,
    unitsSold90Days: 88,
    isFeatured: false,
    keywords: ['pendant', 'bedroom'],
    createdAt: '2025-11-15T00:00:00.000Z',
  },
  {
    id: 'p1111111-1111-4111-8111-111111111120',
    name: 'Up/Down Outdoor Wall Light',
    brand: 'NordLux',
    brandSlug: 'nordlux',
    slug: 'updown-outdoor-wall-light',
    description: 'Dual-beam wall lantern for porches and patio doors.',
    categoryId: 'c1111111-1111-4111-8111-111111111103',
    primaryImageUrl: imageForSlug('updown-outdoor-wall-light'),
    variants: [
      {
        id: 'v1111111-1111-4111-8111-111111111120',
        sku: 'OS-4004-AN',
        label: 'Anthracite / 3000K / 2x5W',
        price: { amountCents: 5599, currency: 'GBP' },
        compareAtPrice: null,
        stockQuantity: 19,
        availableQuantity: 19,
        finish: 'Anthracite',
        wattageW: 10,
        colorTemperatureK: 3000,
        imageUrl: imageForSlug('updown-outdoor-wall-light'),
        isDefault: true,
      },
    ],
    images: [
      {
        url: imageForSlug('updown-outdoor-wall-light'),
        sortOrder: 0,
        altText: 'Outdoor up down wall light',
      },
    ],
    specs: {
      wattageW: 10,
      lumens: 900,
      colorTemperatureK: 3000,
      lightType: 'LED',
      voltage: '220-240V',
      dimmable: false,
      material: 'Aluminium',
      finish: 'Anthracite',
      dimensionsMm: '120x160 mm',
      ipRating: 'IP44',
      bulbIncluded: true,
      installationType: 'Wall mounted',
    },
    reviews: [],
    popularityRank: 11,
    unitsSold90Days: 102,
    isFeatured: false,
    keywords: ['porch', 'outdoor', 'wall'],
    createdAt: '2025-11-18T00:00:00.000Z',
  },
  {
    id: 'p1111111-1111-4111-8111-111111111121',
    name: 'MR16 LED Bulb 6-Pack',
    brand: 'GlowCraft',
    brandSlug: 'glowcraft',
    slug: 'mr16-led-bulb-6-pack',
    description: 'Energy-saving MR16 lamps for downlight retrofits.',
    categoryId: 'c1111111-1111-4111-8111-111111111104',
    primaryImageUrl: imageForSlug('mr16-led-bulb-6-pack'),
    variants: [
      {
        id: 'v1111111-1111-4111-8111-111111111121',
        sku: 'BT-5003-WW',
        label: 'Warm white 2700K / 5W (x6)',
        price: { amountCents: 1899, currency: 'GBP' },
        compareAtPrice: null,
        stockQuantity: 120,
        availableQuantity: 120,
        finish: null,
        wattageW: 5,
        colorTemperatureK: 2700,
        imageUrl: imageForSlug('mr16-led-bulb-6-pack'),
        isDefault: true,
      },
    ],
    images: [
      {
        url: imageForSlug('mr16-led-bulb-6-pack'),
        sortOrder: 0,
        altText: 'MR16 LED bulbs',
      },
    ],
    specs: {
      wattageW: 5,
      lumens: 450,
      colorTemperatureK: 2700,
      lightType: 'LED',
      voltage: '12V AC/DC',
      dimmable: true,
      material: 'Plastic',
      finish: null,
      dimensionsMm: '50 mm diameter',
      ipRating: 'IP20',
      bulbIncluded: true,
      installationType: 'Retrofit',
    },
    reviews: [],
    popularityRank: 6,
    unitsSold90Days: 310,
    isFeatured: false,
    keywords: ['mr16', 'bulb', 'downlight'],
    createdAt: '2025-11-22T00:00:00.000Z',
  },
  {
    id: 'p1111111-1111-4111-8111-111111111122',
    name: 'Smart Wi-Fi Ceiling Fan Light',
    brand: 'Luminex',
    brandSlug: 'luminex',
    slug: 'smart-wifi-ceiling-fan-light',
    description: 'App-controlled fan light with dimmable LED module.',
    categoryId: 'c1111111-1111-4111-8111-111111111101',
    primaryImageUrl: imageForSlug('smart-wifi-ceiling-fan-light'),
    variants: [
      {
        id: 'v1111111-1111-4111-8111-111111111122',
        sku: 'CL-1004-WF',
        label: 'White / 3000K / 18W + fan',
        price: { amountCents: 12999, currency: 'GBP' },
        compareAtPrice: { amountCents: 14999, currency: 'GBP' },
        stockQuantity: 8,
        availableQuantity: 8,
        finish: 'White',
        wattageW: 18,
        colorTemperatureK: 3000,
        imageUrl: imageForSlug('smart-wifi-ceiling-fan-light'),
        isDefault: true,
      },
    ],
    images: [
      {
        url: imageForSlug('smart-wifi-ceiling-fan-light'),
        sortOrder: 0,
        altText: 'Smart ceiling fan light',
      },
    ],
    specs: {
      wattageW: 18,
      lumens: 1600,
      colorTemperatureK: 3000,
      lightType: 'LED',
      voltage: '220-240V',
      dimmable: true,
      material: 'Steel',
      finish: 'White',
      dimensionsMm: '1060 mm blade span',
      ipRating: 'IP20',
      bulbIncluded: true,
      installationType: 'Ceiling mounted',
    },
    reviews: [],
    popularityRank: 3,
    unitsSold90Days: 65,
    isFeatured: true,
    keywords: ['smart', 'wifi', 'fan'],
    createdAt: '2025-12-01T00:00:00.000Z',
  },
  {
    id: 'p1111111-1111-4111-8111-111111111123',
    name: 'Rechargeable Camping Lantern',
    brand: 'GlowCraft',
    brandSlug: 'glowcraft',
    slug: 'rechargeable-camping-lantern',
    description: 'USB-C rechargeable lantern with warm and cool modes.',
    categoryId: 'c1111111-1111-4111-8111-111111111106',
    primaryImageUrl: imageForSlug('rechargeable-camping-lantern'),
    variants: [
      {
        id: 'v1111111-1111-4111-8111-111111111123',
        sku: 'LP-7003-RC',
        label: 'Soft white / 5W',
        price: { amountCents: 2799, currency: 'GBP' },
        compareAtPrice: null,
        stockQuantity: 40,
        availableQuantity: 40,
        finish: 'Forest green',
        wattageW: 5,
        colorTemperatureK: 3000,
        imageUrl: imageForSlug('rechargeable-camping-lantern'),
        isDefault: true,
      },
    ],
    images: [
      {
        url: imageForSlug('rechargeable-camping-lantern'),
        sortOrder: 0,
        altText: 'Rechargeable camping lantern',
      },
    ],
    specs: {
      wattageW: 5,
      lumens: 500,
      colorTemperatureK: 3000,
      lightType: 'LED',
      voltage: 'USB-C 5V',
      dimmable: true,
      material: 'ABS',
      finish: 'Forest green',
      dimensionsMm: '180 mm height',
      ipRating: 'IP54',
      bulbIncluded: true,
      installationType: 'Portable',
    },
    reviews: [],
    popularityRank: null,
    unitsSold90Days: 55,
    isFeatured: false,
    keywords: ['camping', 'portable'],
    createdAt: '2025-12-05T00:00:00.000Z',
  },
  {
    id: 'p1111111-1111-4111-8111-111111111124',
    name: 'DALI Dimmable Panel Kit',
    brand: 'Voltara',
    brandSlug: 'voltara',
    slug: 'dali-dimmable-panel-kit',
    description: '600x600 DALI panel for commercial office refits.',
    categoryId: 'c1111111-1111-4111-8111-111111111107',
    primaryImageUrl: imageForSlug('dali-dimmable-panel-kit'),
    variants: [
      {
        id: 'v1111111-1111-4111-8111-111111111124',
        sku: 'CT-8004-DALI',
        label: '4000K / 36W / DALI',
        price: { amountCents: 8999, currency: 'GBP' },
        compareAtPrice: null,
        stockQuantity: 25,
        availableQuantity: 25,
        finish: 'White frame',
        wattageW: 36,
        colorTemperatureK: 4000,
        imageUrl: imageForSlug('dali-dimmable-panel-kit'),
        isDefault: true,
      },
      {
        id: 'v1111111-1111-4111-8111-111111111125',
        sku: 'CT-8004-DALI-DRIVER',
        label: 'DALI driver add-on',
        price: { amountCents: 3499, currency: 'GBP' },
        compareAtPrice: null,
        stockQuantity: 15,
        availableQuantity: 15,
        finish: null,
        wattageW: null,
        colorTemperatureK: null,
        imageUrl: imageForSlug('dali-dimmable-panel-kit'),
        isDefault: false,
      },
    ],
    images: [
      {
        url: imageForSlug('dali-dimmable-panel-kit'),
        sortOrder: 0,
        altText: 'DALI panel light',
      },
    ],
    specs: {
      wattageW: 36,
      lumens: 3600,
      colorTemperatureK: 4000,
      lightType: 'LED',
      voltage: '220-240V',
      dimmable: true,
      material: 'Aluminium',
      finish: 'White frame',
      dimensionsMm: '600x600 mm',
      ipRating: 'IP40',
      bulbIncluded: true,
      installationType: 'Recessed grid',
    },
    reviews: [],
    popularityRank: 9,
    unitsSold90Days: 72,
    isFeatured: false,
    keywords: ['dali', 'office', 'panel'],
    createdAt: '2025-12-10T00:00:00.000Z',
  },
];

const existingSlugs = new Set(catalog.products.map((p) => p.slug));
for (const product of newProducts) {
  if (!existingSlugs.has(product.slug)) {
    catalog.products.push(product);
  }
}

catalog.coupons = [
  {
    id: 'cp111111-1111-4111-8111-111111111101',
    code: 'CEILING10',
    description: '10% off ceiling lighting',
    percentOff: 10,
    amountOffCents: null,
    currency: 'GBP',
    minSubtotalCents: 5000,
    expiresAt: '2026-12-31T23:59:59.000Z',
    singleUsePerEmail: false,
    excludeSaleItems: true,
    isActive: true,
    categorySlugs: ['ceiling-lights', 'pendant-lights'],
    productSlugs: [],
  },
  {
    id: 'cp111111-1111-4111-8111-111111111102',
    code: 'OUTDOOR15',
    description: '15% off outdoor and security',
    percentOff: 15,
    amountOffCents: null,
    currency: 'GBP',
    minSubtotalCents: 4000,
    expiresAt: '2026-12-31T23:59:59.000Z',
    singleUsePerEmail: false,
    excludeSaleItems: true,
    isActive: true,
    categorySlugs: ['outdoor-security'],
    productSlugs: [],
  },
  {
    id: 'cp111111-1111-4111-8111-111111111103',
    code: 'BULB5',
    description: '£5 off GU10 5-pack',
    percentOff: null,
    amountOffCents: 500,
    currency: 'GBP',
    minSubtotalCents: 1500,
    expiresAt: '2026-12-31T23:59:59.000Z',
    singleUsePerEmail: true,
    excludeSaleItems: false,
    isActive: true,
    categorySlugs: [],
    productSlugs: ['gu10-led-bulb-5-pack'],
  },
];

const json = `${JSON.stringify(catalog, null, 2)}\n`;
fs.writeFileSync(catalogPath, json);
fs.writeFileSync(flutterCatalogPath, json);

const variantCount = catalog.products.reduce(
  (n, p) => n + p.variants.length,
  0,
);
console.log(
  'products',
  catalog.products.length,
  'variants',
  variantCount,
  'featured',
  catalog.products.filter((p) => p.isFeatured).length,
);
