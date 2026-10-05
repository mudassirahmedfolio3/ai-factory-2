import { INVALID_UK_ADDRESS_MESSAGE } from './checkout.constants';
import { UkAddressInputDto } from './dto/uk-address-input.dto';

const UK_POSTCODE_PATTERN =
  /^([A-Z]{1,2}\d[A-Z\d]?|[A-Z]{1,2}\d{2}|[A-Z]{1,2}\d[A-Z\d]?)\s*\d[A-Z]{2}$/i;

const NON_MAINLAND_OUTWARD_PREFIXES = ['BT', 'JE', 'GY', 'IM', 'BFPO'] as const;

export type UkAddressSnapshot = {
  fullName: string;
  line1: string;
  line2?: string;
  city: string;
  region?: string;
  postalCode: string;
  country: 'GB';
};

export function normalizeUkPostcode(postalCode: string): string {
  const compact = postalCode.trim().toUpperCase().replace(/\s+/g, '');
  if (compact.length <= 3) {
    return compact;
  }
  return `${compact.slice(0, -3)} ${compact.slice(-3)}`;
}

export function isValidUkPostcodeFormat(postalCode: string): boolean {
  const normalized = normalizeUkPostcode(postalCode);
  return UK_POSTCODE_PATTERN.test(normalized);
}

function outwardCode(postalCode: string): string {
  const compact = normalizeUkPostcode(postalCode).replace(/\s/g, '');
  if (compact.length <= 3) {
    return compact;
  }
  return compact.slice(0, -3);
}

export function isMainlandUkPostcode(postalCode: string): boolean {
  const outward = outwardCode(postalCode).toUpperCase();
  return !NON_MAINLAND_OUTWARD_PREFIXES.some((prefix) => outward.startsWith(prefix));
}

export function assertMainlandUkAddress(address: UkAddressInputDto): UkAddressSnapshot {
  if (address.country !== 'GB') {
    throw new Error(INVALID_UK_ADDRESS_MESSAGE);
  }

  if (!isValidUkPostcodeFormat(address.postalCode) || !isMainlandUkPostcode(address.postalCode)) {
    throw new Error(INVALID_UK_ADDRESS_MESSAGE);
  }

  const snapshot: UkAddressSnapshot = {
    fullName: address.fullName.trim(),
    line1: address.line1.trim(),
    city: address.city.trim(),
    postalCode: normalizeUkPostcode(address.postalCode),
    country: 'GB',
  };

  if (address.line2?.trim()) {
    snapshot.line2 = address.line2.trim();
  }
  if (address.region?.trim()) {
    snapshot.region = address.region.trim();
  }

  return snapshot;
}
