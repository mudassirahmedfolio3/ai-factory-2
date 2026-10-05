import {
  BadRequestException,
  Injectable,
  UnauthorizedException,
} from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service.js';
import {
  CheckoutPricingService,
  type PricedLineContext,
} from './checkout-pricing.service.js';
import type {
  CheckoutQuoteRequestDto,
  CheckoutQuoteResponseDto,
} from './dto/checkout.dto.js';
import { validateUsShippingAddress } from './us-address.util.js';
import { CartLineInputDto } from '../cart/dto/cart.dto.js';

@Injectable()
export class CheckoutService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly pricing: CheckoutPricingService,
  ) {}

  async createQuote(
    userId: string | undefined,
    dto: CheckoutQuoteRequestDto,
  ): Promise<CheckoutQuoteResponseDto> {
    const addressError = validateUsShippingAddress(dto.shippingAddress);
    if (addressError !== null) {
      throw new BadRequestException(addressError);
    }

    const useServerCart = dto.useServerCart !== false;
    if (useServerCart && userId === undefined) {
      throw new UnauthorizedException('Unauthorized');
    }

    const lines = await this.resolveLines(
      userId,
      useServerCart,
      dto.lines,
    );
    if (lines.length === 0) {
      throw new BadRequestException('Cart is empty');
    }

    const storeConfig = await this.loadStoreConfig();
    const couponRecord = await this.loadCoupon(dto.couponCode);
    const breakdown = this.pricing.computeBreakdown(
      lines,
      storeConfig,
      couponRecord,
      dto.couponCode,
    );

    return this.toQuoteResponse(breakdown);
  }

  async resolveLinesForOrder(
    userId: string,
    useServerCart: boolean,
    lines: CartLineInputDto[] | undefined,
  ): Promise<PricedLineContext[]> {
    return this.resolveLines(userId, useServerCart, lines);
  }

  async loadStoreConfig() {
    const config = await this.prisma.storeConfig.findUnique({ where: { id: 1 } });
    if (config === null) {
      throw new BadRequestException('Store configuration is unavailable');
    }
    return config;
  }

  async loadCoupon(code: string | undefined) {
    if (code === undefined || code.trim().length === 0) {
      return null;
    }
    return this.prisma.coupon.findUnique({
      where: { code: code.trim().toUpperCase() },
      include: { exclusions: true },
    });
  }

  computeBreakdownForLines(
    lines: PricedLineContext[],
    storeConfig: Awaited<ReturnType<CheckoutService['loadStoreConfig']>>,
    couponRecord: Awaited<ReturnType<CheckoutService['loadCoupon']>>,
    couponCode: string | undefined,
  ) {
    return this.pricing.computeBreakdown(
      lines,
      storeConfig,
      couponRecord,
      couponCode,
    );
  }

  private async resolveLines(
    userId: string | undefined,
    useServerCart: boolean,
    inputLines: CartLineInputDto[] | undefined,
  ): Promise<PricedLineContext[]> {
    if (useServerCart) {
      if (userId === undefined) {
        throw new UnauthorizedException('Unauthorized');
      }
      const items = await this.prisma.cartItem.findMany({
        where: { cart: { userId } },
        include: {
          variant: {
            include: {
              product: {
                select: { id: true, categoryId: true, isActive: true, name: true },
              },
            },
          },
        },
        orderBy: { createdAt: 'asc' },
      });
      if (items.length === 0) {
        return [];
      }
      return items.map((item) => {
        this.assertVariantAvailable(item.variant, item.quantity);
        return this.toPricedLine(item.variant, item.quantity, item);
      });
    }

    if (inputLines === undefined || inputLines.length === 0) {
      throw new BadRequestException('Cart lines are required');
    }

    const aggregated = aggregateLines(inputLines);
    const variants = await this.prisma.productVariant.findMany({
      where: { id: { in: [...aggregated.keys()] } },
      include: {
        product: {
          select: { id: true, categoryId: true, isActive: true, name: true },
        },
      },
    });
    const byId = new Map(variants.map((v) => [v.id, v]));

    const resolved: PricedLineContext[] = [];
    for (const [variantId, quantity] of aggregated) {
      const variant = byId.get(variantId);
      if (variant === undefined) {
        throw new BadRequestException(`Unknown product variant: ${variantId}`);
      }
      this.assertVariantAvailable(variant, quantity);
      resolved.push(this.toPricedLine(variant, quantity));
    }
    return resolved;
  }

  private assertVariantAvailable(
    variant: {
      isActive: boolean;
      stockQuantity: number;
      reservedQuantity: number;
      product: { isActive: boolean };
    },
    quantity: number,
  ): void {
    if (!variant.isActive || !variant.product.isActive) {
      throw new BadRequestException('Product variant is not available');
    }
    const available = Math.max(
      0,
      variant.stockQuantity - variant.reservedQuantity,
    );
    if (quantity > available) {
      throw new BadRequestException('Insufficient stock for one or more items');
    }
  }

  private toPricedLine(
    variant: {
      id: string;
      sku: string;
      name: string;
      priceCents: number;
      currency: string;
      product: { id: string; categoryId: string; name: string };
    },
    quantity: number,
    snapshot?: {
      productName: string;
      variantName: string;
      unitPriceCents: number;
      currency: string;
    },
  ): PricedLineContext {
    return {
      variantId: variant.id,
      productId: variant.product.id,
      categoryId: variant.product.categoryId,
      quantity,
      unitPriceCents: snapshot?.unitPriceCents ?? variant.priceCents,
      currency: snapshot?.currency ?? variant.currency,
      productName: snapshot?.productName ?? variant.product.name,
      variantName: snapshot?.variantName ?? variant.name,
      sku: variant.sku,
    };
  }

  private toQuoteResponse(
    breakdown: ReturnType<CheckoutPricingService['computeBreakdown']>,
  ): CheckoutQuoteResponseDto {
    const { currency } = breakdown;
    const money = (amountCents: number) => ({ amountCents, currency });
    return {
      lines: breakdown.lines,
      subtotal: money(breakdown.subtotalCents),
      discount: money(breakdown.discountCents),
      shipping: money(breakdown.shippingCents),
      tax: money(breakdown.taxCents),
      total: money(breakdown.totalCents),
      coupon: breakdown.coupon,
      taxDisclaimer: this.pricing.taxDisclaimer,
    };
  }
}

function aggregateLines(lines: CartLineInputDto[]): Map<string, number> {
  const map = new Map<string, number>();
  for (const line of lines) {
    map.set(line.variantId, (map.get(line.variantId) ?? 0) + line.quantity);
  }
  return map;
}
