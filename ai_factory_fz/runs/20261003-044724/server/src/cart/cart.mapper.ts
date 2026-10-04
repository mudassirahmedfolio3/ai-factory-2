import type { CartItem } from '@prisma/client';
import type { CartItemResponseDto, CartResponseDto } from './dto/cart.dto.js';

export function toCartItemResponse(item: CartItem & { variant: { productId: string } }): CartItemResponseDto {
  const lineTotalCents = item.unitPriceCents * item.quantity;
  return {
    id: item.id,
    variantId: item.variantId,
    productId: item.variant.productId,
    productName: item.productName,
    variantName: item.variantName,
    quantity: item.quantity,
    unitPrice: { amountCents: item.unitPriceCents, currency: item.currency },
    lineTotal: { amountCents: lineTotalCents, currency: item.currency },
  };
}

export function toCartResponse(
  items: (CartItem & { variant: { productId: string } })[],
): CartResponseDto {
  const mapped = items.map(toCartItemResponse);
  const currency = mapped[0]?.unitPrice.currency ?? 'USD';
  const subtotalCents = mapped.reduce(
    (sum, line) => sum + line.lineTotal.amountCents,
    0,
  );
  return {
    items: mapped,
    subtotal: { amountCents: subtotalCents, currency },
  };
}
