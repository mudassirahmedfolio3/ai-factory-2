<!-- SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline. Delete this folder when you have a real run. -->
# Product Brief: ShopEase Mini

## Vision
A tiny mobile shop that lets people browse a handful of products and put them in a cart.

## Target users
Casual shoppers on Android and iOS phones who want a quick, simple way to look at products and see what they would pay.

## Goals
- Let a shopper browse products with name, price and picture.
- Let a shopper open a product to read its description.
- Let a shopper add products to a cart and see quantities and the total price.

## Key features
1. Product list
2. Product detail
3. Add to cart
4. Cart with quantities and total (USD)

## Constraints
- Prices in USD only.
- No sign-in; the cart is tied to an anonymous id kept on the device.
- The product list should appear within 2 seconds on a normal mobile connection.

## Out of scope
Accounts, payments and checkout, admin tools, emails, order history, delivery and returns.

## Open questions (clarified with the customer)
- Where do products come from? A small fixed catalogue served by the API.
- Is stock tracked? No.
