import { CartItem, GuestCartItem, Product, ProductVariant } from '@prisma/client';
import { CartLineItemDto } from './dto/cart-line-item.dto';
import { CartResponseDto } from './dto/cart-response.dto';

type LineWithVariant = (CartItem | GuestCartItem) & {
  variant: ProductVariant & { product: Product };
};

export function lineImageUrl(variant: ProductVariant, product: Product): string {
  return variant.imageUrl ?? product.primaryImageUrl;
}

export function toCartLineItem(line: LineWithVariant): CartLineItemDto {
  const unitPriceCents = line.unitPriceCents;
  return {
    id: line.id,
    variantId: line.variantId,
    productId: line.variant.productId,
    productName: line.productName,
    variantLabel: line.variantLabel,
    sku: line.sku,
    quantity: line.quantity,
    unitPrice: {
      amountCents: unitPriceCents,
      currency: line.currency,
    },
    lineSubtotalCents: unitPriceCents * line.quantity,
    imageUrl: lineImageUrl(line.variant, line.variant.product),
  };
}

export function toCartResponse(
  cartId: string,
  items: LineWithVariant[],
  options?: { guestCartId?: string },
): CartResponseDto {
  const mappedItems = items.map(toCartLineItem);
  const subtotalCents = mappedItems.reduce((sum, item) => sum + item.lineSubtotalCents, 0);
  const itemCount = mappedItems.reduce((sum, item) => sum + item.quantity, 0);
  const currency = mappedItems[0]?.unitPrice.currency ?? 'GBP';

  return {
    id: cartId,
    guestCartId: options?.guestCartId,
    items: mappedItems,
    subtotalCents,
    currency,
    itemCount,
  };
}
