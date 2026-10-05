/** Keep in sync with apps/api/src/openapi/m3-api.operations.ts (Release 2 / M3). */
export const M3_COUNTED_OPERATION_IDS = [
  'getHome',
  'listCategories',
  'getCategoryBySlug',
  'getCatalogFacets',
  'listProducts',
  'getProductById',
  'listProductReviews',
  'registerUser',
  'loginUser',
  'refreshTokens',
  'logoutUser',
  'forgotPassword',
  'resetPassword',
  'getCurrentUser',
  'deleteCurrentUser',
  'getCart',
  'addCartItem',
  'updateCartItem',
  'removeCartItem',
  'mergeGuestCart',
  'previewCheckout',
  'createOrder',
  'confirmMockPayment',
  'listOrders',
  'getOrderById',
  'listWishlist',
  'addWishlistItem',
  'removeWishlistItem',
];

export const M3_HEALTH_OPERATION_ID = 'getHealth';

export const M3_CATALOG_PARITY = {
  minProductCount: 18,
  expectedProductCount: 24,
  minCategoryCount: 7,
};
