# Design system

## Colors
| Token | Light | Dark |
|---|---|---|
| primary | #B0245A | #F4A6C0 |
| onPrimary | #FFFFFF | #4A0E25 |
| background | #FFF8F9 | #141012 |
| surface | #FFFFFF | #1C1719 |
| onSurface | #1F1A1C | #ECE0E3 |
| onSurfaceVariant | #5F5358 | #CFC2C6 |
| outline | #85737A | #9C8C92 |
| error | #B3261E | #F2B8B5 |
| onError | #FFFFFF | #601410 |
| badgeBackground | #B3261E | #F2B8B5 |
| onBadge | #FFFFFF | #601410 |
| placeholderLipstick | #C2185B | #E57399 |
| placeholderFoundation | #E8C4A0 | #C9A37F |
| placeholderMascara | #3E3A39 | #6B6563 |
| placeholderFaceSerum | #F2D16B | #D4B44F |
| placeholderMoisturizer | #CFE8E4 | #8FB8B3 |
| placeholderPerfume | #B39DDB | #9575CD |
| placeholderNailPolish | #E53935 | #EF7B78 |
| placeholderBrushSet | #A1887F | #8D6E63 |

## Typography
| Style | Size | Weight | Line height |
|---|---|---|---|
| headlineSmall | 24.0 | 600 | 1.33 |
| titleLarge | 22.0 | 500 | 1.27 |
| titleMedium | 16.0 | 500 | 1.5 |
| priceLarge | 20.0 | 700 | 1.4 |
| bodyLarge | 16.0 | 400 | 1.5 |
| bodyMedium | 14.0 | 400 | 1.43 |
| labelLarge | 14.0 | 500 | 1.43 |
| labelSmall | 11.0 | 500 | 1.45 |

Spacing scale: 4, 8, 12, 16, 24, 32, 48 dp. Corner radii: 4, 8, 12, 16, 999 dp.

## Shared widgets
- **ProductTile**: lib/features/catalog/presentation/widgets/product_tile.dart. Grid tile showing a placeholder color block from a PlaceholderPalette token, the product name and the price formatted from integer cents (e.g. 1999 -> $19.99). Wrapped in InkWell/Semantics(button: true, label: '<name>, <price>') with at least a 48dp tap target. Tapping calls context.push('/products/<id>'). Uses 12dp corner radius, 8dp inner spacing, titleMedium for name and bodyMedium/priceLarge-style token for price; colors come only from theme tokens.
- **PlaceholderBlock**: Rounded color block that stands in for a product image, colored from the PlaceholderColor enum token (placeholder* color tokens, light/dark variants). Used in ProductTile (square, 12dp radius) and ProductDetailScreen (large, full width, 16dp radius). Exposes semantic label '<name> placeholder image' on the detail screen; decorative (excluded from semantics) inside the tile because the tile already has its own label.
- **CartBadge**: lib/features/cart/presentation/widgets/cart_badge.dart. Cart icon inside a Badge placed in the BrowseScreen AppBar actions. Semantic label 'Cart, N items'. Badge hidden when count == 0; shows N when count > 0 using badgeBackground/onBadge tokens and labelSmall. Not tappable; no checkout exists anywhere in the app. Reads cartProvider count.
- **AddToCartButton**: lib/features/cart/presentation/widgets/add_to_cart_button.dart. Full-width FilledButton labelled 'Add to cart' with minimum size 48dp (use 56dp height), primary/onPrimary colors, labelLarge text. Each tap calls cartProvider.notifier.add(productId) and shows a SnackBar 'Added to cart'. No quantity editing or removal.
- **StateMessageView**: Centered message view in lib/core/widgets used for empty and error states: icon (with semantic label), message text (bodyLarge, onSurfaceVariant) and an optional action button with minimum 48dp height (e.g. 'Retry' on Browse error, which invalidates productsProvider; 'Back to products' on Product not found). Empty Browse message: 'No products yet'. Not-found message: 'Product not found'.
- **LoadingIndicator**: Centered CircularProgressIndicator in lib/core/widgets with semantic label 'Loading'. Practically unseen in M1 because data is synchronous; kept for API parity.
- **PriceText**: Text widget that formats integer cents with currency code USD for display only (e.g. 1999 -> $19.99); never uses floating-point price storage. Uses priceLarge on detail and bodyMedium bold on tiles with onSurface color.

## Screens
### SCR-01 BrowseScreen (`/`)
Home screen (route name 'browse'). Shows a 2-column grid of exactly 8 hard-coded beauty products (lipstick, foundation, mascara, face serum, moisturizer, perfume, nail polish, makeup brush set), each with placeholder color block, name and USD price formatted from cents. Works offline with no backend. AppBar titled 'beauty-mini' with CartBadge. Tapping a tile pushes the product detail via context.push('/products/<id>') so the grid state is preserved on return. Data from productsProvider (Provider<List<Product>>).
- Components: AppBar (title 'beauty-mini'), CartBadge, GridView (2 columns, 16dp padding, 12dp gaps), ProductTile x8, PlaceholderBlock, PriceText, StateMessageView, LoadingIndicator
- States: success: grid of exactly 8 ProductTile widgets, CartBadge hidden when cart count is 0 and showing N when N > 0, empty: 'No products yet' message, error: message with Retry button that invalidates productsProvider, loading: centered spinner (practically unseen because data is synchronous)
- Stories: US-001, US-002, US-003

### SCR-02 ProductDetailScreen (`/products/:productId`)
Detail screen (route name 'productDetail'). AppBar with back button; large placeholder color block with semantic label '<name> placeholder image', then product name, USD price, short description and AddToCartButton. Name and price match the tapped tile. System back / AppBar back pops to Browse with grid preserved. Data from productByIdProvider(productId). Add to cart increments the in-memory cart count shown on Browse and shows SnackBar 'Added to cart'.
- Components: AppBar (back button), PlaceholderBlock (large), Text name (headlineSmall), PriceText, Text description (bodyLarge), AddToCartButton, StateMessageView, LoadingIndicator, SnackBar
- States: success: name, price, description and Add to cart button displayed, not-found/error: productId unknown shows 'Product not found' and a 'Back to products' button, loading: centered spinner for API parity (practically unseen), added: SnackBar 'Added to cart' after each Add to cart tap
- Stories: US-002, US-003

## Navigation
- SCR-01 BrowseScreen → SCR-02 ProductDetailScreen: Tap a ProductTile -> context.push('/products/<id>')
- SCR-02 ProductDetailScreen → SCR-01 BrowseScreen: AppBar back button or system back gesture (pop); grid state preserved and CartBadge reflects updated count
- SCR-02 ProductDetailScreen → SCR-01 BrowseScreen: Tap 'Back to products' button on the 'Product not found' state (context.go('/'))

## Accessibility
- Minimum touch target 48x48dp for all interactive elements: ProductTile, AppBar back button, AddToCartButton (min 48dp, use 56dp height), Retry and 'Back to products' buttons.
- ProductTile exposes Semantics(button: true, label: '<name>, <price>') so product names and prices are read by screen readers.
- Detail placeholder block has semantic label '<name> placeholder image'; all icons and images have semantic labels.
- CartBadge has semantic label 'Cart, N items'; it is not tappable and is hidden when count is 0.
- Text contrast meets WCAG AA (at least 4.5:1 for body text, 3:1 for large text and UI components) in both light and dark themes; text is never drawn directly on placeholder colors, it sits on surface tokens below the color block.
- Placeholder colors are never the only means of identifying a product; name and price are always shown as text.
- SnackBar 'Added to cart' is announced to screen readers as a live region.
- Support dynamic text scaling; tile layouts must not overflow at 200% text scale (use flexible tile height and maxLines with ellipsis for names).
- Light and dark themes are built from design tokens in lib/core/theme; no hard-coded colors or sizes in widgets.
- Every screen handles loading, empty and error states with readable messages and focusable action buttons.