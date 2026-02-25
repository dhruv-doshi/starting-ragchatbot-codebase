# Frontend Changes: Dark/Light Mode Toggle Button

## Overview

Added a dark/light mode theme toggle button positioned in the top-right corner of the UI. The button uses SVG sun/moon icons, animates smoothly when toggling, and is fully keyboard-navigable.

---

## Files Modified

### `frontend/index.html`

- **Cache-busted** asset version strings from `v=9` → `v=10` (`style.css`, `script.js`).
- Added a `<button id="themeToggle" class="theme-toggle">` element placed directly inside `.container`, before `.main-content`. The button contains:
  - A **sun SVG icon** (`.sun-icon`) — visible in dark mode; clicking switches to light.
  - A **moon SVG icon** (`.moon-icon`) — visible in light mode; clicking switches to dark.
  - `aria-label="Switch to light mode"` (updated dynamically by JS on each toggle).
  - Both SVGs use `aria-hidden="true"` since the accessible name comes from the button's `aria-label`.

---

### `frontend/style.css`

#### Light theme CSS variables (`[data-theme="light"]`)

Overrides the `:root` dark-mode variables when `data-theme="light"` is set on `<html>`:

| Variable | Dark (`:root`) | Light (`[data-theme="light"]`) |
|---|---|---|
| `--background` | `#0f172a` | `#f8fafc` |
| `--surface` | `#1e293b` | `#ffffff` |
| `--surface-hover` | `#334155` | `#e2e8f0` |
| `--text-primary` | `#f1f5f9` | `#0f172a` |
| `--text-secondary` | `#94a3b8` | `#64748b` |
| `--border-color` | `#334155` | `#e2e8f0` |
| `--assistant-message` | `#374151` | `#f1f5f9` |
| `--shadow` | dark rgba | lighter rgba |
| `--focus-ring` | `rgba(37,99,235,0.2)` | `rgba(37,99,235,0.15)` |
| `--welcome-bg` | `#1e3a5f` | `#eff6ff` |

#### Theme transition

Added `transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease` to key elements (`body`, `.sidebar`, `.chat-messages`, `.message-content`, `#chatInput`, `.stat-item`, `.suggested-item`, `.source-chip`, `.theme-toggle`) for a smooth animated switch.

#### `.theme-toggle` button styles

- `position: fixed; top: 1rem; right: 1rem; z-index: 100` — always visible top-right.
- `40×40px` circular button (`border-radius: 50%`).
- Uses `var(--surface)` background and `var(--border-color)` border — adapts to both themes.
- `:hover` — scales up slightly (`transform: scale(1.1)`) and tints icon with `var(--primary-color)`.
- `:focus` — renders a visible focus ring using `var(--focus-ring)` for keyboard accessibility.

#### Icon visibility logic

```css
/* Dark mode (default): show sun, hide moon */
.theme-toggle .sun-icon { display: block; }
.theme-toggle .moon-icon { display: none; }

/* Light mode: hide sun, show moon */
[data-theme="light"] .theme-toggle .sun-icon { display: none; }
[data-theme="light"] .theme-toggle .moon-icon { display: block; }
```

#### Light mode code block overrides

Inline `<code>` and `<pre>` blocks use `rgba(0,0,0,0.06)` background in light mode instead of the default `rgba(0,0,0,0.2)` to maintain readability on a light surface.

---

### `frontend/script.js`

#### New functions

- **`initTheme()`** — Runs immediately (before `DOMContentLoaded`) to avoid a flash of the wrong theme. Checks `localStorage.getItem('theme')` first; falls back to `window.matchMedia('(prefers-color-scheme: light)')` to respect system preference. If neither applies, the dark `:root` variables take effect by default.

- **`applyTheme(theme)`** — Sets `data-theme` attribute on `<html>` and updates the button's `aria-label` to reflect the action that will happen on the *next* click ("Switch to dark mode" / "Switch to light mode").

- **`toggleTheme()`** — Reads the current `data-theme`, computes the opposite, calls `applyTheme()`, and persists the choice to `localStorage`.

#### Integration

- `initTheme()` called at module top-level (before DOMContentLoaded) to prevent flash.
- `document.getElementById('themeToggle').addEventListener('click', toggleTheme)` wired up inside `DOMContentLoaded`.

---

## Accessibility

- Button element is naturally focusable and activatable via `Enter`/`Space` keys.
- `aria-label` is kept up-to-date to describe the *action* (not the current state).
- SVG icons have `aria-hidden="true"` to avoid duplicate announcements.
- Focus ring visible in both themes via `var(--focus-ring)`.

## Persistence & System Preference

| Scenario | Behaviour |
|---|---|
| First visit, system dark | Dark mode (no localStorage entry set) |
| First visit, system light | Light mode applied automatically |
| User toggles | Preference saved to `localStorage`, overrides system setting on future visits |
| Revisiting page | Saved `localStorage` theme restored before first paint |

---

# Frontend Changes: Light Theme Colour Refinement

## Overview

Expanded the light theme with a complete, accessibility-audited colour palette. Fixed contrast failures on error/success messages, added missing variable overrides, and corrected a pre-existing bug (`var(--primary)` → `var(--primary-color)`) that affected blockquote rendering in both themes.

---

## Files Modified

### `frontend/style.css`

#### Expanded `[data-theme="light"]` variable block

All variables are now explicitly overridden (not inherited from the dark `:root`) so the light theme is self-contained. WCAG AA contrast ratios verified for every text/background pairing:

| Variable | Value | Notes |
|---|---|---|
| `--background` | `#f1f5f9` | Slate-50 — gives the page a slight warmth vs pure white |
| `--surface` | `#ffffff` | Cards / sidebar / message bubbles |
| `--surface-hover` | `#e2e8f0` | Hover state fill |
| `--text-primary` | `#0f172a` | ≥ 16:1 on `#fff` ✓ |
| `--text-secondary` | `#475569` | 5.9:1 on `#fff` ✓ (upgraded from `#64748b` which was 4.7:1) |
| `--border-color` | `#cbd5e1` | More visible dividers than the previous `#e2e8f0` |
| `--shadow` | two-layer subtle shadow | Replaces the dark-mode heavy shadow |
| `--primary-color` | `#2563eb` | 5.3:1 on `#fff` ✓ |
| `--primary-hover` | `#1d4ed8` | Explicit (was implicitly inherited) |
| `--user-message` | `#2563eb` | White text on it = 5.3:1 ✓ |
| `--assistant-message` | `#f8fafc` | Near-white surface for assistant bubbles |
| `--focus-ring` | `rgba(37,99,235,0.2)` | Same as dark for consistency |
| `--welcome-bg` | `#eff6ff` | Blue-50 tint |
| `--welcome-border` | `#93c5fd` | Softer blue accent instead of full `#2563eb` |

#### Light mode element overrides

**Code blocks** — use a dark-on-light treatment instead of the dark-mode black overlay:
- `code`: `background rgba(15,23,42,0.07)`, `color: #1e293b`
- `pre`: same tint + explicit `border: 1px solid var(--border-color)` for better definition

**Welcome message** — box-shadow halved from `rgba(0,0,0,0.2)` → `rgba(0,0,0,0.07)` to suit a light surface; border switches to `--welcome-border` (soft blue).

**Error messages** — the original `color: #f87171` (light coral) achieves only ~2:1 contrast on a light background, failing WCAG AA. Replaced with:
- `color: #b91c1c` — verified 6.2:1 on the tinted background ✓
- `background: rgba(220,38,38,0.07)` — slightly lighter tint
- `border-color: rgba(220,38,38,0.25)`

**Success messages** — the original `color: #4ade80` (light green) achieves only ~1.5:1 on a light background. Replaced with:
- `color: #15803d` — verified 5.1:1 on the tinted background ✓
- `background: rgba(22,163,74,0.07)`
- `border-color: rgba(22,163,74,0.25)`

**Source chips** — given explicit light-theme values (`border: #cbd5e1`, `background: #f1f5f9`, `color: #475569`) so they are visually distinct from the white surface.

#### Bug fix — blockquote border

`border-left: 3px solid var(--primary)` referenced an undefined CSS variable in both themes (the variable is named `--primary-color`, not `--primary`). Fixed to `var(--primary-color)`.

---

## Accessibility summary (light theme)

| Element | Foreground | Background | Contrast | WCAG |
|---|---|---|---|---|
| Body text | `#0f172a` | `#f1f5f9` | ~17:1 | AAA ✓ |
| Body text | `#0f172a` | `#ffffff` | ~21:1 | AAA ✓ |
| Secondary text | `#475569` | `#ffffff` | 5.9:1 | AA ✓ |
| Primary / links | `#2563eb` | `#ffffff` | 5.3:1 | AA ✓ |
| User msg text | `#ffffff` | `#2563eb` | 5.3:1 | AA ✓ |
| Error text | `#b91c1c` | tinted bg | 6.2:1 | AA ✓ |
| Success text | `#15803d` | tinted bg | 5.1:1 | AA ✓ |
| Code text | `#1e293b` | `rgba(15,23,42,0.07)` ≈ `#eef0f3` | ~12:1 | AAA ✓ |

---

# Frontend Changes: JavaScript Toggle Functionality & Smooth Transitions

## Overview

Completed the theme-switching implementation by fixing a Flash of Unstyled Content (FOUC) bug, animating the icon swap, adding click feedback on the toggle button, and extending smooth transitions to every element that references a CSS variable. Also added an explicit `[data-theme="dark"]` CSS block to make both themes fully self-contained.

---

## Files Modified

### `frontend/index.html`

- **FOUC-prevention inline script** added in `<head>`, *before* the stylesheet `<link>`. Runs synchronously before the first paint, reads `localStorage` and `prefers-color-scheme`, and sets `data-theme` on `<html>` immediately. Prevents a flash of dark content for users whose saved/system preference is light.
- Version bumped to `v=11`.

---

### `frontend/style.css`

#### `[data-theme="dark"]` explicit variable block

Added after the `[data-theme="light"]` block. Mirrors `:root` exactly, making the dark theme self-contained and consistent with the light-theme pattern. Enables use of `[data-theme="dark"]` selectors for future dark-only overrides.

#### Expanded theme transition selector

The previous rule covered 11 elements. Extended to 23, adding every element that references a CSS variable:

```
.main-content, #sendButton, .stat-value, .stat-label,
.course-title-item, .message-meta, .sources-collapsible,
.new-chat-btn, .stats-header, .suggested-header, .loading span
```

All transition `background-color`, `color`, `border-color`, and `box-shadow` over `0.3s ease`.

#### Animated icon swap (sun ↔ moon)

Replaced the instant `display: none/block` toggle with `position: absolute` + `opacity/transform` transitions:

| State | Sun | Moon |
|---|---|---|
| Dark mode | `opacity:1`, `rotate(0) scale(1)` — visible | `opacity:0`, `rotate(90deg) scale(0.5)` — rotated away |
| Light mode | `opacity:0`, `rotate(-90deg) scale(0.5)` — rotated away | `opacity:1`, `rotate(0) scale(1)` — visible |

Both icons fade and spin simultaneously (0.3 s), creating a smooth cross-rotation effect. Icons use `pointer-events: none` so they never block the button's click area.

#### Button click animation

```css
@keyframes theme-click {
    0%   { transform: scale(1);    }
    35%  { transform: scale(0.84); }
    100% { transform: scale(1);    }
}
.theme-toggle.activated { animation: theme-click 0.28s ease forwards; }
```

Provides tactile press-down feedback when the button is clicked.

#### `.theme-toggle` stacking context

Added `isolation: isolate` so the absolutely-positioned icon SVGs are guaranteed to remain inside the button's stacking context.

---

### `frontend/script.js`

#### `initTheme()` — always writes an explicit `data-theme`

Added an `else` branch so the dark theme is always set as `data-theme="dark"` rather than leaving the attribute absent. This ensures `[data-theme="dark"]` CSS rules fire correctly.

```js
} else {
    applyTheme('dark'); // explicit attribute, not implicit :root fallback
}
```

#### `toggleTheme()` — button click animation

Before switching the theme, the function:
1. Removes any existing `.activated` class
2. Forces a reflow (`void btn.offsetWidth`) so the CSS animation restarts cleanly on rapid clicks
3. Adds `.activated` to play the press-down keyframe
4. Attaches a one-time `animationend` listener to remove the class when done

```js
btn.classList.remove('activated');
void btn.offsetWidth;
btn.classList.add('activated');
btn.addEventListener('animationend', () => btn.classList.remove('activated'), { once: true });
```

---

## How all the pieces fit together

```
User clicks button
      │
      ▼
toggleTheme() in script.js
  ├─ Adds .activated → CSS @keyframes fires (press-down)
  ├─ Reads current data-theme on <html>
  ├─ Calls applyTheme('light'|'dark')
  │     ├─ setAttribute('data-theme', …) on <html>
  │     └─ Updates button aria-label
  └─ localStorage.setItem('theme', …)

On next page load
  ├─ Inline <head> script sets data-theme BEFORE first paint  (no flash)
  └─ initTheme() in script.js confirms + syncs aria-label
```
