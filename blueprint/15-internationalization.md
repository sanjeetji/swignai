# 15 — Internationalization (i18n)

> 🧭 **Status:** 📝 Spec · **Tier:** ③ Advanced → **Target: 🏆 Best-in-class** · **Phase 1** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** The platform must support **multiple languages — English and Hindi at launch — and be architected so more languages can be added without code changes.** This is distinct from the LLM Hinglish *stock explanations* (doc 03): that's AI-generated content; this doc is about the **entire UI** — buttons, labels, messages, dates, numbers, currency — being translatable. Admin sets the default language; users override their own (doc 16).

---

## 1. Scope — what gets localized

- **All UI strings** — navigation, buttons, labels, form fields, validation messages, empty/error states, emails, notifications.
- **Formatting** — dates/times (IST, locale format), numbers, and **₹ currency** (Indian grouping: 1,00,000 not 100,000).
- **SEO** — `hreflang` tags, localized metadata on public pages (doc 08).
- **Not** the AI stock explanations — those are generated per-locale by the LLM/templates (doc 03). i18n covers the *chrome*; the LLM covers the *content*.

---

## 2. Library & architecture

**Library:** **next-intl** (App Router-native, SSR-friendly, TypeScript-typed messages).

**Locale routing:** path-prefix strategy — `/{locale}/...`:
```
/en/dashboard      /hi/dashboard
/en/stocks/HAL     /hi/stocks/HAL
```
- Default locale resolved from: **user preference → platform default (admin) → Accept-Language header → fallback `en`.**
- Middleware (doc 08) handles locale detection + redirect, alongside auth.
- `hreflang` + canonical tags emitted for SEO so Google serves the right language version (doc 08).

**Message files (translation catalogs):**
```
apps/web/locales/
├── en/
│   ├── common.json     # nav, buttons, generic
│   ├── dashboard.json
│   ├── admin.json
│   ├── auth.json
│   └── errors.json
├── hi/
│   ├── common.json
│   └── ...
└── index.ts            # locale registry (add a locale here = available platform-wide)
```
**Adding a language = add a folder + register it.** No component changes. The registry feeds the admin language options (doc 16) and the user/locale switcher.

---

## 3. Usage rules (so nothing is hardcoded)

- **No hardcoded user-facing strings in components — ever.** Every string goes through the i18n function: `t('dashboard.picks.title')`. This is enforced in review/lint (doc 11 includes an i18n-coverage check).
- **Namespaced keys** by feature (`common`, `dashboard`, `admin`, …) to keep catalogs manageable.
- **Interpolation & pluralization** via next-intl (`{count} trades`, plural rules) — never string-concatenate translations.
- **Rich text** (bold, links inside sentences) via next-intl rich formatting, not HTML string splicing.

---

## 4. Formatting (locale-aware)

| Type | Approach |
|---|---|
| **Currency ₹** | `Intl.NumberFormat('en-IN' / 'hi-IN', {style:'currency', currency:'INR'})` → Indian lakh/crore grouping |
| **Numbers** | locale-aware grouping; consider lakh/crore display for large values (₹1.2 Cr) |
| **Dates/times** | locale + **IST** timezone; relative times ("2 din pehle") localized |
| **Percentages / R-multiples** | locale-formatted, sign-aware |

Centralize formatters in `lib/format.ts` so currency/number/date rendering is consistent and locale-driven everywhere (KPIs, charts, tables).

---

## 5. Fonts for scripts

- Hindi (Devanagari) needs a capable font — **Noto Sans Devanagari** / **Hind** — coordinated with the design system fonts (doc 14). The selected UI font must render the active locale's script correctly; fall back to a Devanagari-capable family when the locale needs it.
- Verify line-height/letter-spacing for Devanagari (taller glyphs) so layouts don't break between languages.

---

## 6. Translation workflow

- **Source of truth:** `en` catalogs (developers write these).
- **Hindi:** human-translated (quality matters for trust in a finance product) — not raw machine translation; can be LLM-assisted then human-reviewed.
- **Missing-key handling:** fall back to `en` (never show a raw key to a user); log missing keys in dev/CI so gaps are caught (doc 11).
- **Optional later:** a translation-management tab in admin or a service (e.g. Crowdin/Tolgee) when locale count grows.

---

## 7. RTL readiness (future-proofing)

- English + Hindi are both LTR, so RTL isn't needed now — but **use logical CSS properties** (`margin-inline-start`, not `margin-left`) and direction-agnostic layouts so adding an RTL language (e.g. Urdu) later is a config change, not a rewrite. The design system (doc 14) follows this.

---

## 8. Backend & data localization

- **API responses** stay locale-neutral (raw data/enums); the **frontend localizes** display. Enums like trade status return codes (`hit_target`), and the UI maps them to localized labels.
- **Server-generated content** that must be localized (emails, notifications, doc 18) takes a `locale` param and renders from server-side catalogs.
- **LLM explanations** (doc 03) are generated **per target language** (Hinglish for HI audience; clean English for EN), cached per (pick, locale).
- `user_preferences.locale` and `platform_settings.default_locale` (doc 06) drive resolution.

---

## 9. Phase evolution

| Phase | Deliverable |
|---|---|
| 1 | next-intl wired, locale routing + middleware, **EN + HI** full UI catalogs, ₹/date formatting, locale switcher, admin default + user override (doc 16) |
| 2 | Localized emails/notifications/alerts; localized SEO (`hreflang`) at scale; refine Hindi copy from user feedback |
| 3 | Add more Indian languages (e.g. Marathi, Tamil, Gujarati, Bengali) — each via the registry; optional TMS |
| Future | RTL support if needed; per-region content; locale-specific onboarding |

---

*Next: [`16-admin-control-panel.md`](./16-admin-control-panel.md) — the Super Admin control plane that sets platform defaults for theme, font, and language.*
