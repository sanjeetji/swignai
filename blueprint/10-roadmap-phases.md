# 10 — Roadmap: Phases 0 → 4

> 🧭 **Status:** ✅ Living · **Tier:** — → **Target: 🏆 Best-in-class** · **Phase all** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** The complete, granular build plan from "prove the edge" to "scale + F&O." Each phase has a single **goal/key question**, a **checklist**, a **cost**, and an **exit criterion** that gates the next phase. Build in this order — skipping Phase 0 is the most common and most expensive mistake. Check the boxes as you go; this doubles as the resume pointer.

> **Sequencing principle:** validate before building; **Survival + Process layers (Layers 1–2) before Signals (Layer 3)**; revenue only after retention is proven.

---

## PHASE 0 — Validate the edge (Weeks 1–2 build → 90-day public run) — **DO THIS FIRST**

**Goal / key question:** *Does the strategy have positive, net-of-cost expectancy out-of-sample — and can it attract an audience?* This is the **highest-risk unknown in the project.**

**Checklist:**
- [x] `quant/config.py` — all tunable parameters (doc 04)
- [x] `quant/indicators.py` — EMA/RSI/MACD/ATR/volume ratio/rel-strength (pure pandas/numpy; TA-Lib avoided to skip the native build — swappable later)
- [x] `quant/regime.py` — Gate 0 (NIFTY regime: bull/neutral/bear)
- [x] `quant/filters.py` — Stage 1 knockouts
- [x] `quant/scorer.py` — Stage 2 weighted score + breakdown
- [x] `quant/risk.py` — Stage 3 stop/targets/position size/portfolio guards
- [x] `quant/exits.py` — exit/trailing/scratch logic (start-of-bar stop, honest scratch band)
- [x] `quant/picker.py` — orchestrator (`get_top_picks`)
- [x] `data/` — synthetic (offline) + `yfinance_provider.py` + factory (Redis cache: Phase 1)
- [x] `backtest/` — next-bar execution, cost model, walk-forward, regime-segmented, R-multiple metrics (doc 05)
- [x] `tests/` — 23 passing (indicators, risk, exits, picker, backtest honesty); `cli.py` runner
- [ ] **Run the REAL-DATA backtest** (`pip install yfinance`; `python -m app.cli backtest --days 600`) → review expectancy, profit factor, drawdown, per-regime *(synthetic run works; real-data run is the actual gate)*
- [ ] Add point-in-time universe construction for the real backtest (avoid survivorship — doc 05 §3)
- [ ] **If positive:** run the strategy **LIVE in public** 90 days (free Telegram/Twitter log, honest, R-based)

**Exit criterion:** ✅ positive walk-forward expectancy net of costs + sane per-regime behavior + early audience signal → **Phase 1.** ❌ otherwise rework strategy (tune `config.py`) or stop.

**Status:** harness built & green on synthetic data (no edge there — expected). Real-data run pending; that is the go/no-go (R1).

**Cost:** ~₹5k total.

---

## PHASE 1 — MVP for you + 20 testers (Months 1–4)

**Goal / key question:** *Is live expectancy positive over ~3 months? Do testers come back?* Build **Survival + Process layers first.**

**Checklist — infra & data:**
- [ ] Monorepo scaffold (pnpm + uv, Docker Compose local) (doc 01)
- [ ] Supabase project (Postgres + Auth), Alembic migrations, schema §Phase-1 tables (doc 06)
- [ ] Upstash Redis wired (doc 01)
- [ ] Migrate live data to **Angel One SmartAPI** (+ Dhan fallback) (doc 02)
- [ ] Sentry + analytics + the error-handling contract (doc 07 §4)

**Checklist — backend:**
- [ ] FastAPI app + endpoints (doc 07): daily-picks, paper-trade buy/close, portfolio, analytics, track-record, regime
- [ ] `daily_pipeline` cron (3:30 PM) + `exit_checker` (3:45 PM) + nightly `update_old_picks` + `recompute_analytics`
- [ ] LLM layer (Gemini Flash + OpenRouter fallback) **or** templates; output validated for <60w + disclaimer + no buy/sell (docs 03, 09)
- [ ] Paper-trading engine + **server-side risk guards** (doc 07 §2)

**Checklist — frontend (Layers 1–2 are the priority):**
- [ ] `/dashboard`: picks with score breakdown, **enforced risk/position-size calculator**, portfolio heat meter
- [ ] Paper trading + **auto journal** + **post-trade review** + **personal expectancy** dashboard
- [ ] Auth (Supabase) + `middleware.ts` protected routes
- [ ] Basic marketing `/` + honest **`/track-record`** (R-based, net, all trades incl. scratches)
- [ ] **Mobile-first + fully responsive** (Android-first); design-system tokens, **theme presets + light/dark/system**, fonts (doc 14)
- [ ] **i18n EN + HI** (next-intl), locale routing, ₹/date formatting (doc 15)

**Checklist — platform control & security (foundational — docs 16–20):**
- [ ] **RBAC** (roles + permissions, server-enforced) + **admin 2FA** (doc 19)
- [ ] **Super Admin control plane** `/admin` (full-page screens): appearance (theme/font/language defaults + lock), settings, maintenance mode (doc 16)
- [ ] **Integrations & secrets vault** (encrypted) for LLM + data + Sentry/geo, with Test Connection (doc 17)
- [ ] **User management + session tracking** (IP→city/region, device), force-logout, block/unblock (doc 18)
- [ ] **Unified event log** + `emit()` helper wired into auth/admin/integration/pipeline; full-page viewer + filters + export; Audit Log view (doc 22)
- [ ] **Session-tracking + block-gate + RBAC middleware**; rate limiting (docs 07, 19)
- [ ] **DPDP**: consent, privacy policy, data export/deletion, retention TTL (docs 09, 18)
- [ ] **No-hardcoded-data** discipline + DB backups (docs 11, 19)
- [ ] Admin overview KPIs + personal analytics dashboard (doc 20)
- [ ] **Marketing CMS (seeded):** content model, core blocks, per-page SEO + JSON-LD, ISR + revalidation, basic admin editors, sitemap/robots (doc 21)

**Exit criterion:** positive live expectancy over 3 months + testers returning → **Phase 2.**

**Cost:** ₹800–1,500/mo.

---

## PHASE 2 — 100–500 beta users (Months 5–8)

**Goal / key question:** *Do users check the app 4+ days/week?* (Retention is the signal that the discipline value is real.)

**Checklist:**
- [ ] **WhatsApp/SMS alerts** on target/SL hit — Gupshup/MSG91 (WhatsApp), MSG91/Twilio (SMS); `alerts` table + `alerts_dispatch` job (docs 06, 07, 13)
- [ ] Deep portfolio analytics (win%, hold, best sector, R achieved, discipline trends over time)
- [ ] **SEO engine live at scale:** `/stocks/[symbol]` + `/sectors/[sector]` ISR, weekly AI `/blog` (docs 07, 08)
- [ ] Referral system (`referrals` table) + UI
- [ ] Hinglish UI expansion (beyond just explanations)
- [ ] Data redundancy (Dhan/Upstox auto-failover) hardened
- [ ] Mobile-web polish
- [ ] **Feature flags, announcements, content management** (doc 16); **impersonation + anomaly alerts** (doc 18)
- [ ] **Engagement/retention/cohort analytics + funnel** (doc 20); integration health dashboard (doc 17)
- [ ] Alerts providers wired in vault (WhatsApp/SMS/email)
- [ ] **Marketing CMS full editor:** block composer + drag-reorder + live preview, versioning/rollback, dynamic page creation, categories/items, media library, nav builder, hreflang (doc 21)

**Exit criterion:** 4+ days/week usage from a meaningful share of beta users → **Phase 3.**

---

## PHASE 3 — 1,000–10,000 users / real business (Months 9–18)

**Goal / key question:** *Can it generate real subscription revenue?*

**Checklist:**
- [ ] **Subscriptions** (Razorpay): Free / ₹499 Pro / ₹999 Premium; `subscriptions` + `payments` tables; gated features
- [ ] **Upgrade LLM → Claude/OpenAI** (two-line config swap, doc 03)
- [ ] **Paid data (TrueData)** when free-tier limits/accuracy bite (doc 02)
- [ ] **SEBI RA license** process + full compliance pages (doc 09)
- [ ] SEO content engine at scale; structured data everywhere (doc 08)
- [ ] **Android app** (Kotlin + Jetpack Compose — you build it) (doc 13)
- [ ] Admin override + ops dashboards
- [ ] **Full revenue suite: MRR, ARR, ARPU, LTV, churn, cohorts** with Razorpay live (doc 20)
- [ ] **Custom theme-token editor** + granular role editor (docs 14, 16, 19)
- [ ] **More languages** (Marathi/Tamil/Gujarati/Bengali) via the locale registry (doc 15)
- [ ] Security hardening: step-up auth, pen-test/security review, abuse tooling (doc 19)
- [ ] (Optional) **ML scoring** experiment vs rule baseline, walk-forward gated (docs 04 §10, 13)

**Exit criterion:** sustainable paying-user growth + acceptable unit economics → **Phase 4.**

---

## PHASE 4 — Scale + F&O (Month 18+)

**Goal:** *Expand the surface area once swing trading is proven.*

**Checklist:**
- [ ] **F&O — only after swing track record is proven** and (ideally) RA license in place
- [ ] F&O as **risk-defined strategies + education** (capital-defined spreads, explicit max loss), **never** naked option buy-calls (docs 09, 13)
- [ ] Real-time intraday infrastructure (Angel One WebSocket) for alerts (doc 13)
- [ ] Broker integration / one-click execution (compliance-gated) (doc 13)
- [ ] Community/leaderboards, AI chat assistant (doc 13)
- [ ] Fundraising (optional), deeper compliance & infra hardening

---

## Cost snapshot (Phase 1)

| Item | Cost |
|---|---|
| Vercel (frontend) | Free |
| Railway/Render (FastAPI + cron) | ₹800–1,500/mo |
| Supabase (Postgres + Auth) | Free tier |
| Upstash Redis | Free tier |
| Market data | yfinance free → Angel One free |
| LLM | Gemini/OpenRouter free (~₹0, ~5 cached calls/day) |
| **Total** | **₹800–1,500/mo** |

Costs scale meaningfully only at Phase 3 (paid data, paid LLM, payments) — by which point there's revenue.

---

## The honest non-code risks carried across all phases (see doc 12)

1. **Does the edge exist?** Unknown until Phase 0.
2. **SEBI framing legality** — needs a lawyer before public launch.
3. **Distribution** — 125k–250k free users needed for ARR target; a marketing/founder-time problem no code solves.
4. **Hinglish quality** of free models — test before committing.
5. **yfinance data cleanliness** for the Phase-0 backtest — cross-check or the results lie.

---

*Next: [`11-verification-testing.md`](./11-verification-testing.md) — how to prove each layer actually works.*
