import { validateEnv } from './env.validation';

describe('validateEnv', () => {
  it('accepts required DATABASE_URL', () => {
    const result = validateEnv({
      DATABASE_URL: 'postgresql://localhost:5432/db?schema=public',
      JWT_ACCESS_SECRET: 'access-secret-min-16-chars',
      JWT_REFRESH_SECRET: 'refresh-secret-min-16-chars',
    });
    expect(result.DATABASE_URL).toContain('postgresql');
  });

  it('rejects missing DATABASE_URL', () => {
    expect(() =>
      validateEnv({
        JWT_ACCESS_SECRET: 'access-secret-min-16-chars',
        JWT_REFRESH_SECRET: 'refresh-secret-min-16-chars',
      }),
    ).toThrow(/Invalid environment/);
  });

  it('rejects missing JWT secrets', () => {
    expect(() =>
      validateEnv({
        DATABASE_URL: 'postgresql://localhost:5432/db?schema=public',
      }),
    ).toThrow(/Invalid environment/);
  });
});
