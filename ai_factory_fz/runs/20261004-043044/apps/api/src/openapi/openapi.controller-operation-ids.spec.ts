import { Type } from '@nestjs/common';

const SWAGGER_API_OPERATION = 'swagger/apiOperation';
import { AuthController } from '../auth/auth.controller';
import { CartController } from '../cart/cart.controller';
import { CatalogController } from '../catalog/catalog.controller';
import { CheckoutController } from '../checkout/checkout.controller';
import { HealthController } from '../health/health.controller';
import { OrdersController } from '../orders/orders.controller';
import { PaymentsController } from '../payments/payments.controller';
import { UsersController } from '../users/users.controller';
import { WishlistController } from '../wishlist/wishlist.controller';
import { M3_API_OPERATIONS } from './m3-api.operations';

const M3_CONTROLLERS: Type<unknown>[] = [
  HealthController,
  CatalogController,
  AuthController,
  UsersController,
  CartController,
  CheckoutController,
  PaymentsController,
  OrdersController,
  WishlistController,
];

function collectControllerOperationIds(controller: Type<unknown>): string[] {
  const prototype = controller.prototype as Record<string, unknown>;
  const ids: string[] = [];

  for (const methodName of Object.getOwnPropertyNames(prototype)) {
    if (methodName === 'constructor') {
      continue;
    }
    const handler = prototype[methodName];
    if (typeof handler !== 'function') {
      continue;
    }
    const operation = Reflect.getMetadata(SWAGGER_API_OPERATION, handler) as
      | { operationId?: string }
      | undefined;
    if (operation?.operationId) {
      ids.push(operation.operationId);
    }
  }

  return ids;
}

describe('Controller OpenAPI operationIds', () => {
  const implementedIds = M3_CONTROLLERS.flatMap(collectControllerOperationIds);

  it('implements every M3 contract operationId on a controller handler', () => {
    for (const { operationId } of M3_API_OPERATIONS) {
      expect(implementedIds).toContain(operationId);
    }
  });

  it('does not duplicate operationIds across controllers', () => {
    expect(new Set(implementedIds).size).toBe(implementedIds.length);
  });
});
