import { plainToInstance } from 'class-transformer';
import {
  IsInt,
  IsOptional,
  IsString,
  Max,
  Min,
  MinLength,
  validateSync,
} from 'class-validator';

class EnvironmentVariables {
  @IsString()
  DATABASE_URL!: string;

  @IsString()
  @MinLength(16)
  JWT_ACCESS_SECRET!: string;

  @IsString()
  @MinLength(16)
  JWT_REFRESH_SECRET!: string;

  @IsOptional()
  @IsInt()
  @Min(60)
  @Max(86400)
  JWT_ACCESS_EXPIRES_SECONDS?: number;

  @IsOptional()
  @IsInt()
  @Min(3600)
  @Max(2592000)
  JWT_REFRESH_EXPIRES_SECONDS?: number;

  @IsOptional()
  @IsInt()
  @Min(300)
  @Max(86400)
  PASSWORD_RESET_EXPIRES_SECONDS?: number;

  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(65535)
  PORT?: number;

  @IsOptional()
  @IsString()
  NODE_ENV?: string;

  @IsOptional()
  @IsInt()
  @Min(3600)
  @Max(2_592_000)
  GUEST_CART_TTL_SECONDS?: number;

  @IsOptional()
  @IsInt()
  @Min(0)
  @Max(1_000_000)
  UK_SHIPPING_FLAT_RATE_CENTS?: number;

  @IsOptional()
  @IsInt()
  @Min(0)
  @Max(10_000_000)
  UK_FREE_DELIVERY_THRESHOLD_CENTS?: number;

  @IsOptional()
  @IsInt()
  @Min(300)
  @Max(86400)
  MOCK_PAYMENT_SESSION_EXPIRES_SECONDS?: number;

  @IsOptional()
  @IsInt()
  @Min(300)
  @Max(86400)
  STOCK_RESERVATION_EXPIRES_SECONDS?: number;

  /** 1 = persist ProductViewEvent rows on product detail reads; 0 = log-only stub (default). */
  @IsOptional()
  @IsInt()
  @Min(0)
  @Max(1)
  ANALYTICS_PERSIST_PRODUCT_VIEWS?: number;
}

export function validateEnv(config: Record<string, unknown>): Record<string, unknown> {
  const validated = plainToInstance(EnvironmentVariables, config, {
    enableImplicitConversion: true,
  });
  const errors = validateSync(validated, { skipMissingProperties: false });
  if (errors.length > 0) {
    throw new Error(`Invalid environment: ${errors.toString()}`);
  }
  return validated as unknown as Record<string, unknown>;
}

export const DEFAULT_ACCESS_EXPIRES_SECONDS = 900;
export const DEFAULT_REFRESH_EXPIRES_SECONDS = 604_800;
export const DEFAULT_PASSWORD_RESET_EXPIRES_SECONDS = 3600;
