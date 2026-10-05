import { assertMainlandUkAddress, isMainlandUkPostcode, normalizeUkPostcode } from './uk-address.validation';
import { UkAddressInputDto } from './dto/uk-address-input.dto';

const baseAddress = (): UkAddressInputDto => ({
  fullName: 'Alex Smith',
  line1: '10 High Street',
  city: 'London',
  postalCode: 'SW1A 1AA',
  country: 'GB',
});

describe('uk-address.validation', () => {
  it('normalizes UK postcodes', () => {
    expect(normalizeUkPostcode('sw1a1aa')).toBe('SW1A 1AA');
    expect(normalizeUkPostcode('  ec2a  4ne ')).toBe('EC2A 4NE');
  });

  it('accepts mainland UK addresses', () => {
    const snapshot = assertMainlandUkAddress(baseAddress());
    expect(snapshot.postalCode).toBe('SW1A 1AA');
    expect(snapshot.country).toBe('GB');
  });

  it('rejects non-mainland outward codes', () => {
    expect(isMainlandUkPostcode('BT1 1AA')).toBe(false);
    expect(isMainlandUkPostcode('JE2 3AB')).toBe(false);
    expect(isMainlandUkPostcode('GY1 1AA')).toBe(false);
    expect(isMainlandUkPostcode('IM1 1AA')).toBe(false);
  });

  it('throws for invalid postcodes', () => {
    expect(() =>
      assertMainlandUkAddress({ ...baseAddress(), postalCode: 'INVALID' }),
    ).toThrow();
    expect(() =>
      assertMainlandUkAddress({ ...baseAddress(), postalCode: 'BT1 1AA' }),
    ).toThrow();
  });
});
