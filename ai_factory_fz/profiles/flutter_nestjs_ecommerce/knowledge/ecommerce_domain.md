E-commerce domain rules for this project:
- Prices are stored as integer minor units (cents) with an ISO 4217 currency code. Never floats.
- Stock is tracked per product variant. Checkout reserves stock; a failed or expired payment releases it.
- A cart belongs to a signed-in user (guest carts are out of scope for the first release unless the PRD says otherwise).
- Order status flow: pending_payment -> paid -> fulfilled -> delivered, plus cancelled and refunded.
- Order lines copy product name and unit price at purchase time, so later catalog changes do not alter past orders.
- Payments use Stripe PaymentIntents in test mode. The server creates the intent; the app confirms it with the Stripe SDK; a Stripe webhook marks the order paid. Card data never touches our server.
- Personal data: store the minimum; passwords hashed with bcrypt or argon2; support account deletion.
