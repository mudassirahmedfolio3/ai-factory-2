import { validateEnv } from './env.validation';

describe('validateEnv', () => {
  it('accepts required DATABASE_URL', () => {
    const result = validateEnv({
      DATABASE_URL: 'postgresql://user:pass@localhost:5432/db',
    });
    expect(result.DATABASE_URL).toContain('postgresql');
  });

  it('rejects missing DATABASE_URL', () => {
    expect(() => validateEnv({})).toThrow(/Invalid environment/);
  });
});
