import 'reflect-metadata';

import { plainToInstance } from 'class-transformer';
import { validateSync } from 'class-validator';
import { describe, expect, it } from 'vitest';
import {
  AvailabilityFilter,
  ListProductsQueryDto,
  ProductSort,
} from './list-products.query.js';

function validateQuery(raw: Record<string, string>): string[] {
  const dto = plainToInstance(ListProductsQueryDto, raw, {
    enableImplicitConversion: true,
  });
  return validateSync(dto).flatMap((error) => Object.values(error.constraints ?? {}));
}

describe('ListProductsQueryDto (docs/openapi.yaml query parameters)', () => {
  it('accepts q up to 100 characters', () => {
    expect(validateQuery({ q: 'candle' })).toEqual([]);
  });

  it('rejects q longer than 100 characters', () => {
    expect(validateQuery({ q: 'x'.repeat(101) }).length).toBeGreaterThan(0);
  });

  it('accepts documented sort and availability enum values', () => {
    for (const sort of Object.values(ProductSort)) {
      expect(validateQuery({ sort })).toEqual([]);
    }
    for (const availability of Object.values(AvailabilityFilter)) {
      expect(validateQuery({ availability })).toEqual([]);
    }
  });

  it('rejects undocumented sort values', () => {
    expect(validateQuery({ sort: 'popular' }).length).toBeGreaterThan(0);
  });

  it('rejects pageSize above the documented maximum of 100', () => {
    expect(validateQuery({ pageSize: '101' }).length).toBeGreaterThan(0);
  });
});
