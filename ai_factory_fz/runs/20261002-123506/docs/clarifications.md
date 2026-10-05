# Clarifications

Q: For the first demo, is Stripe card checkout (PaymentIntents + SDK) the only payment method required, or must Apple Pay and/or Google Pay also be supported?
A: Stripe card checkout only for the first demo. Apple Pay and Google Pay are not required in this sprint; we can add them after we prove the basic buy flow works.
Q: Which catalog filter dimensions are in MVP scope beyond text search (e.g. price range, metal, occasion, category, in-stock only)?
A: Beyond text search, MVP filters are: price range, category (e.g. earrings, necklaces, bracelets, rings), metal (e.g. gold-tone, silver-tone, rose gold), and occasion (e.g. everyday, work, gift, party). In-stock only is not required for this demo.
Q: Must product reviews and star ratings be limited to verified purchasers of that product, or may any signed-in user rate and review?
A: Any signed-in user may leave a star rating and review for this release. Verified-purchase-only reviews can wait until we have real order history; for the demo we still show reviews and ratings clearly on each product.
Q: What return/refund policy text must appear at checkout for this release (or is a short placeholder policy acceptable for the sprint demo)?
A: A short placeholder policy is acceptable for the sprint demo. Use this copy at checkout: "Returns & refunds: Unworn jewellery may be returned within 30 days of delivery for a full refund to the original payment method. Earrings are final sale for hygiene reasons unless faulty. Contact support@womensjewellery.demo to start a return."
Q: What brand display name and from-address should the order confirmation email use?
A: Brand display name: Womens Jewellery. From address: orders@womensjewellery.demo (sender name shown as "Womens Jewellery").
