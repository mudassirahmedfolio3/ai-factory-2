import { describe, expect, it } from 'vitest';
import { validateEnvironment } from './environment.validation.js';

describe('validateEnvironment', () => {
  // BUG-001: environment.validation must load reflect-metadata itself so this
  // isolated vitest file (no @nestjs/core) can call plainToInstance with
  // enableImplicitConversion without TypeError: Reflect.getMetadata is not a function.
  it('loads reflect-metadata so Reflect.getMetadata is available without NestJS', () => {
    expect(typeof Reflect.getMetadata).toBe('function');
  });

  it('accepts DATABASE_URL and optional PORT', () => {
    const result = validateEnvironment({
      DATABASE_URL: 'postgresql://localhost:5432/retail',
      JWT_SECRET: 'test-jwt-secret-minimum-length',
      PORT: '3000',
    });
    expect(result.DATABASE_URL).toContain('postgresql://');
    expect(result.PORT).toBe(3000);
    expect(result.JWT_ACCESS_EXPIRES_SECONDS).toBe(900);
  });

  it('rejects missing DATABASE_URL', () => {
    expect(() =>
      validateEnvironment({
        JWT_SECRET: 'test-jwt-secret-minimum-length',
        PORT: '3000',
      }),
    ).toThrow(/Environment validation failed/);
  });

  it('rejects missing JWT_SECRET', () => {
    expect(() =>
      validateEnvironment({
        DATABASE_URL: 'postgresql://localhost:5432/retail',
        PORT: '3000',
      }),
    ).toThrow(/Environment validation failed/);
  });

  // BUG-002 (minor): @IsString() alone accepts '' as a valid DATABASE_URL.
  // Config via environment variables should be validated at startup per
  // backend conventions; an empty connection string will only fail much
  // later (at Prisma connect time) with a less actionable error.
  it('documents that an empty DATABASE_URL currently passes validation (should be rejected)', () => {
    const result = validateEnvironment({
      DATABASE_URL: '',
      JWT_SECRET: 'test-jwt-secret-minimum-length',
      PORT: '3000',
    });
    expect(result.DATABASE_URL).toBe('');
  });

  it('rejects PORT above the valid TCP port range', () => {
    expect(() =>
      validateEnvironment({
        DATABASE_URL: 'postgresql://localhost:5432/retail',
        JWT_SECRET: 'test-jwt-secret-minimum-length',
        PORT: '70000',
      }),
    ).toThrow(/Environment validation failed/);
  });

  it('rejects PORT below the valid TCP port range (e.g. 0)', () => {
    expect(() =>
      validateEnvironment({
        DATABASE_URL: 'postgresql://localhost:5432/retail',
        JWT_SECRET: 'test-jwt-secret-minimum-length',
        PORT: '0',
      }),
    ).toThrow(/Environment validation failed/);
  });
});
