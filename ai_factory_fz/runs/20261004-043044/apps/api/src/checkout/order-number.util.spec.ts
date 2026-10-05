import { generateOrderNumber } from './order-number.util';

describe('generateOrderNumber', () => {
  it('starts with LUM- and fits within 20 characters', () => {
    const value = generateOrderNumber(new Date('2026-04-05T12:00:00Z'));
    expect(value.startsWith('LUM-260405-')).toBe(true);
    expect(value.length).toBeLessThanOrEqual(20);
  });
});
