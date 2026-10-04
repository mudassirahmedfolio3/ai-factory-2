# Clarifications

Q: Should the cart persist after the app is closed and reopened, or is in-session only acceptable for the demo?
A: In-session only is acceptable. The brief says the cart only needs to be kept while the app is open. Persistence across app restarts can wait until the next phase, so no local storage for the cart is needed in this release.
Q: Do you want search and sorting (by price, popularity) in the first demo, or should they be deferred to the next phase? If sorting is included, which sort options are required?
A: Defer both search and sorting to the next phase. The first demo covers browse with basic category filtering only, which keeps scope small and within the 4-6 week timeline. With only 20-30 products, shoppers can scroll and filter by category easily.
Q: Should product variants (for example shades and sizes) be supported in the demo, or is each product a single purchasable item?
A: Each product is a single purchasable item. No shades, sizes or variants in the demo. Variants can be considered in a later phase, so please keep the data model easy to extend, but do not build variant selection now. Your standard per-variant stock tracking is not needed for this release.
Q: Should the demo show stock availability or out-of-stock states, or can all products be treated as always available with a maximum quantity limit per line (for example 10)?
A: Treat all products as always available, with no stock display and no out-of-stock states. Yes, please use a maximum quantity of 10 per cart line, with a minimum of 1.
Q: Should the app include a Checkout button or any path beyond the cart, for example a disabled or placeholder button with a 'coming soon' message, or should the cart end at the total with no checkout entry point?
A: The cart should end at the total, with no checkout entry point. Checkout, payments, and accounts are out of scope for this version, and I do not want a placeholder button that could confuse stakeholders or suggest something that does not work. We will add checkout in a later phase.
Q: Is the demo for iOS, Android or both, and which devices and minimum OS versions will be used at the showcase?
A: Both iOS and Android, as the brief requires Flutter to run on both. We will present mainly on a recent iPhone and a recent mid-range Android phone. Please support reasonably current OS versions, for example iOS 14 or later and Android 8 (API 26) or later, and let us know if the team recommends different minimums. Tablets and web are not required.
Q: Are final brand guidelines (logo, colors, fonts) available, or should the team propose a simple style?
A: We do not have full final brand guidelines ready. We will supply our logo. Please propose a simple, premium, beauty-oriented style covering colors, typography and imagery, with good contrast and readable text sizes, and send it to us for approval early in the project.
Q: Will product data, images and descriptions be delivered in a defined format (for example JSON with image files), and will each product belong to exactly one category? Is the final list of categories Skincare, Makeup, Haircare and Fragrance?
A: Yes. We will supply about 20-30 products as a JSON file (or a spreadsheet we can convert to JSON if the team prefers to give us a template) plus image files. Each product will have an ID, name, brand, category, price in USD, short description, key ingredients or usage notes, and an image. Each product belongs to exactly one category. The final categories are Skincare, Makeup, Haircare and Fragrance, plus an All view showing everything.
Q: Should any analytics or event tracking be included in the demo to measure interest, or should it be explicitly excluded?
A: Exclude analytics and event tracking from the demo. We will gather feedback directly from stakeholders and test users at the showcase. This also avoids privacy and consent requirements at this stage. Analytics can be added in a later phase.
Q: Is the cart expected to apply any promotions, discounts, shipping or tax estimates, or should the total be a simple sum of item subtotals in USD?
A: The total should be a simple sum of item subtotals in USD. Each line shows price times quantity, and the overall total is the sum of the lines. There are no promotions, discounts, shipping or tax estimates in this version.
