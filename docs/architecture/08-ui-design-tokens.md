# Ameen Retail — UI design tokens (v1)

**Status:** Binding for frontend visual design. Layout, screen wireframes, and component inventory are **not** specified here.

**Source:** Product theme from Stitch / Material 3 custom theme.

If this file conflicts with implementation CSS, **this file and `00-frozen-decisions.md` win**.

---

## Locked theme

| Token | Value |
|---|---|
| Seed / brand primary | `#147D78` |
| Color theme | Custom (Material 3 tonal palettes derived from the seed) |
| Palettes | Primary, Secondary, Tertiary, Neutral |
| Headline font | Inter |
| Body font | Inter |
| Label font | Inter |
| Corner radius | Stitch `ROUND_TWELVE` — **12px** default |

Do not swap the seed for a different teal, do not mix a second display font, and do not use pill-radius (`ROUND_FULL`) or sharp (`4px`) as the default.

---

## Color

Use **semantic tokens**, not raw hex in components.

Brand actions (primary buttons, key links, focus rings, POS pay) use the **seed** `#147D78` so the UI matches the chosen swatch. Surfaces, containers, and on-colors use the Material 3 tonal-spot scheme generated from that seed.

### Light (default)

Retail back office and POS ship in **light** mode first.

| Role | Hex | Use |
|---|---|---|
| `primary` | `#147D78` | Filled buttons, active nav, key accents |
| `on-primary` | `#FFFFFF` | Text/icons on primary |
| `primary-container` | `#A8F0EA` | Tinted chips, selected rows, soft highlights |
| `on-primary-container` | `#015C58` | Text on primary-container |
| `primary-dim` | `#045D59` | Hover on filled primary; small text on light surfaces when `#147D78` fails contrast |
| `secondary` | `#4A6462` | Secondary buttons, supporting UI |
| `on-secondary` | `#FFFFFF` | Text on secondary |
| `secondary-container` | `#CCE8E5` | Secondary tints |
| `on-secondary-container` | `#3D5654` | Text on secondary-container |
| `tertiary` | `#37647B` | Optional accent (charts, tags) — not a second brand |
| `on-tertiary` | `#FFFFFF` | Text on tertiary |
| `tertiary-container` | `#B5E3FD` | Tertiary tints |
| `on-tertiary-container` | `#245369` | Text on tertiary-container |
| `error` | `#A83836` | Destructive, validation |
| `on-error` | `#FFFFFF` | Text on error |
| `error-container` | `#FA746F` | Error banners (use `on-error-container` for text) |
| `on-error-container` | `#6E0A12` | Text on error-container |
| `background` / `surface` | `#F6FAF9` | Page canvas |
| `on-background` / `on-surface` | `#2A3433` | Body text |
| `on-surface-variant` | `#566160` | Secondary text, captions |
| `surface-container-lowest` | `#FFFFFF` | Cards, dialogs, POS cart panel |
| `surface-container-low` | `#EEF5F3` | Subtle wells |
| `surface-container` | `#E7F0EE` | Nested panels, table header |
| `surface-container-high` | `#E1EAE8` | Elevated nested |
| `surface-container-highest` | `#D9E5E3` | Highest nested |
| `outline` | `#727D7B` | Borders on inputs, dividers that must be visible |
| `outline-variant` | `#A9B4B2` | Hairline dividers |
| `inverse-surface` | `#0A0F0F` | Snackbars, inverse chips |
| `inverse-on-surface` | `#DCE8E6` | Text on inverse-surface |
| `inverse-primary` | `#9BD0CC` | Accent on inverse-surface |
| `scrim` | `#000000` | Modal overlay (use ~40–50% opacity) |

### Dark (supported, not default)

| Role | Hex |
|---|---|
| `primary` | `#9BD0CC` |
| `on-primary` | `#0E4845` |
| `primary-container` | `#265B57` |
| `on-primary-container` | `#B8EDE9` |
| `secondary` | `#B0CCC9` |
| `on-secondary` | `#2C4543` |
| `secondary-container` | `#27403E` |
| `on-secondary-container` | `#A9C5C2` |
| `tertiary` | `#D5EFFF` |
| `on-tertiary` | `#2E5C72` |
| `tertiary-container` | `#1A4154` |
| `on-tertiary-container` | `#B5E3FD` |
| `error` | `#FA746F` |
| `on-error` | `#490006` |
| `error-container` | `#871F21` |
| `on-error-container` | `#FF9993` |
| `background` / `surface` | `#0A0F0F` |
| `on-background` / `on-surface` | `#DCE8E6` |
| `on-surface-variant` | `#A2ADAC` |
| `surface-container-lowest` | `#000000` |
| `surface-container-low` | `#0E1514` |
| `surface-container` | `#131B1A` |
| `surface-container-high` | `#192120` |
| `surface-container-highest` | `#1D2827` |
| `outline` | `#6D7876` |
| `outline-variant` | `#3F4A49` |
| `inverse-surface` | `#F6FAF9` |
| `inverse-on-surface` | `#2A3433` |
| `inverse-primary` | `#147D78` |

Filled brand buttons in **dark** mode may keep seed `#147D78` with `on-primary` `#FFFFFF` when the control must match the logo; otherwise use the table `primary` / `on-primary` pair for contrast on dark surfaces.

---

## Typography

Load **Inter** from a first-party or Google Fonts stylesheet. One family for all three roles.

| Role | CSS | Use |
|---|---|---|
| Headline | `Inter`, 600–700 | Page titles, POS total, dialog titles |
| Body | `Inter`, 400–500 | Paragraphs, table cells, form values |
| Label | `Inter`, 500–600 | Buttons, tabs, input labels, chips, nav |

Stack: `"Inter", ui-sans-serif, system-ui, sans-serif`. Tabular figures for money and quantities (`font-variant-numeric: tabular-nums`).

### Scale (rem @ 16px root)

| Token | Size | Line height | Weight | Role |
|---|---|---|---|---|
| `display` | 2.25rem (36px) | 1.2 | 700 | POS total, rare hero |
| `headline-lg` | 1.75rem (28px) | 1.25 | 600 | Screen title |
| `headline-md` | 1.375rem (22px) | 1.3 | 600 | Section title |
| `headline-sm` | 1.125rem (18px) | 1.35 | 600 | Card title |
| `body-lg` | 1rem (16px) | 1.5 | 400 | Default body |
| `body-md` | 0.875rem (14px) | 1.45 | 400 | Compact tables, POS list |
| `body-sm` | 0.75rem (12px) | 1.4 | 400 | Helper, timestamps |
| `label-lg` | 0.875rem (14px) | 1.25 | 600 | Buttons, tabs |
| `label-md` | 0.75rem (12px) | 1.25 | 500 | Input labels, chips |
| `label-sm` | 0.6875rem (11px) | 1.2 | 500 | Badges, overlines |

Do not use Inter for monospace document numbers if a dedicated mono is added later; until then Inter + tabular nums is enough.

---

## Shape (`ROUND_TWELVE`)

Default control radius is **12px**. Inner elements may step down; never default to 0 or full pill except avatars, switches, and explicit pills (status chips).

| Token | Value | Use |
|---|---|---|
| `radius-xs` | 4px | Checkboxes, tiny indicators |
| `radius-sm` | 8px | Nested chips inside 12px cards, inner inputs |
| `radius-md` | **12px** | Buttons, text fields, selects, cards, menus, table wrappers |
| `radius-lg` | 16px | Dialogs, large POS panels, sheets |
| `radius-full` | 9999px | Avatars, switches, count badges only |

Focus rings: 2px solid `primary`, offset 2px. Do not use a second radius language (e.g. 6px “bootstrap” defaults).

---

## Implementation rules

- Put tokens in CSS custom properties (see `tokens.css` in this folder). Components consume variables only.
- Do not hard-code `#147D78` outside the token file.
- Motion: 150ms ease-out for hover/focus; 200ms for panels. No decorative animation on POS pay.
- Elevation: prefer surface-container steps over heavy drop shadows. If a shadow is needed: `0 1px 2px rgb(10 15 15 / 8%), 0 4px 12px rgb(10 15 15 / 6%)`.
- This document does **not** define screen layouts. Navigation and RBAC screens stay in document 07.

Copy-paste variables: [`tokens.css`](./tokens.css).
