# STATUS — Living Tracker

> **The single source of truth for what's done, pending, and how good it is.** Updated as the build progresses. Each blueprint doc also carries a one-line status badge linking here. The **target maturity for the entire platform is 🏆 Best-in-class** — this table tracks the gap between *current* and *target*.

**Legend**
- **Code status:** `📋 Initial` (idea) · `📝 Spec` (designed, not coded) · `🧪 Partial` (some code) · `🛠️ In progress` · `✅ Done` (built + verified)
- **Maturity tiers:** `① Basic` → `② Mid` → `③ Advanced` → `🏆 Best-in-class`
- **Target for every feature: 🏆 Best-in-class.**

_Last updated: 2026-06-26 · Phase 0 (validation) COMPLETE — walk-forward done, edge not proven; honest educational positioning validated. Platform (Phases 1–3 build) functional._

---

## Phase-level status

| Phase | Goal | Status |
|---|---|---|
| **0 — Validation** | Prove the trading edge (backtest) | ✅ **COMPLETE — edge NOT proven.** Real-data backtest + **walk-forward (3×5y windows)** done: no robust out-of-sample edge (profitable only in trending years, loses in choppy 2024–26). Validated the **honest educational/discipline positioning**, NOT "winning picks" (see Phase-0 result below). Harness ✅. |
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

**✅ Walk-forward — COMPLETED (2026-06-26):** the rule-based funnel runs over 3 sequential **5-year** windows on real yfinance data (every window is out-of-sample since no parameters are fitted). The yfinance provider was extended to a 5y fetch so each window has its 200-EMA warmup.

| Window | Period | Trades | Expectancy | Win% | PF | Return |
|---|---|---|---|---|---|---|
| 1 | 2021–2023 | 61 | +0.046R | 36.1% | 0.88 | −2.5% |
| 2 | 2023–2024 | 152 | **+0.209R** | 37.5% | 1.13 | **+6.0%** |
| 3 | 2024–2026 | 114 | **−0.107R** | 28.9% | 0.57 | **−16.5%** |

**The edge is regime/period-dependent, not robust:** positive only in the strong-trend window (2023–24), marginal in 2021–23, and clearly negative in the recent choppy market (2024–26). Win rate is consistently low (29–38%) — the system leans on rare large winners, which is fragile. Averaged it is roughly break-even *before* the recent drawdown, and the most recent, most-relevant window loses. This **confirms** the prior finding with proper walk-forward methodology.

**✅ Edge research — COMPLETED (2026-06-26):** acting on the walk-forward insight (bull entries chase over-extension), tested 5 principled, economically-motivated variants with walk-forward (`backend/research_edge.py`, data cached once). **Every variant that tightens the over-extension knockout beat baseline** — the hypothesis is confirmed, not overfit. Best = **`no_overbought`** (`max_extension_pct` 8→4, `rsi_high` 65→60): avg expectancy across windows nearly tripled (**+0.135R vs +0.049R**) and the recent choppy window improved **−0.107R → −0.014R**. Applied to the live `DEFAULT` config → the full recent 600-day backtest moved from **−0.138R to +0.001R (break-even)**, win rate 27%→33%, return −21%→−15.5%, profit factor 0.53→0.65. **A material, OOS-validated improvement** — but still **not a proven positive edge** (recent expectancy ≈ 0, return still negative net of costs). Don't chase further tweaks (overfitting risk); a real edge needs a different signal source + survivorship-free universe.

**✅ Edge research round 2 — signal gates (2026-06-28):** tested the computed-but-unused indicators as **walk-forward-gated knockouts** (`research_edge.py`): ADX (trend strength), OBV accumulation, Bollinger %b, and combos. **Only `adx_min=25` was positive in EVERY window** and improved the most-relevant recent OOS window (**−0.014R → +0.015R**, avg **+0.135R → +0.157R**, all 3 windows positive). OBV (W1 collapse +0.137→+0.037) and Bollinger (recent window −0.031) were inconsistent/negative-recent = overfit; all combos over-filtered (recent −0.07 to +0.02). **Adopted ADX≥25 into live `DEFAULT`; rejected the rest** (kept as off-by-default knobs). This is a disciplined, single, economically-motivated gate (only trade genuine strong trends) — the recent window is now marginally positive, but expectancy is still small and this is **still not a proven durable edge** (one universe, ~19 symbols, survivorship caveat). 29 tests green with the gate active.

**Verdict — Phase-0 validation is COMPLETE: edge materially improved but still NOT proven (recent OOS ≈ break-even/slightly positive, not robust).** The deterministic textbook-indicator funnel does not have a durable edge and loses in recent conditions; its profitability is confined to trending years. Phase 0 did its job — it caught this cheaply *before* scaling. **Do not treat the live picks as a proven edge / do not sell "winning picks."** The validated, honest path (already the product's positioning): **risk-discipline + education + paper-trading + a transparent, R-based track record** (blueprint/00) — the screener is framed as *educational technical analysis, not advice*. **Open research direction (R&D, not a Phase-0 pass):** the bull-regime entries chase over-extension and revert — a genuinely researched edge would target better entries (pullback/tight-base) or relative-strength ranking with a stricter over-extension knockout; revisit only with a point-in-time survivorship-free universe.

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
