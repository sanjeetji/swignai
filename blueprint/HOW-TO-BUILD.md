# HOW TO BUILD — Build Order, Setup & Resume Prompt

> 🧭 **Status:** ✅ Living build guide · **Tier:** — → **Target: 🏆 Best-in-class** · **Phase all** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** This file tells you (and any AI/dev) exactly how to start building SwingAI from the docs, in what order, and — critically — **how to resume from a paused state every time**. The project root is this same directory: `/Users/sanjeet_kumar/Documents/swingai/` (the monorepo lives here, alongside `blueprint/`).

---

## 0. The golden rule of sequencing

**Prove the edge (Phase 0) before building the platform.** The #1 unknown is whether the trading strategy actually has positive net-of-cost expectancy (doc 12 R1). All the cool UI, admin plane, CMS, and analytics are worthless if the picks don't work. So:

```
Phase 0 (validation harness)  →  decision gate  →  Phase 1 platform  →  Phase 2 → 3 → 4
```

Do **not** start with the marketing site or admin panel. Start with `quant/` + `backtest/` (docs 04, 05).

---

## 1. One-time setup (before any feature)

1. `git init` at the project root (`/Users/sanjeet_kumar/Documents/swingai/`); add `.gitignore` (node, python, env).
2. Scaffold the **Turborepo monorepo** per [01-architecture-techstack.md](./01-architecture-techstack.md): `apps/marketing` + `apps/dashboard` (Next.js+TS), `packages/ui` + `packages/api-client`, `backend/` (FastAPI), `infra/` (Docker Compose: Postgres + Redis). **Clone OmniMark into the workspace and lift its layout + infra** (vault, RBAC, audit, CMS, theming, `render.yaml`/`turbo.json`) — see [OMNIMARK-REUSE.md](./OMNIMARK-REUSE.md). Build the **trading engine and i18n fresh** (not in OmniMark).
3. Create accounts/keys (added later via the vault, doc 17, not hardcoded): Supabase, Upstash Redis, Vercel, Railway/Render, Gemini/OpenRouter, Angel One.
4. Local env via Docker Compose; `.env` for local only (production secrets live in the vault/platform secret store).

---

## 2. Build order (each item links its doc)

> Build in this order. Each unit is API-driven, themed (dark/light/system), i18n-ready (EN+HI), responsive, and has no hardcoded data.

**Phase 0 — Validate**  ✅ *built — see `backend/`*
1. `backend/app/quant/` — indicators, regime, filters, scorer, risk, exits, picker ([04](./04-picker-strategy.md)) ✅
2. `backend/app/data/` — synthetic + yfinance providers + factory ([02](./02-data-layer.md)) ✅
3. `backend/app/backtest/` — walk-forward, net-of-cost, R-multiple harness ([05](./05-validation-backtest.md)) ✅
4. `backend/tests/` + `backend/app/cli.py` — 23 passing; `python3 -m app.cli backtest --synthetic` ✅
5. **Run the real-data backtest** (`pip install yfinance`, `python -m app.cli backtest --days 600`) → if positive, run a 90-day public log. **GATE.** ⬅ next

**Phase 1 — MVP (Survival + Process first), then platform plane**
6. Supabase schema + Alembic migrations ([06](./06-database-schema.md)); **seed** roles/permissions, theme presets, platform settings, marketing content ([19](./19-rbac-security.md), [21](./21-marketing-cms.md))
7. FastAPI app: auth, **RBAC + 2FA + session/block middleware**, endpoints ([07](./07-backend-api-cron.md), [19](./19-rbac-security.md))
8. LLM layer (Gemini/OpenRouter) or templates ([03](./03-ai-llm-layer.md))
9. Paper-trading engine + risk guards ([04](./04-picker-strategy.md), [07](./07-backend-api-cron.md))
10. Cron: daily pipeline, exit checker, accuracy, metrics ([07](./07-backend-api-cron.md))
11. Next.js shell: providers (theme/i18n), middleware (locale/auth/RBAC/block), design system + presets ([14](./14-design-system-ui-ux.md), [15](./15-internationalization.md))
12. **User dashboard** — picks, enforced risk calculator, paper trading, journal, personal analytics ([08](./08-frontend-seo.md), [20](./20-business-analytics.md))
13. **Super Admin control plane** (full-page): appearance, integrations/secrets vault, user/session mgmt, **event logs + audit** (`emit()` helper wired in), overview ([16](./16-admin-control-panel.md), [17](./17-integrations-secrets.md), [18](./18-user-management-sessions.md), [22](./22-event-logs.md))
14. **Marketing CMS** — seeded pages, blocks, per-page SEO + JSON-LD, ISR + revalidation ([21](./21-marketing-cms.md), [08](./08-frontend-seo.md))
15. Honest **track-record** page; DPDP consent/policy/export/delete ([09](./09-compliance-sebi.md))

**Phase 2–4** — alerts, deep analytics, subscriptions, more languages, custom theme editor, F&O — per [10-roadmap-phases.md](./10-roadmap-phases.md).

---

## 3. Progress ledger (update as you go)

Track state here so resume is unambiguous. (The roadmap checkboxes in [10](./10-roadmap-phases.md) are the detailed source of truth.)

```
CURRENT PHASE: 1 — MVP (foundation BUILT & booting; feature-completion in progress)
LAST COMPLETED UNIT: Full Phase-1 foundation.
  BACKEND (FastAPI, boots on async SQLite, 23 endpoints, verified end-to-end):
    core (config, async db, JWT+RBAC security, redis), models (users/roles/perms,
    platform/theme/flags/integrations, sessions/blocks, event_logs+DSR, trading,
    cms, billing), services (event_log emit, secret_box vault, rbac), routers
    (health, brand, platform appearance, auth register/login/me, daily-picks wired
    to the quant engine, paper-trade buy/close/portfolio with risk guards, admin
    users/appearance/integrations/event-logs/audit, cms public+admin), seed
    (roles+perms, 4 theme presets, super admin admin@swingai.in/admin12345, marketing).
  FRONTEND (Turborepo: apps/marketing + apps/dashboard + packages/ui + api-client):
    theming (next-themes + token presets), i18n (next-intl EN+HI), marketing landing
    (CMS block renderer, ISR, SEO metadata), dashboard (login, picks+portfolio),
    admin shell (users + event logs). Needs `npm install` to run.
  Phase-0 quant harness still green (23 tests).
  INFRA (VERIFIED): docker-compose (SwingAI's OWN Postgres :5434 + Redis :6380, separate
    from OmniMark) + control scripts (scripts/{swingai,db,backend,frontend,logs}.sh,
    _common.sh). Backend verified booting against Postgres — 34 tables created + seeded.
  ADDED endpoints (now 27): /api/track-record + /api/analytics (honest, no fabrication),
    admin GET appearance, admin /metrics, integration test (vault encrypt→decrypt verified,
    masked hint, secret never returned). Dashboard RiskCalculator + marketing track-record page.
NEXT UNIT (pick one, continue feature-by-feature):
  (a) `scripts/swingai.sh start` → verify both apps in the browser end-to-end.
  (b) Admin sub-pages: appearance editor, integrations/secrets UI, user-detail+sessions,
      CMS block composer (TipTap+dnd), analytics charts, event-log filters/live-tail.
  (c) Dashboard depth: wire RiskCalculator→paper-buy, journal, expectancy/equity curve.
  (d) Real cron pipeline + Redis caching + Angel One data + LLM explanations.
  (e) Alembic migrations (replace dev create_all), 2FA, rate-limiting, Supabase prod.
BLOCKERS / NOTES: trading edge still UNPROVEN (run real-data backtest, R1). SEBI+DPDP
  lawyer before public launch (R2/R9). Auth is dev-grade (token in localStorage) — move
  to Supabase/httpOnly cookies for prod (blueprint/19). Frontend not yet `npm install`-ed/
  browser-verified here. Working tree uncommitted. Docker DB containers currently UP.
```

Update these lines after every work session. An AI resuming the project reads this first.

**What exists now:** `backend/app/{core,models,services,routers,schemas}` + Phase-0
`{quant,data,backtest}`; `apps/marketing`, `apps/dashboard`, `packages/{ui,api-client}`.
**Run backend:** `cd backend && uvicorn app.main:app --reload` → http://localhost:9000/docs
**Run frontend:** `npm install && npm run dev` (marketing :9002, dashboard :9001).
**Tests:** `cd backend && python3 -m pytest -q`.

---

## 4. ▶ THE RESUME PROMPT (paste this to continue any time)

Copy-paste this string at the start of any new session to resume exactly where you left off:

```
Resume building the SwingAI platform. Project root: /Users/sanjeet_kumar/Documents/swingai
(monorepo lives here, alongside blueprint/).

1. Read blueprint/README.md, then blueprint/HOW-TO-BUILD.md (§3 progress ledger = current state),
   then the numbered docs relevant to the next unit.
2. Obey the 3 non-negotiables and Engineering Principles in blueprint/00-overview-philosophy.md:
   - deterministic math picker (never AI); honest R-based track record (incl. scratches);
     "analysis not advice" framing.
   - NO dummy/static/hardcoded data — every feature backend/API-driven with real
     loading/empty/error states; strings via i18n (EN+HI), colors via theme tokens
     (dark/light/system), secrets via the encrypted vault.
   - role-based (Super Admin vs User), secure by default (RBAC + 2FA + RLS + audit + DPDP),
     responsive/mobile-first, cool/animated UI.
3. Build order = blueprint/HOW-TO-BUILD.md §2. Start Phase 0 (quant + backtest) FIRST and do not
   skip the edge-validation gate. Then Phase 1 per blueprint/10-roadmap-phases.md checkboxes.
4. Work on the NEXT UNIT from the progress ledger. When done: run its verification
   (blueprint/11-verification-testing.md), tick the roadmap checkbox, and update the
   §3 progress ledger (CURRENT PHASE / LAST COMPLETED / NEXT UNIT / BLOCKERS).
5. If reusing OmniMark patterns, first clone that repo into the workspace so its code is
   readable (it is not accessible otherwise).

Tell me what unit you're building, build it end-to-end (backend + API + UI + tests),
then stop and report status + the updated ledger.
```

**Short version** (for quick continuation):
```
Continue SwingAI from blueprint/HOW-TO-BUILD.md §3 ledger. Read README + the next unit's docs,
follow 00's non-negotiables + engineering principles (no hardcoded data, themed, i18n,
RBAC, API-driven). Build the NEXT UNIT end-to-end, verify per doc 11, update the ledger.
```

---

## 5. How "pause / resume" works in practice

- **To pause:** finish the current unit (or leave it clearly half-done with a note), update the §3 ledger, commit (`git commit`).
- **To resume:** open a new session, paste the **Resume Prompt** (§4). The AI reads the ledger + relevant docs and continues from `NEXT UNIT`.
- The docs are the durable memory; the ledger is the bookmark. Together they make the build fully restartable regardless of session/context loss.

---

*Back to the [README index](./README.md).*
