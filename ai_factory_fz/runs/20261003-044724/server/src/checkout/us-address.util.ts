/** US contiguous states (excludes AK, HI) acceptable for Release 2 demo shipping. */
export const US_CONTIGUOUS_STATE_CODES = new Set([
  'AL',
  'AZ',
  'AR',
  'CA',
  'CO',
  'CT',
  'DE',
  'FL',
  'GA',
  'ID',
  'IL',
  'IN',
  'IA',
  'KS',
  'KY',
  'LA',
  'ME',
  'MD',
  'MA',
  'MI',
  'MN',
  'MS',
  'MO',
  'MT',
  'NE',
  'NV',
  'NH',
  'NJ',
  'NM',
  'NY',
  'NC',
  'ND',
  'OH',
  'OK',
  'OR',
  'PA',
  'RI',
  'SC',
  'SD',
  'TN',
  'TX',
  'UT',
  'VT',
  'VA',
  'WA',
  'WV',
  'WI',
  'WY',
  'DC',
]);

export type ShippingAddressInput = {
  fullName: string;
  email?: string;
  phone?: string;
  line1: string;
  line2?: string;
  city: string;
  region: string;
  postalCode: string;
  country: string;
};

export function validateUsShippingAddress(address: ShippingAddressInput): string | null {
  if (address.country !== 'US') {
    return 'Shipping is limited to the United States';
  }
  if (address.fullName.trim().length === 0) {
    return 'Full name is required';
  }
  if (address.line1.trim().length === 0) {
    return 'Address line 1 is required';
  }
  if (address.city.trim().length === 0) {
    return 'City is required';
  }
  const region = address.region.trim().toUpperCase();
  if (!US_CONTIGUOUS_STATE_CODES.has(region)) {
    return 'State must be a valid US contiguous state code';
  }
  const postal = address.postalCode.trim();
  if (!/^\d{5}(-\d{4})?$/.test(postal)) {
    return 'Postal code must be a valid US ZIP code';
  }
  return null;
}
