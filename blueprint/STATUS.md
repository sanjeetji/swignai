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
| **0 — Validation** | Prove the trading edge (backtest) | 🔴 **EDGE NOT PROVEN** — real-data backtest run; the strategy as-configured has NEGATIVE expectancy (see Phase-0 result below). Harness ✅ works; **strategy needs rework before scaling** |
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

## 🔴 PHASE-0 RESULT — real-data backtest (the go/no-go gate, blueprint/05, risk R1)

Ran `app.cli backtest --days 600` on **real NSE data via yfinance** (~20 large-caps, ~2 years), net of costs:

| Metric | Value |
|---|---|
| Trades | 127 |
| **Expectancy (avg R)** | **−0.149** ❌ (need > 0) |
| Return | **−21.3%** |
| Win rate (incl. scratches) | 26.8% (34W / 68L / 25 scratch) |
| Profit factor | 0.52 (need > 1) |
| Max drawdown | 21.4% |
| By regime | bull −0.215R, neutral +0.425R, bear ~flat (gate working) |

**Out-of-sample study (2026-06-25):** ran 6 principled variants (wider stops, longer hold, concentrate, tighter entry, combos) on ~4y real data with a **train/test split (60/40)**. Result: **every variant is POSITIVE in-sample (train +0.22…+0.37R) but NEGATIVE out-of-sample (test −0.03…−0.17R).** That train-positive/test-negative pattern is the classic **overfitting signature — there is no durable edge** in the textbook-indicator approach. Best OOS = −0.025R (tighter_entry), still negative.

**Verdict:** the deterministic textbook-indicator funnel **has no real (out-of-sample) edge** and loses money net of costs. This is exactly what Phase 0 is for — it caught this cheaply *before* scaling. **Chasing more parameter tweaks will keep overfitting.** The honest path is to stop selling "winning picks" and reframe the product (see recommendation). **Do not treat the live picks as a proven edge.** Honest next options (do NOT skip): (1) parameter study + proper walk-forward on a wider, point-in-time universe; (2) replace the textbook signals with a genuinely researched edge (relative-strength/regime focus, better entries); (3) accept the edge isn't there with these signals and pivot the product to *risk-discipline + education + paper-trading* (still valuable per blueprint/00) rather than "winning picks". The platform plumbing is real; the **strategy is not yet validated**.

## DIRECTION (2026-06-25) — honest swing-trading screener on real data

Decision: keep the platform **focused on swing trading**; reframe honestly (educational
technical screening + transparent tracker, NOT "guaranteed winning picks"); keep edge
research in the background. The screener is **fully deterministic math on real prices** —
no guessing. Enriched with advanced indicators: EMA 20/50/100/200 + SMA200, RSI, MACD,
ATR, **ADX** (trend strength), **Stochastic**, **Bollinger %b**, volume ratio, **OBV**
(accumulation), **52-week** range, relative strength, distance-to-breakout.
- New `GET /api/stocks/{symbol}` — full math breakdown + the 6 swing conditions + score +
  trade plan on REAL prices (verified live for HAL). Educational disclaimer enforced.
- `/api/daily-picks` now serves the pipeline's stored picks from the DB (real-data, fast),
  with live compute as fallback. Pipeline stores the full analysis snapshot per pick.
- **Live real-data pipeline (verified 2026-06-25):** with `DATA_PROVIDER=yfinance`, the daily
  pipeline computed **5 real swing candidates** (SBIN, MARUTI, ICICIBANK, AXISBANK, LT; bull
  regime) → stored in `ai_picks` → `/api/daily-picks` serves them from the DB (source=pipeline)
  with full analysis + Hinglish. Public `/stocks/[symbol]` SEO page + dashboard `/analyze`
  surface the math. Scheduler verified (3:30 PM pipeline, 3:45 PM exit-checker IST) — enable via
  `ENABLE_SCHEDULER=true`; or trigger on demand via Admin → Re-run pipeline.
- **Honest note:** richer math + real data = better *analysis/education*, NOT proven edge (the OOS
  study still says no durable edge). The tracker will show, transparently, whether it works.

## INITIAL STATE (baseline)
Greenfield 2026-06-24. Now: full spec (23 areas) + Phase-0 harness + Phase-1 foundation (backend booting, frontend scaffolded). Resume anytime via [HOW-TO-BUILD.md](./HOW-TO-BUILD.md) §4 prompt.

_Updated: 2026-06-24 (Phase-1 foundation built)._
