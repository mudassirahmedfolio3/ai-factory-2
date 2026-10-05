/** OpenAPI operationIds for M3 (contract test source of truth). */
export const M3_COUNTED_OPERATIONS = [
  { operationId: 'getHome', method: 'get', path: '/home' },
  { operationId: 'listCategories', method: 'get', path: '/categories' },
  {
    operationId: 'getCategoryBySlug',
    method: 'get',
    path: '/categories/{slug}',
  },
  { operationId: 'getCatalogFacets', method: 'get', path: '/catalog/facets' },
  { operationId: 'listProducts', method: 'get', path: '/products' },
  {
    operationId: 'getProductById',
    method: 'get',
    path: '/products/{productId}',
  },
  {
    operationId: 'listProductReviews',
    method: 'get',
    path: '/products/{productId}/reviews',
  },
  { operationId: 'registerUser', method: 'post', path: '/auth/register' },
  { operationId: 'loginUser', method: 'post', path: '/auth/login' },
  { operationId: 'refreshTokens', method: 'post', path: '/auth/refresh' },
  { operationId: 'logoutUser', method: 'post', path: '/auth/logout' },
  {
    operationId: 'forgotPassword',
    method: 'post',
    path: '/auth/forgot-password',
  },
  {
    operationId: 'resetPassword',
    method: 'post',
    path: '/auth/reset-password',
  },
  { operationId: 'getCurrentUser', method: 'get', path: '/users/me' },
  { operationId: 'deleteCurrentUser', method: 'delete', path: '/users/me' },
  { operationId: 'getCart', method: 'get', path: '/cart' },
  { operationId: 'addCartItem', method: 'post', path: '/cart/items' },
  {
    operationId: 'updateCartItem',
    method: 'patch',
    path: '/cart/items/{itemId}',
  },
  {
    operationId: 'removeCartItem',
    method: 'delete',
    path: '/cart/items/{itemId}',
  },
  { operationId: 'mergeGuestCart', method: 'post', path: '/cart/merge' },
  {
    operationId: 'previewCheckout',
    method: 'post',
    path: '/checkout/preview',
  },
  { operationId: 'createOrder', method: 'post', path: '/checkout/orders' },
  {
    operationId: 'confirmMockPayment',
    method: 'post',
    path: '/payments/mock/confirm',
  },
  { operationId: 'listOrders', method: 'get', path: '/orders' },
  { operationId: 'getOrderById', method: 'get', path: '/orders/{orderId}' },
  { operationId: 'listWishlist', method: 'get', path: '/wishlist' },
  { operationId: 'addWishlistItem', method: 'post', path: '/wishlist/items' },
  {
    operationId: 'removeWishlistItem',
    method: 'delete',
    path: '/wishlist/items/{productId}',
  },
] as const;

/** Infrastructure operation; excluded from the twenty-eight operation cap. */
export const M3_HEALTH_OPERATION = {
  operationId: 'getHealth',
  method: 'get',
  path: '/health',
} as const;

export const M3_API_OPERATIONS = [
  M3_HEALTH_OPERATION,
  ...M3_COUNTED_OPERATIONS,
] as const;

export const M3_COUNTED_OPERATION_IDS = M3_COUNTED_OPERATIONS.map(
  (op) => op.operationId,
);

export const M3_API_OPERATION_IDS = M3_API_OPERATIONS.map(
  (op) => op.operationId,
);
