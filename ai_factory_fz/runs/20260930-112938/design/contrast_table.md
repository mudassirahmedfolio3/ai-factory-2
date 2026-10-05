# Contrast workings for the proposed palette (WI-001)

Method: WCAG 2.1. For each sRGB channel c = value/255, linear = c/12.92 if c <= 0.04045, else ((c + 0.055)/1.055)^2.4.
Relative luminance L = 0.2126 R + 0.7152 G + 0.0722 B. Contrast = (L_lighter + 0.05) / (L_darker + 0.05).
Ratios are rounded down to one decimal. Requirement: text at least 4.5:1, non-text boundaries at least 3:1.
These values were calculated by hand for the proposal. The automated contrast unit test to be added to the Flutter theme in WI-009 is the authoritative check and must assert every pair below.

## Relative luminance per token

| Token | Light hex | L (light) | Dark hex | L (dark) |
|---|---|---|---|---|
| primary / badge | #8C3B4F | 0.0927 | #F2B8C6 | 0.5724 |
| onPrimary / onBadge | #FFFFFF | 1.0000 | #4A1425 | 0.0209 |
| primaryContainer | #F8E1E7 | 0.7958 | #5E2537 | 0.0398 |
| onPrimaryContainer | #3F1220 | 0.0159 | #FFD9E2 | 0.7638 |
| background | #FFFBF9 | 0.9709 | #1A1416 | 0.0078 |
| surface | #FFFFFF | 1.0000 | #251D20 | 0.0138 |
| onSurface | #211A1C | 0.0115 | #F5EDEF | 0.8658 |
| onSurfaceVariant | #6B5C61 | 0.1164 | #C9BCC0 | 0.5220 |
| outline | #857378 | 0.1860 | #9A8B90 | 0.2735 |
| error | #B3261E | 0.1106 | #F2B8B5 | 0.5650 |
| onError | #FFFFFF | 1.0000 | #601410 | 0.0303 |
| inverseSurface | #2E2427 | 0.0199 | #F0E4E7 | 0.7989 |
| onInverseSurface | #F8EEF0 | 0.8777 | #2E2427 | 0.0199 |

## Pair results

| Pair (foreground on background) | Light | Dark | Required | Result |
|---|---|---|---|---|
| onSurface on background | 16.6:1 | 15.8:1 | 4.5:1 | Pass |
| onSurface on surface | 17.0:1 | 14.3:1 | 4.5:1 | Pass |
| onSurfaceVariant on background | 6.1:1 | 9.9:1 | 4.5:1 | Pass |
| onSurfaceVariant on surface | 6.3:1 | 8.9:1 | 4.5:1 | Pass |
| onPrimary on primary | 7.3:1 | 8.7:1 | 4.5:1 | Pass |
| primary on background (text actions) | 7.1:1 | 10.7:1 | 4.5:1 | Pass |
| primary on surface | 7.3:1 | 9.7:1 | 4.5:1 | Pass |
| onPrimaryContainer on primaryContainer | 12.8:1 | 9.0:1 | 4.5:1 | Pass |
| onError on error | 6.5:1 | 7.6:1 | 4.5:1 | Pass |
| error on surface (error icon/text) | 6.5:1 | 9.6:1 | 4.5:1 | Pass |
| onInverseSurface on inverseSurface | 13.2:1 | 12.1:1 | 4.5:1 | Pass |
| onBadge on badge | 7.3:1 | 8.7:1 | 4.5:1 | Pass |
| outline on background | 4.3:1 | 5.6:1 | 3:1 | Pass |
| outline on surface | 4.4:1 | 5.0:1 | 3:1 | Pass |

All required pairs pass in both themes.
