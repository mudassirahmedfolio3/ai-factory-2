import { randomBytes } from 'node:crypto';

/** Generates a unique human-readable order number (max 20 chars). */
export function generateOrderNumber(now = new Date()): string {
  const y = now.getUTCFullYear().toString().slice(-2);
  const m = String(now.getUTCMonth() + 1).padStart(2, '0');
  const d = String(now.getUTCDate()).padStart(2, '0');
  const suffix = randomBytes(3).toString('hex').toUpperCase();
  return `LUM-${y}${m}${d}-${suffix}`;
}
