import 'reflect-metadata';

if (!process.env.DATABASE_URL) {
  process.env.DATABASE_URL =
    'postgresql://localhost:5432/lighting_test?schema=public';
}

if (!process.env.JWT_ACCESS_SECRET) {
  process.env.JWT_ACCESS_SECRET = 'test-jwt-access-secret-min-16-chars';
}

if (!process.env.JWT_REFRESH_SECRET) {
  process.env.JWT_REFRESH_SECRET = 'test-jwt-refresh-secret-min-16-chars';
}
