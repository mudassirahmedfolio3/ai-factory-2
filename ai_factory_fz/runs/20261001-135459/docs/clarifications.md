# Clarifications

Q: Should v1 support guest checkout, or require signed-in accounts only (project default is signed-in carts unless guest is explicitly in scope)?
A: V1 must support guest checkout. First-time buyers should not be blocked by account creation. Optional simple account/login is fine for returning customers who want saved preferences and order history, but guest checkout is required at launch.
Q: What fulfillment options are required at launch: local delivery, shipping, in-store pickup, or a mix—and which address/contact fields are mandatory at checkout?
A: Launch with a mix of local delivery and in-store pickup. Full shipping can wait for a later release. Mandatory checkout fields: full name, phone number, and email. For local delivery also require delivery address (street, city/area, and postal/ZIP if used locally). For in-store pickup, contact details only—no delivery address required.
Q: Is Stripe card PaymentIntents (test mode) the only payment method for v1, or are digital wallets / cash on delivery also required?
A: Stripe card payments via PaymentIntents (test mode for development, live cards at launch) is the only required payment method for v1. Digital wallets and cash on delivery are not required for the first release.
Q: What return/refund and tax rules must the app enforce in v1 (e.g., return window, refund-to-original-payment, tax inclusive vs exclusive pricing)?
A: Show a simple return policy in the app: customers may request returns within 14 days of delivery/pickup for unused items in original condition. Refunds go back to the original payment method. Display prices tax-inclusive (final price shown is what the customer pays). No complex tax engine in v1—use a single configured tax-inclusive pricing approach for the launch market.
Q: What approximate catalog size, product categories, and markets/currencies/languages should the first release support?
A: Support roughly 50–150 products at launch across a small set of retail categories such as Apparel, Accessories, Home, and Essentials (or equivalent store categories). Single market initially: English language and one primary currency (USD unless the store’s local currency is already set). No multi-language or multi-currency support in v1.
