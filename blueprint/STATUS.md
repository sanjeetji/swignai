# STATUS — Living Tracker

> **The single source of truth for what's done, pending, and how good it is.** Updated as the build progresses. Each blueprint doc also carries a one-line status badge linking here. The **target maturity for the entire platform is 🏆 Best-in-class** — this table tracks the gap between *current* and *target*.

**Legend**
- **Code status:** `📋 Initial` (idea) · `📝 Spec` (designed, not coded) · `🧪 Partial` (some code) · `🛠️ In progress` · `✅ Done` (built + verified)
- **Maturity tiers:** `① Basic` → `② Mid` → `③ Advanced` → `🏆 Best-in-class`
- **Target for every feature: 🏆 Best-in-class.**

_Last updated: 2026-06-24 · Phase 0 (validation) harness built & green (23 tests)._

---

## Phase-level status

| Phase | Goal | Status |
|---|---|---|
| **0 — Validation** | Prove the trading edge (backtest) | 🧪 **Partial** — harness ✅ built & tested; real-data run pending (the gate) |
| **1 — MVP** | Survival+process, platform plane, marketing | 🛠️ **In progress** — backend spine ✅ booting (23 endpoints); frontend monorepo + both apps scaffolded; feature depth in progress |
| **2 — Beta** | Retention, alerts, SEO, analytics | 📝 Spec |
| **3 — Business** | Subscriptions, scale, Android, RA license | 📝 Spec |
| **4 — Scale + F&O** | Expand once swing proven | 📝 Spec |

---

## Feature / doc status & maturity

| # | Area (doc) | Code status | Current tier | Target | Phase |
|---|---|---|---|---|---|
| 00 | Overview & philosophy | ✅ Done (living) | 🏆 Best-in-class | 🏆 | — |
| 01 | Architecture & tech stack | ✅ Spec (revised to OmniMark split) | 🏆 | 🏆 | — |
| 02 | Market data layer | 🧪 Partial (synthetic+yfinance built; Angel One/Redis pending) | ③ Advanced | 🏆 | 0→2 |
| 03 | AI / LLM layer | 📝 Spec | 🏆 (design) | 🏆 | 1 |
| 04 | Picker & strategy | ✅ **Done** (Phase 0 built + tested) | ③ Advanced | 🏆 | 0 |
| 05 | Validation / backtest | ✅ **Done** (harness built; real-data run pending) | ③ Advanced | 🏆 | 0 |
| 06 | Database schema | 🧪 Partial (SQLAlchemy models built + seeded; Alembic/Postgres pending) | ③ Advanced | 🏆 | 1 |
| 07 | Backend API & cron | 🧪 Partial (FastAPI app + 23 endpoints ✅ booting; cron/Redis pending) | ③ Advanced | 🏆 | 0→1 |
| 08 | Frontend & SEO | 🧪 Partial (2 Next apps scaffolded: theming/i18n/landing/dashboard/admin shell) | ③ Advanced | 🏆 | 1 |
| 09 | Compliance (SEBI/DPDP) | 📝 Spec (needs lawyer) | ③ Advanced | 🏆 | 1 (gate) |
| 10 | Roadmap | ✅ Living | — | — | all |
| 11 | Verification & testing | 🧪 Partial (Phase 0 tests ✅) | ③ Advanced | 🏆 | 0→all |
| 12 | Decisions & risks | ✅ Living (ADRs) | — | — | all |
| 13 | Future vision | 📝 Spec (deferred) | 🏆 (design) | 🏆 | 3→ |
| 14 | Design system & UI/UX | 🧪 Partial (tokens, presets, theme provider, core components, toggle) | ③ Advanced | 🏆 | 1 |
| 15 | Internationalization | 🧪 Partial (next-intl EN+HI, locale routing, both apps) | ③ Advanced | 🏆 | 1 |
| 16 | Admin control panel | 🧪 Partial (appearance API + admin shell; editors pending) | ③ Advanced | 🏆 | 1 |
| 17 | Integrations & secrets vault | 🧪 Partial (vault encrypt/decrypt + API; UI pending) | ③ Advanced | 🏆 | 1 |
| 18 | User mgmt & sessions | 🧪 Partial (users list/block + audit; sessions/detail UI pending) | ③ Advanced | 🏆 | 1 |
| 19 | RBAC & security | 🧪 Partial (roles/perms/JWT/guards ✅; 2FA/rate-limit pending) | ③ Advanced | 🏆 | 1 |
| 20 | Business analytics | 📝 Spec | 🏆 (design) | 🏆 | 1→3 |
| 21 | Marketing CMS | 🧪 Partial (models+seed+public render+block renderer; composer pending) | ③ Advanced | 🏆 | 1→2 |
| 22 | Event logs | 🧪 Partial (emit + log + admin list/audit; filters/live-tail pending) | ③ Advanced | 🏆 | 1 |

> "Current tier" for un-coded areas = the maturity of the **design**; it can only be confirmed once built and verified (doc 11). Areas marked ③ Advanced reach 🏆 with the noted upgrades (e.g. picker → ML scoring, data → Angel One/TrueData, i18n → more languages).

---

## What's DONE right now (built + verified)
- **Phase 0 quant engine + backtest harness** (`backend/app/{quant,data,backtest}`) + CLI + **23 passing tests**. ✅
- **Backend platform spine** (`backend/app/{core,models,services,routers,schemas}`): FastAPI app **boots on async SQLite, 23 endpoints, verified end-to-end** — auth (register/login/me), RBAC guards (403 verified), seeded super admin + 4 theme presets + marketing content, event/audit logging, daily-picks wired to the quant engine, paper-trade with server-side risk guards, admin users/appearance/integrations/events, CMS public+admin. ✅
- **Secrets vault** (`services/secret_box.py`) encrypt/decrypt + masking. ✅
- **Frontend monorepo** (Turborepo): `packages/{ui,api-client}` + `apps/{marketing,dashboard}` — theming (next-themes + token presets), i18n (next-intl EN+HI), marketing landing (CMS block renderer + SEO metadata, ISR) + **track-record page**, dashboard (login + picks + portfolio + **enforced RiskCalculator**), admin shell (users + event logs). 🧪 scaffolded (needs `npm install`).
- **Local infra (Docker, VERIFIED)**: `docker-compose.yml` — SwingAI's OWN Postgres `:5434` + Redis `:6380` (separate from OmniMark). Backend boots against Postgres (34 tables seeded). **27 API endpoints**; honest `/api/track-record` + `/api/analytics`; secrets vault encrypt→decrypt verified. ✅
- **Control scripts** (`scripts/`): `swingai.sh` (master: start/stop/restart/status/fresh/logs/test) + `db.sh` `backend.sh` `frontend.sh` `logs.sh` + `_common.sh`. ✅
- **Brand single-source-of-truth** + one-command rename (`scripts/rename-brand.sh`). ✅

## What's PENDING next (in order)
1. **Run the real-data backtest** (`pip install yfinance`; `python -m app.cli backtest --days 600`) → Phase-0 go/no-go gate (R1). ⬅ still the most important
2. `npm install` + boot both apps against the API; verify end-to-end in the browser.
3. Feature depth: admin editors (appearance/integrations/CMS composer/user-detail), dashboard risk-calculator + journal + expectancy/equity-curve + track-record page, real cron + Redis + Angel One + LLM explanations, 2FA + rate-limit, Alembic + Supabase/Postgres.

## INITIAL STATE (baseline)
Greenfield 2026-06-24. Now: full spec (23 areas) + Phase-0 harness + Phase-1 foundation (backend booting, frontend scaffolded). Resume anytime via [HOW-TO-BUILD.md](./HOW-TO-BUILD.md) §4 prompt.

_Updated: 2026-06-24 (Phase-1 foundation built)._
