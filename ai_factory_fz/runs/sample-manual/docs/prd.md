<!-- SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline. Delete this folder when you have a real run. -->
# PRD: ShopEase Mini

## Summary
A tiny mobile shop. Shoppers browse products, open one to read its description, add it to a cart,
and see the cart with quantities and the total price. Prices are in USD.

## User stories

### US-001: Browse products (must)
As a shopper, I want to see a list of products with name, price and picture so that I can find something to buy.
- Given the app is open, When the product list loads, Then each product shows its name, price in USD and picture.
- Given the product list is loading, When the API has not answered yet, Then a loading state is shown.
- Given there are no products, When the list loads, Then an empty-state message is shown.

### US-002: View product details (must)
As a shopper, I want to open a product to read its description so that I can decide whether to buy it.
- Given the product list, When I tap a product, Then a detail screen shows its name, picture, price and description.
- Given a product that no longer exists, When I open it, Then an error message with a way back is shown.

### US-003: Add to cart (must)
As a shopper, I want to add a product to my cart so that I can buy it later.
- Given a product detail screen, When I tap "Add to cart", Then the product is in my cart with quantity 1.
- Given the product is already in my cart, When I add it again, Then its quantity increases by 1.

### US-004: View cart and total (must)
As a shopper, I want to see my cart with quantities and the total price so that I know what I will pay.
- Given items in my cart, When I open the cart, Then each line shows name, unit price, quantity and line total, and the cart shows the total in USD.
- Given I change a quantity, When the cart updates, Then the line total and the cart total are recalculated.
- Given an empty cart, When I open it, Then an empty-state message is shown.

## Non-functional requirements
- Performance: the product list appears within 2 seconds on a normal mobile connection.
- Security: no secrets in the app; the API is served over HTTPS in production.
- Privacy: no personal data is collected; the cart is tied to an anonymous id kept on the device.
- Accessibility: touch targets of at least 48dp and text contrast of at least WCAG AA.
- Supported platforms: Android and iOS.

## Out of scope
Sign-in and accounts, payments and checkout, admin tools, emails, order history, delivery and returns.
