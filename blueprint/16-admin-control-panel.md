# 16 — Super Admin Control Panel

> 🧭 **Status:** 📝 Spec · **Tier:** 🏆 Best-in-class (design) → **Target: 🏆 Best-in-class** · **Phase 1** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** The Super Admin / Platform Owner needs a real control plane to run the platform — set the global look & feel (theme, font, language), manage integrations & secrets (doc 17), govern users & sessions (doc 18), see business analytics (doc 20), and toggle platform behavior — all **backend/API-driven, no hardcoded values.** This doc defines the control-panel structure, the global appearance settings (with the confirmed *admin-default + user-override + optional-lock* model), feature flags, maintenance mode, and the **full-page (never dialog)** navigation pattern.

---

## 1. Access & roles

- The control panel lives at `/admin` (and `/{locale}/admin`), gated by **RBAC** (doc 19): only `super_admin` (and scoped `admin`/`support` roles) can enter; everyone else is redirected. Server-enforced, not just hidden in UI.
- Super Admin = full control. Lower admin roles see a subset per their permissions (doc 19).
- Every privileged action is **audit-logged** (doc 18 §audit).

---

## 2. Navigation model — full-page screens, never dialogs

**Hard rule (per requirement):** every admin section and detail view is a **full page** with its own route, **not a modal/dialog or cramped panel.** A **back button** returns to the previous list/section. Modals are allowed only for short confirmations ("Block this user?").

```
/admin                          → Overview dashboard (KPIs, health) — doc 20
/admin/appearance               → Theme / font / language defaults (this doc §3)
/admin/integrations             → API keys & secrets vault — doc 17
/admin/integrations/[provider]  → Single integration config (full page)
/admin/users                    → User list (search/filter/bulk) — doc 18
/admin/users/[id]               → User detail: sessions, devices, activity — doc 18 (full page)
/admin/sessions                 → Active sessions across platform — doc 18
/admin/analytics                → Revenue / MRR / ARR / cohorts — doc 20
/admin/marketing/*              → Marketing CMS: pages, blocks, SEO, testimonials, stats,
                                  categories, FAQs, navigation, media (full pages) — doc 21
/admin/content                  → Blog/SEO content management
/admin/feature-flags            → Toggle features (this doc §4)
/admin/event-logs               → Unified event log (security/admin/system/integration/…) — doc 22
/admin/audit-log                → Audit trail (= event-log filtered to admin+security) — docs 18, 22
/admin/roles                    → Roles & permissions — doc 19
/admin/settings                 → Platform settings (maintenance mode, etc. — §5)
```
- Layout: collapsible sidebar (desktop) / drawer (mobile), responsive from the start (doc 14). Breadcrumbs + back button on every detail page.
- All data loaded from admin APIs (doc 07) — **no static screens.** Each page has real loading/empty/error states.

---

## 3. Appearance control (theme / font / language)

Drives the design system (doc 14) and i18n (doc 15) via `platform_settings` + `theme_presets` (doc 06).

**Confirmed model — default + user override + optional lock:**
- Super Admin sets the **platform default** for each axis:
  - **Mode default:** light / dark / system
  - **Color preset default:** one of the curated presets
  - **Font default:** one of the curated fonts
  - **Language default:** one of the registered locales (EN / HI / …)
- **Users can override their own** (in user settings) — unless the admin **locks** that axis.
- **Lock toggle per axis:** when locked, the admin's choice is forced platform-wide and the user's control for that axis is hidden/disabled.
- Admin can also **enable/disable** which presets, fonts, and languages are *available* to users (curate the menu).

**UX:** the appearance page shows a **live preview** of each preset (light & dark), the available fonts, and language options. Changes are saved to the backend and take effect platform-wide (cached in Redis, read by the `ThemeProvider`/i18n on load). No redeploy.

**Resolution (recap from doc 14):**
```
user override (if set & not locked) → platform default (admin) → safe fallback
```

**Future (doc 14 §10):** full custom theme-token editor (per-token color picker) for white-labeling.

---

## 4. Feature flags

- A `/admin/feature-flags` page to toggle features on/off **without a deploy** — e.g. enable alerts, enable a new chart, gate a beta feature to certain tiers/roles, kill a misbehaving integration.
- Backed by a settings/flags store (doc 06 `platform_settings` or a dedicated `feature_flags` table), read by both frontend and backend.
- Supports targeting: global, by subscription tier, by role, or by user cohort.
- Every flag change is audit-logged.

---

## 5. Platform settings & maintenance mode

`/admin/settings` controls platform-wide behavior (all persisted, API-driven):
- **Maintenance mode:** toggle a banner or full maintenance screen (e.g. during a data-migration); admins bypass it. Useful around the 3:30 PM pipeline or deploys.
- **Default capital / risk defaults** for new users (doc 06 `users` defaults).
- **Pick parameters surface (read-only or guarded):** expose key quant config (doc 04) for visibility; changing strategy params is guarded/audit-logged and ideally versioned (it affects the track record — handle carefully).
- **Compliance copy:** edit disclaimers/terms shown across the app (doc 09) — centralized, localized (doc 15).
- **Email/notification templates** management (doc 18).
- **Announcements:** push an in-app banner/notice to users.

---

## 6. What the control panel is NOT

- It is **not** a way to fake the track record. Strategy params and pick outcomes are guarded and audit-logged; the public tracker stays honest (doc 00 non-negotiable #2). Admin override of a *pick* (doc 07 `override-pick`) is logged and visible — not a silent edit of history.
- It is **not** a place for hardcoded demo data — every panel reads live backend data.

---

## 7. Security

- All admin routes double-gated: authenticated **and** role-authorized server-side (doc 19).
- **2FA required for admin roles** (doc 19).
- Every mutating action audit-logged with actor, target, before/after, IP, timestamp (doc 18).
- Rate-limited; sensitive actions (secrets, blocking users, role changes) may require re-auth.

---

## 8. Phase evolution

| Phase | Deliverable |
|---|---|
| 1 | `/admin` shell + RBAC gate, appearance (theme/font/language defaults + lock), user list/detail + session control (doc 18), integrations/secrets (doc 17), basic overview KPIs, maintenance mode, audit log |
| 2 | Feature flags, announcements, content management, richer analytics (doc 20), notification templates |
| 3 | Custom theme-token editor, granular role editor (doc 19), white-label, advanced cohort analytics |
| Future | Multi-admin workflows, approval flows, A/B test management |

---

*Next: [`17-integrations-secrets.md`](./17-integrations-secrets.md) — the API-key/secret vault for all integrations.*
