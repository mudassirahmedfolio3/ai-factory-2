# Clarifications

Q: Which platform(s) must the first demo run on: iOS, Android, or both, and should it be shown on physical devices or emulators?
A: Both iOS and Android, since we are building in Flutter from one codebase. For the stakeholder demo we will show it on physical phones (one iPhone and one Android phone), with emulators as a backup. If time gets tight, iOS is the priority for the stakeholder meeting, but the app must still run correctly on Android.
Q: Should the cart persist between app launches (local storage) or may it reset each time the app is closed?
A: It is fine for the cart to reset when the app is closed. The cart is for demonstration only, so simple in-memory state is enough. Saving the cart between launches can wait for the next phase.
Q: Should the first demo include search and/or sorting (for example price low-to-high), or only category filtering?
A: Category filtering only. Search and sorting are out of scope for the first demo to keep the build small. We will consider them for the next phase based on feedback.
Q: Which product categories and roughly how many products are in the sample catalog, and who supplies the images, descriptions, prices and currency (which single currency should be displayed)?
A: Four categories: skincare, makeup, haircare and fragrance. About 24 products in total, roughly 6 per category. We will supply the product images, descriptions, brand names and prices from our own catalog, using only content we own or have rights to use. If images are not ready in time, the team can use neutral placeholder images for the demo. All prices are shown in a single currency, US dollars ($).
Q: Which variant types must the product detail page support (size and/or shade), and should each variant have its own price, image, or an out-of-stock indicator in the demo, or is stock display out of scope?
A: Support both size and shade selectors, shown only where they apply (for example shades for makeup, sizes for skincare and haircare). Variants do not need their own price, image, or stock status. The product has one price and one main image set, and selecting a variant simply records the choice on the cart item. Stock display and out-of-stock indicators are out of scope.
Q: Should the demo show product reviews or ratings, or are they excluded from this release?
A: Excluded. No reviews or ratings in this release. We will revisit them in a later phase.
Q: Are there brand guidelines (logo, colors, fonts) to follow, or should the team propose a simple style for approval?
A: We do not have formal brand guidelines. We will provide our logo file. The team should propose a simple, clean palette and typography that matches the logo, and send it to us for quick approval before building the full UI.
Q: What should happen when the user taps a checkout or proceed button in the cart: no button at all, or a disabled/placeholder button with a message such as 'Coming soon'?
A: Show a Checkout button that is clearly a placeholder. When tapped, it displays a short message such as 'Checkout is coming soon. This is a demo.' No payment, account, or order flow should exist behind it.
Q: Is a demo deadline date known, and are there any accessibility or language requirements (for example English only) for the demo?
A: We do not have a fixed date yet, but the target is a build of about 3 to 4 weeks so we can show it soon, with the stakeholder demo (owner, sales and marketing leads) right after. The demo is English only, with a single currency. For accessibility, please use readable text sizes, good color contrast, and tappable areas that are large enough. Full accessibility compliance is not required for this demo.
