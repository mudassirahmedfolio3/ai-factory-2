# Clarifications

Q: Which payment providers and methods (card only, Apple Pay / Google Pay, COD) are required for the demo?
A: For the MVP demo, card payment only is required—use a simple simulated or basic card checkout (e.g., test card entry). Apple Pay, Google Pay, and cash on delivery are out of scope for this sprint so we can ship a clean browse → cart → pay → confirmation path quickly.
Q: What is the initial catalog size and source of product data—manual seed list, CSV import, or admin entry?
A: Ship with a manual seed list of about 12–20 smartphones (mix of popular models and price points), with listing style like iPhone X ($899.99)—name, price, and key details. No CSV import or admin product entry in this release; we can expand catalog tooling after the demo validates demand.
Q: How should reviews be moderated—open posting after purchase only, or allow any signed-in user?
A: Allow any signed-in user to post a review and star rating on a product page for the MVP. Do not require a prior purchase to review in this sprint. Keep moderation light: no complex approval queue—just basic content on the product (rating + short text) so social proof is visible for the demo.
Q: Which markets, currencies, and tax/shipping rules apply for the first release?
A: First release targets a single English-language market with USD pricing only. Apply a simple flat shipping fee at checkout and do not calculate complex tax jurisdictions for the MVP—either show prices as tax-inclusive or add a single simple tax line if needed for the demo. Multi-country, multi-currency, and detailed tax/shipping rules are out of scope.
Q: What account recovery and email/notification flows are required beyond basic sign-up and sign-in?
A: Beyond sign-up and sign-in, include a simple forgot-password / reset flow only. Order confirmation can be shown in-app after checkout; full email/push notification systems and advanced account recovery are not required for this one-sprint demo.
Q: Is inventory tracking and out-of-stock handling required in the MVP, or can stock be assumed available?
A: Assume stock is available for all seeded products in the MVP. Do not build inventory tracking, low-stock alerts, or out-of-stock blocking for this sprint—every phone in the catalog can be added to cart and purchased for the demo.
Q: What brand name, visual identity, and storefront naming should appear in the app beyond the working project title?
A: Brand the storefront as PulsePhones—a clean, modern mobile phone shop. Use a simple, trustworthy retail look (clear product photos, readable prices, star ratings prominent on listings and detail pages). App name and splash/home branding should say PulsePhones, not the working project title.
