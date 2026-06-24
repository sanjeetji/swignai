# 14 — Design System & UI/UX

> 🧭 **Status:** 📝 Spec · **Tier:** 🏆 Best-in-class (design) → **Target: 🏆 Best-in-class** · **Phase 1** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** The platform must look cool, modern, and professional — and be fully responsive on desktop and mobile **from day one**, not retrofitted. This doc defines the design system: curated theme presets, light/dark/system modes, multiple fonts, animations, charts/graphs, the responsive strategy, accessibility, and the performance budget that keeps "cool" from hurting SEO. All theming is driven by real settings from the backend (doc 16) — **no hardcoded colors/strings in components.**

---

## 1. Principles

- **Responsive-first, mobile-first.** ~85% of Indian traders are on Android phones. Design every screen mobile-up; desktop is the enhancement. No "we'll fix mobile later."
- **Token-driven.** All color/spacing/typography flow from **design tokens** (CSS variables), never hardcoded in components. Themes swap tokens, not components. This is what makes admin theming (doc 16) and dark mode work everywhere instantly.
- **Cool but fast.** Animations and charts must respect a **performance budget** (§7) — Core Web Vitals drive SEO (doc 08), so motion never blocks interaction or tanks LCP.
- **Accessible by default.** WCAG 2.1 AA: contrast, keyboard nav, focus states, reduced-motion, screen-reader labels.
- **Everything data-driven.** Theme/font/locale come from backend settings + user prefs (docs 16, 06). No static defaults baked into the bundle beyond a safe fallback.

---

## 2. Theming architecture

**Library:** **next-themes** for light/dark/system + theme-preset switching, on top of **Tailwind CSS** with CSS-variable design tokens. shadcn/ui components consume the tokens, so a theme change re-skins the whole app with zero per-component work.

**Three independent axes (all user-overridable; admin sets defaults — doc 16):**
1. **Mode:** `light` / `dark` / `system` (follows OS).
2. **Color preset:** one of **4–6 curated schemes** (e.g. *Default Blue*, *Emerald*, *Violet*, *Slate*, *Amber*, *Rose*). Each defines token values for both light and dark.
3. **Font:** one of several curated families (e.g. *Inter*, *Manrope*, *Plus Jakarta Sans*, plus a Devanagari-capable font like *Noto Sans / Hind* for Hindi — see doc 15).

**Token set (CSS variables):**
```
--background, --foreground, --card, --popover,
--primary, --primary-foreground, --secondary, --accent,
--muted, --border, --input, --ring,
--success (gains), --destructive (losses), --warning,
--radius, --font-sans, --font-display
```
Presets are stored in the DB (`theme_presets`, doc 06) and served by the backend — so new presets can be added without a redeploy.

**Resolution order (who wins):**
```
user override (if set & not admin-locked)  →  platform default (admin)  →  safe built-in fallback
```
Admin can **lock** any axis to force it platform-wide (doc 16). The resolved theme is applied via a `ThemeProvider` that reads platform settings (SSR) + user prefs and sets the token variables; **no flash of unstyled/wrong theme** (set initial theme on the server / via a pre-hydration script).

**Financial color semantics:** gains/losses use `--success`/`--destructive`, but **never rely on color alone** (a11y) — pair with +/− signs and arrows. Indian convention is configurable (some users expect green=up; keep it standard but tokenized).

---

## 3. Component library

- **shadcn/ui + Tailwind** (+ cva, tailwind-merge, tw-animate-css, lucide icons) as the base — owned, fully themeable via tokens. **sonner** for toasts. *(All confirmed from OmniMark — reuse `packages/ui`; see OMNIMARK-REUSE.)*
- **TanStack Table** for data grids; **@tremor/react** + **Recharts** for analytics widgets; **TipTap** for rich text + **@hello-pangea/dnd** for drag-reorder (CMS, doc 21); **leaflet** for the admin session-location map (doc 18).
- **Custom domain components** built on top: `PickCard`, `ScoreBreakdownBar`, `RiskCalculator`, `PortfolioHeatMeter`, `EquityCurve`, `RegimeBanner`, `TrackRecordTable`, `KpiStatCard`, `DataTable` (sortable/filterable — used for admin user tables, doc 18).
- **States are first-class:** every data component ships **loading (skeleton)**, **empty**, and **error** states — because everything is API-driven (no dummy data), these states are real and must be designed, not afterthoughts.

---

## 4. Animations

**Library:** **Framer Motion** (React) for component/page motion; CSS transitions for micro-interactions.

**Where motion is used (purposefully, not decoratively):**
- Page/route transitions (subtle fade/slide).
- Card hover/press, button feedback, list stagger-in.
- Number count-ups for KPIs (P&L, ARR/MRR — doc 20).
- Chart draw-in animations (equity curve sweeping in, bars growing).
- Skeleton shimmer while data loads.
- Toast/notification slide-ins.
- Onboarding micro-celebrations (first paper trade, discipline milestone).

**Rules:**
- Respect **`prefers-reduced-motion`** — disable non-essential motion.
- Motion must never delay interactivity or block content paint.
- Keep durations short (150–300ms typical); avoid janky large-layout animations on mobile.

---

## 5. Charts & graphs

| Use | Library | Notes |
|---|---|---|
| Price candlesticks (stock pages, pick detail) | **TradingView `lightweight-charts`** | Purpose-built, fast, free; overlay EMA/RSI/MACD |
| Equity curve, P&L over time, drawdown | **Recharts** | Smooth, themeable via tokens |
| KPI sparklines (ARR/MRR/usage) | **Recharts** (mini) | In `KpiStatCard` |
| Cohort/funnel/heatmaps (admin analytics, doc 20) | **Recharts / visx** | More complex viz |
| Score breakdown bars (per pick) | Custom (Tailwind/Recharts) | Shows RS/Trend/Volume… |

- All charts read theme tokens (gain/loss colors, grid, font) so they re-skin with the theme.
- Charts must be **responsive** (resize observers) and touch-friendly on mobile.
- Data always from the API (doc 07) — charts never render placeholder/hardcoded series.

---

## 6. Responsive strategy

- **Breakpoints:** Tailwind defaults (`sm 640 / md 768 / lg 1024 / xl 1280 / 2xl 1536`), mobile-first utility usage.
- **Navigation:** bottom tab bar / hamburger drawer on mobile; sidebar on desktop. Admin uses a collapsible sidebar (doc 16).
- **Tables → cards on mobile:** dense admin/data tables (users, trades) collapse to card lists on small screens; never horizontal-scroll a critical table by default.
- **Touch targets** ≥ 44px; thumb-reachable primary actions on mobile.
- **Full-page screens, not dialogs**, for any substantial flow (admin settings, user detail, secrets) — see doc 16/18. Modals only for short confirmations.
- Test on real Android viewport sizes; the dashboard must feel native-quality on a phone before any native app exists (doc 13).

---

## 7. Performance budget (so "cool" doesn't kill SEO)

- Public pages target **good Core Web Vitals** (LCP/INP/CLS) — they're the SEO engine (doc 08).
- **Code-split** heavy chart/animation libs; lazy-load below-the-fold and dashboard-only bundles so marketing pages stay light.
- **No layout shift** from theme/font loading (preload fonts, set theme pre-hydration).
- Animations GPU-friendly (transform/opacity), not layout-thrashing.
- Images via `next/image`; icons via a tree-shaken set (lucide).
- Budget guardrail: marketing route JS kept lean; dashboard can be heavier (authenticated, no SEO need).

---

## 8. Accessibility (WCAG 2.1 AA)

- Contrast checked for **every** theme preset in both light and dark (gain/loss colors included).
- Full keyboard navigation + visible focus rings (`--ring`).
- Semantic HTML + ARIA labels; charts have text/table alternatives.
- `prefers-reduced-motion` honored.
- Forms: labels, error messaging, screen-reader announcements.
- Locale-aware (doc 15): correct `lang` attribute, Devanagari rendering for Hindi.

---

## 9. Where settings come from (no hardcoding)

- **Platform defaults** (default preset/mode/font, available presets/fonts, locks) ← `platform_settings` + `theme_presets` (doc 06) via admin (doc 16).
- **User overrides** ← `user_preferences` (doc 06), set in user settings.
- Frontend reads both at load (SSR for the public default, client for the logged-in user's override) and applies tokens. A safe built-in fallback exists only for first paint before settings resolve.

---

## 10. Phase evolution

| Phase | Deliverable |
|---|---|
| 1 | Token system, 4–6 presets, light/dark/system, 3–4 fonts, core animations, responsive dashboard, charts (price + equity), a11y baseline |
| 2 | Richer animations, more chart types (cohort/funnel for analytics), polish, more presets |
| 3 | **Full custom theme-token editor** for Super Admin (live color picker per token), white-label readiness |
| Future | Per-tier theming, seasonal themes, advanced data-viz, motion design system |

---

*Next: [`15-internationalization.md`](./15-internationalization.md) — multi-language architecture (English + Hindi, extensible).*
