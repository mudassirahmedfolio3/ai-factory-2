// Required by class-transformer when enableImplicitConversion is true
// (Reflect.getMetadata). Must be imported here so unit tests that load this
// module without @nestjs/core still get the polyfill (BUG-001).
import 'reflect-metadata';

import { plainToInstance } from 'class-transformer';
import {
  IsInt,
  IsOptional,
  IsString,
  Max,
  Min,
  validateSync,
} from 'class-validator';

class EnvironmentVariables {
  @IsString()
  DATABASE_URL!: string;

  @IsString()
  JWT_SECRET!: string;

  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(65535)
  PORT: number = 3000;

  @IsOptional()
  @IsInt()
  @Min(60)
  JWT_ACCESS_EXPIRES_SECONDS: number = 900;

  @IsOptional()
  @IsInt()
  @Min(1)
  JWT_REFRESH_EXPIRES_DAYS: number = 7;

  @IsOptional()
  @IsInt()
  @Min(4)
  @Max(15)
  BCRYPT_ROUNDS: number = 12;
}

export function validateEnvironment(
  config: Record<string, unknown>,
): EnvironmentVariables {
  const validatedConfig = plainToInstance(EnvironmentVariables, config, {
    enableImplicitConversion: true,
  });
  const errors = validateSync(validatedConfig, {
    skipMissingProperties: false,
  });
  if (errors.length > 0) {
    throw new Error(`Environment validation failed: ${errors.toString()}`);
  }
  return validatedConfig;
}
