# beauty-mvp Style Guide (Proposal v1.0)

Status: **PROPOSED, awaiting written business approval** (see `design/style_approval.md`)
Work item: WI-001 | Story: US-006 | Milestone: M1
Date: 2026-09-30
Source of tokens: `docs/design_system.md` (this guide does not change any token value; it explains how to use them and records the checks).

---

## 1. Design direction

Clean, premium, beauty-oriented. The look should feel like a quality skincare counter: warm off-white backgrounds, generous white space, one deep rose/berry accent colour, elegant serif headlines and a highly readable sans-serif for everything else. Product photography is the hero; the UI stays quiet around it.

Principles:
1. **Product first**: images get the most space; chrome is minimal (logo bar, category chips, cart button).
2. **One accent**: the rose `primary` is reserved for actions, selection and the cart badge. Never used for large decorative fills.
3. **Readable for everyone**: body text at least 14 sp, contrast at least 4.5:1, touch targets at least 48x48 dp, layouts survive 150% text scale.
4. **Honest and simple**: no stock badges, promo banners, checkout placeholders or decorative clutter (out of scope for the demo).

---

## 2. Colour palette

Light and dark themes follow the device system setting. Widgets use tokens only (from `lib/core/theme`), never hard-coded hex values.

| Token | Light | Dark | Use |
|---|---|---|---|
| primary | #8C3B4F (deep rose) | #F2B8C6 (soft blush) | Primary buttons, selected chip outline and check, links, focus |
| onPrimary | #FFFFFF | #4A1425 | Text/icons on primary |
| primaryContainer | #F8E1E7 | #5E2537 | Selected category chip fill |
| onPrimaryContainer | #3F1220 | #FFD9E2 | Text/icons on primaryContainer |
| background | #FFFBF9 (warm ivory) | #1A1416 | Screen background |
| surface | #FFFFFF | #251D20 | Tiles, cards, app bar, cart lines |
| onSurface | #211A1C | #F5EDEF | Primary text (names, prices, headings) |
| onSurfaceVariant | #6B5C61 | #C9BCC0 | Secondary text (brand, captions, section labels) |
| outline | #857378 | #9A8B90 | Unselected chip borders, dividers, stepper borders |
| placeholder | #EFE6E8 | #3A2F33 | Image placeholder block (decorative) |
| skeleton | #F1E8EA | #33292C | Loading skeleton bars (decorative) |
| error | #B3261E | #F2B8B5 | Error icon and error actions |
| onError | #FFFFFF | #601410 | Text on error |
| inverseSurface | #2E2427 | #F0E4E7 | SnackBar background |
| onInverseSurface | #F8EEF0 | #2E2427 | SnackBar text |
| badge | #8C3B4F | #F2B8C6 | Cart count badge |
| onBadge | #FFFFFF | #4A1425 | Cart count text |

### 2.1 Contrast verification (WCAG 2.1 relative luminance)

Text pairs must be at least 4.5:1; non-text boundaries (outline) at least 3:1. The full workings (relative luminance per token and every pair) are in `design/contrast_table.md`. Summary:

| Pair (foreground on background) | Light | Dark | Required | Result |
|---|---|---|---|---|
| onSurface on background / surface | 16.6:1 / 17.0:1 | 15.8:1 / 14.3:1 | 4.5:1 | Pass |
| onSurfaceVariant on background / surface | 6.1:1 / 6.3:1 | 9.9:1 / 8.9:1 | 4.5:1 | Pass |
| onPrimary on primary | 7.3:1 | 8.7:1 | 4.5:1 | Pass |
| primary on background (text actions) | 7.1:1 | 10.7:1 | 4.5:1 | Pass |
| onPrimaryContainer on primaryContainer | 12.8:1 | 9.0:1 | 4.5:1 | Pass |
| onError on error | 6.5:1 | 7.6:1 | 4.5:1 | Pass |
| onInverseSurface on inverseSurface | 13.2:1 | 12.1:1 | 4.5:1 | Pass |
| onBadge on badge | 7.3:1 | 8.7:1 | 4.5:1 | Pass |
| outline on background / surface | 4.3:1 / 4.4:1 | 5.6:1 / 5.0:1 | 3:1 | Pass |

These values were calculated by hand for the proposal. WI-009 adds an automated contrast unit test over these pairs in the Flutter theme; that test is the authoritative check and stops the palette from regressing.

Rules:
- `placeholder` and `skeleton` are decorative only; never place text on them.
- Selection is never conveyed by colour alone (chip uses fill + outline + check icon + "selected" semantics).
- Disabled controls use reduced emphasis but the icon outline must still reach 3:1.

---

## 3. Typography

Proposed typefaces (both SIL Open Font License, free for commercial use, bundled in the app under `assets/fonts/` so no network fetch is needed):

- **Headlines and prices: Playfair Display** (elegant high-contrast serif, gives the premium beauty feel). Used for headlineLarge, headlineMedium and priceLarge.
- **Everything else: Inter** (neutral, highly legible sans-serif at small sizes on both iOS and Android). Used for titles, body, labels and captions.
- Fallback if the business prefers platform fonts: SF Pro (iOS) / Roboto (Android) with identical sizes and weights.

| Style | Font | Size (sp) | Weight | Line height | Use |
|---|---|---|---|---|---|
| headlineLarge | Playfair Display | 28 | 600 | 1.29 | Product name on Detail |
| headlineMedium | Playfair Display | 22 | 600 | 1.27 | Screen titles (Cart), state titles |
| titleLarge | Inter | 18 | 600 | 1.33 | Section headings (Key ingredients, How to use) |
| titleMedium | Inter | 16 | 600 | 1.5 | Product name on tiles and cart lines |
| priceLarge | Playfair Display | 22 | 700 | 1.27 | Price on Detail, cart Total |
| bodyLarge | Inter | 16 | 400 | 1.5 | Description text |
| bodyMedium | Inter | 14 | 400 | 1.43 | General body, tile price |
| labelLarge | Inter | 14 | 600 | 1.43 | Buttons, chips |
| caption | Inter | 14 | 400 | 1.43 | Brand name, helper text |

Rules:
- **Minimum 14 sp** for all text; no style smaller than 14 sp exists.
- All sizes scale with the system text size (no `textScaler` clamping). Layouts must stay usable at 150%: names wrap to 2+ lines, no fixed-height text containers, Detail content scrolls, cart lines wrap vertically.
- Sentence case for all labels and buttons ("Add to Cart" is the one approved exception as a product term). No all-caps body text.
- Prices always come from integer cents formatted as USD, e.g. $24.50.

---

## 4. Spacing, shape and elevation

- Spacing scale: 4, 8, 12, 16, 24, 32, 48 dp. Screen horizontal padding 16 dp; grid gutter 12 dp; section spacing 24 dp.
- Corner radii: 8 (chips inner elements), 12 (buttons, tiles, images), 16 (cards/sheets), 24 (large image on Detail), 999 (pills, badge).
- Elevation: flat design. Tiles on `surface` over `background` with no or very soft shadow; SnackBar floating.
- Touch targets: every interactive control at least **48x48 dp** (cart icon, chips, tiles, stepper buttons, Remove, Add to Cart, back, state actions).

---

## 5. Logo usage

The business supplies the logo (not yet received; see approval record).

Required asset delivery:
- Preferred: SVG (single-colour and full-colour). Otherwise PNG with transparent background at 1x/2x/3x, minimum 3x height 84 px.
- A light-background version and a dark-background (reversed) version, or a single-colour version that the app can tint with `onSurface`.

Placement in the app:
- **AppLogoBar** on Browse and Cart: logo centred (iOS and Android alike, for brand consistency) in the app bar, height **28 dp**, width scaled proportionally, max width 160 dp.
- Product Detail shows a back control plus the cart button instead of the logo (keeps focus on the product).
- Clear space: at least 8 dp around the logo; nothing overlaps it.
- Contrast: logo against the app bar `surface` must reach at least 3:1 (graphical object); use the reversed/tinted version in dark theme.
- Accessibility: semantic label **"beauty-mvp logo"** (to be replaced by the brand name once the business confirms it).
- Do not: stretch, recolour outside the supplied versions, add effects/shadows, or place it on a photo.
- App icon (launcher): derived from the logo mark on `primary` or `background`; to be produced once the logo is received.

---

## 6. Imagery guidelines

Product photos are supplied by the business and bundled with the app.

| Rule | Guideline |
|---|---|
| Aspect ratio | 1:1 square for every product (tiles, detail, cart thumbnails all crop-free) |
| Source resolution | At least 1200x1200 px supplied |
| In-app export | 800x800 px, WebP (or JPEG quality 80), target at most 150 KB per image, for fast loading and smooth scrolling |
| Background | Clean, seamless white or warm off-white (close to #FFFFFF / #FFFBF9); no busy scenes |
| Composition | Product centred, upright, fully visible, about 10% padding on all sides, consistent camera angle and scale across the catalog |
| Lighting | Soft, even, natural-looking light; realistic colour (especially for makeup shades); subtle natural shadow allowed |
| Content | No text overlays, price stickers, watermarks, promo badges or models' faces in the demo set |
| File naming | `<productId>.webp` matching the catalog JSON `image` path |
| Alt text | Every image has `image.alt` in the catalog JSON: short, factual, max 125 characters, e.g. "Rose hydrating serum in a 30 ml glass dropper bottle". Used as the screen-reader label |
| Missing / failed image | The `placeholder` token block with a neutral image icon is shown; name, brand and price stay visible; placeholder is excluded from screen-reader semantics |

---

## 7. Component styling summary

| Component | Styling |
|---|---|
| PrimaryButton | Full width, min height 48 dp, radius 12, `primary` fill, `onPrimary` labelLarge text |
| CategoryChipRow | Chips min 48 dp high; unselected: `surface` fill, `outline` border, `onSurface` text; selected: `primaryContainer` fill, `primary` border, check icon, `onPrimaryContainer` text |
| ProductTile | `surface` card, radius 12, 1:1 image, name titleMedium (max 2 lines), brand caption `onSurfaceVariant`, price bodyMedium `onSurface` |
| CartBadgeButton | 48x48 dp, badge pill radius 999 `badge`/`onBadge`, hidden at 0 |
| QuantitySelector | 48x48 dp outlined buttons (`outline`), centred value titleMedium |
| AppSnackBar | Floating, `inverseSurface` / `onInverseSurface`, radius 12 |
| Empty / Error states | Centred icon (`onSurfaceVariant` / `error`), headlineMedium title, bodyMedium message, PrimaryButton action |
| Skeleton / placeholder | `skeleton` / `placeholder` tokens, radius 12, decorative only |

---

## 8. Accessibility checklist (acceptance for US-006)

- [ ] Body text at least 14 sp on all screens.
- [ ] Text/background contrast at least 4.5:1 in light and dark themes (section 2.1).
- [ ] Interactive controls at least 48x48 dp.
- [ ] Images labelled from `image.alt`; logo labelled; icon buttons labelled ("Cart, N items", "Decrease quantity of <name>", "Increase quantity of <name>", "Remove <name>", "Back").
- [ ] Browse, Product Detail and Cart usable at 150% system text size with no overlap, clipping or overflow.
- [ ] Approved colours, typography and logo applied consistently on iOS and Android.

---

## 9. What approval covers

Approval of this guide confirms: the colour palette (section 2), typefaces and type scale (section 3), logo placement rules (section 5) and imagery guidelines (section 6). Changes after approval go through a new version of this document and a new sign-off.
