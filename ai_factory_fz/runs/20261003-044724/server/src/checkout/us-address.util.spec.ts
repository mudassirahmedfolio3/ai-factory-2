import { describe, expect, it } from 'vitest';
import { validateUsShippingAddress } from './us-address.util.js';

describe('validateUsShippingAddress', () => {
  const valid = {
    fullName: 'Jane Doe',
    line1: '123 Main St',
    city: 'Austin',
    region: 'TX',
    postalCode: '78701',
    country: 'US',
  };

  it('accepts contiguous US address', () => {
    expect(validateUsShippingAddress(valid)).toBeNull();
  });

  it('rejects non-US country', () => {
    expect(
      validateUsShippingAddress({ ...valid, country: 'CA' }),
    ).not.toBeNull();
  });

  it('rejects Alaska for demo contiguous rule', () => {
    expect(
      validateUsShippingAddress({ ...valid, region: 'AK' }),
    ).not.toBeNull();
  });
});
