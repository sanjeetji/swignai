# 01 — Architecture & Tech Stack

> 🧭 **Status:** 📝 Spec ✅ (OmniMark split) · **Tier:** 🏆 Best-in-class → **Target: 🏆 Best-in-class** · **Phase —** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** SwingAI is one product with a public, SEO-driven marketing/content surface and a private, authenticated trading dashboard — backed by a Python "quant brain" that does all the math. This doc locks the high-level architecture and every technology choice with honest alternatives and a free-now / paid-later note.

---

## 1. The big decision: ONE repo, TWO Next.js apps, ONE backend

**Decision (revised): a single Turborepo monorepo with two Next.js apps — `apps/marketing` (public/SEO) and `apps/dashboard` (private app + admin) — sharing `packages/ui` + `packages/api-client`, backed by ONE FastAPI service.** One repo, one design system, one API client; one public domain (marketing at root, dashboard at `/app` or `app.` subdomain via routing/proxy).

**Why this (and why it changed):** I originally recommended a single Next.js monolith. After reviewing your **OmniMark Pro** project — which uses exactly this two-app split *"so we can ship marketing changes daily and hit Lighthouse 100"* — the split is the better-evidenced choice **and** it lets SwingAI **directly reuse OmniMark's structure and code** (see [`OMNIMARK-REUSE.md`](./OMNIMARK-REUSE.md)). Honest reasoning:
- **Marketing stays ultra-light → Lighthouse 100 / great SEO.** The public app carries no dashboard JS, charting, or auth weight, so Core Web Vitals (the SEO engine, doc 08) stay excellent.
- **Dashboard can be heavy** (charts, tables, admin) without hurting public performance.
- **Still one repo, one design system, one API client** via `packages/*` — no duplication, shared theming/i18n/components.
- **SEO authority preserved:** serve both under one domain (marketing at apex, dashboard at a path/subdomain) behind one CDN; SEO-critical pages (`/stocks/[symbol]`, `/blog`, `/backtest`, `/track-record`) live in `apps/marketing` (ISR), not the dashboard.
- **Proven + reusable:** mirrors your working OmniMark layout, so its infra (vault, RBAC, audit, CMS, theming, deploy configs) ports with minimal change.

> If you'd prefer the simpler single-app monolith (one `apps/web`), it's still viable — but you lose the Lighthouse isolation and the easy OmniMark reuse. The docs below assume the two-app split; collapsing to one app is a mechanical change.

> **⚠️ "Two apps" is NOT "two websites" — it is ONE website.**
> | Concept | Reality |
> |---|---|
> | One domain / brand / SEO authority | ✅ `swingai.in` — marketing at root, dashboard at `/app` (or `app.` subdomain), one CDN |
> | Two apps (`apps/marketing` + `apps/dashboard`) | Just how the *code* is split, so the public site stays light |
> | Two ports (dev `9002` / `9001`) | **Local development only** — each `npm run dev` server needs its own port; in production both sit behind one domain |
>
> Decision confirmed (2026-06-25): keep the two-app monorepo (ADR #29).

---

## 2. Monorepo structure

> Layout mirrors **OmniMark Pro** (`apps/marketing` + `apps/dashboard` + `packages/ui` + `packages/api-client` + one `backend`) so its code reuses cleanly — see [`OMNIMARK-REUSE.md`](./OMNIMARK-REUSE.md).

```
swingai/                          # monorepo root (git) — Turborepo + workspaces
├── apps/
│   ├── marketing/                # Next.js (App Router, TS) — PUBLIC site, ultra-light (Lighthouse 100)
│   │   └── app/[locale]/         # i18n prefix (en/hi/…) — doc 15
│   │       ├── (home)/           # landing, pricing, about — CMS-driven, ISR — doc 21
│   │       ├── stocks/[symbol]/  # public ISR — SEO engine
│   │       ├── sectors/[sector]/ # public ISR
│   │       ├── backtest/         # public "prove it" tool
│   │       ├── blog/[slug]/      # public SEO articles
│   │       └── track-record/     # public honest scorecard
│   └── dashboard/                # Next.js (App Router, TS) — PRIVATE app + admin (can be heavy)
│       └── app/[locale]/
│           ├── dashboard/        # 🔒 user: picks, paper trades, P&L, journal, settings
│           └── admin/            # 🔒 RBAC full-page control plane — docs 16–21
│               ├── appearance/ integrations/ users/ sessions/ marketing/
│               └── analytics/ feature-flags/ audit-log/ roles/ settings/
├── packages/
│   ├── ui/                       # shared design system (shadcn, tokens, theme, animated components)
│   ├── api-client/               # typed API client (generated from FastAPI OpenAPI)
│   └── i18n/                     # shared locale catalogs / config — doc 15
├── backend/                      # Python 3.11 + FastAPI — the quant brain + platform API
│   └── app/
│       ├── core/                 # config, db (async SQLAlchemy), redis, security (JWT/RBAC/2FA), secrets
│       ├── data/                 # market data providers (pluggable) — doc 02
│       ├── quant/                # indicators, regime, picker, risk, exits — doc 04
│       ├── backtest/             # validation harness — doc 05
│       ├── llm/                  # pluggable LLM layer — doc 03
│       ├── paper/                # paper-trading engine
│       ├── cms/                  # marketing content + SEO — doc 21
│       ├── admin/                # platform settings, integrations vault, user/session mgmt — docs 16–18
│       ├── auth/                 # roles, permissions, sessions, audit, 2FA — docs 18, 19
│       ├── services/             # secret_box (envelope encryption), metrics (MRR/ARR), etc.
│       ├── workers/ jobs/        # cron/Celery: picks, exits, accuracy, metrics, health — doc 07
│       ├── routers/              # endpoints (public + user + admin)
│       ├── db/ models.py         # SQLAlchemy models — doc 06
│       └── tests/
├── infra/                        # docker-compose (local), render.yaml, turbo.json — adapt from OmniMark
├── blueprint/                         # these docs
└── README.md
```

**Tooling:** **Turborepo + npm/pnpm workspaces** (JS) + **uv** or Poetry (Python). (Turborepo confirmed — OmniMark uses it; adopt from the start for the two-app build graph.)

**The clean runtime picture:**
```
apps/marketing (Vercel) ┐
apps/dashboard (Vercel) ┼─►  FastAPI backend (Railway/Render): quant brain + cron + platform API
                        │              │
   packages/ui + api-client (shared)   ├─► Supabase (Postgres + Auth)
                                       └─► Upstash Redis (cache: picks, explanations, quotes, sessions)
```
Both Next apps share `packages/ui` + `api-client`. FastAPI owns the heavy Python (picker, backtest, paper logic, CMS, cron). Supabase = Postgres + Auth. Redis caches everything hot.

> **Why a separate Python backend at all?** Because the entire quant ecosystem (TA-Lib, pandas, numpy, backtesting) is Python — the math *must* live there. Next.js handles UI/auth; it does not do the math.

---

## 3. Tech stack — locked, with alternatives & reasons

> Convention: **PICK (now, free)** = use today. **UPGRADE (later, paid)** = move to at scale. **Why** = the honest reason.

### 3.1 Frontend
| Concern | PICK (now) | Alternatives | Why this |
|---|---|---|---|
| Framework | **Next.js (App Router) + TypeScript** | Remix, React+Vite, Astro | SSR/ISR = perfect SEO for stock pages; one codebase for public + private. Non-negotiable for SEO-led fintech. |
| UI kit | **Tailwind + shadcn/ui** | MUI, Chakra, Mantine | Fast, clean, fully ownable components, no design overhead. |
| Data fetching | **TanStack Query** | SWR, RTK Query | Caching, retries, background refetch out of the box. |
| State | **Zustand** | Redux, Jotai | Minimal global state; keep it light. |
| Price charts | **TradingView `lightweight-charts`** | ApexCharts, Highcharts | Purpose-built for candlesticks, free, fast. |
| Other charts (P&L/analytics) | **Recharts** (+ visx for complex viz) | Visx, Nivo | Equity curves, cohorts, funnels (docs 14, 20). |
| **Theming** | **next-themes + Tailwind CSS-variable tokens** | hand-rolled CSS vars | Light/dark/system + preset switching, admin-controlled (docs 14, 16). |
| **i18n** | **next-intl** | react-i18next, lingui | App-Router-native SSR i18n; EN+HI extensible (doc 15). |
| **Animation** | **Framer Motion** | GSAP, CSS only | Purposeful motion within a perf budget (doc 14). |
| Hosting | **Vercel (free tier)** | Netlify, Cloudflare Pages | First-class Next.js, ISR, edge. |

### 3.2 Backend
| Concern | PICK (now) | Alternatives | Why this |
|---|---|---|---|
| Language/Framework | **Python 3.11 + FastAPI** | Node/Nest, Go, Spring Boot | The quant ecosystem is Python — mandatory. FastAPI = async + Pydantic, familiar coming from Spring Boot. |
| ORM | **SQLAlchemy 2.0 + Alembic** | SQLModel, Tortoise, raw SQL | Mature; Alembic migrations. (SQLModel fine if you prefer Pydantic-native models.) |
| Validation | **Pydantic v2** | — | Native to FastAPI; request/response schemas. |
| Scheduler | **APScheduler** *(or Render/Railway cron)* | Celery+Redis, Temporal | 2–3 daily jobs don't justify Celery. Add Celery only at real scale (doc 07). |
| Hosting | **Railway or Render** | Fly.io, AWS ECS | ~₹800–1,500/mo, simple deploys, built-in cron. Render = mature; Railway = nicer DX. |

### 3.3 Database, Auth, Cache
| Concern | PICK (now, free tier) | UPGRADE (paid) | Why this |
|---|---|---|---|
| Database | **Supabase (PostgreSQL)** | Neon, Railway PG, AWS RDS | Postgres + Auth + storage in one; generous free tier. |
| Auth | **Supabase Auth** | Clerk, Auth.js, custom JWT | **Do NOT build your own auth.** JWT/sessions/social/email handled; Next.js middleware checks session. Saves weeks. |
| Cache | **Upstash Redis** | Redis Cloud, self-host | Serverless, pay-per-request, great free tier, pairs with Vercel/Railway. |

### 3.4 Third-party services (summary; details in their own docs)
| Concern | PICK (now, free) | UPGRADE | Doc |
|---|---|---|---|
| Market data | yfinance (backtest) → **Angel One SmartAPI** (production, free) | TrueData (paid) | [`02-data-layer.md`](./02-data-layer.md) |
| LLM | **Gemini Flash** + OpenRouter (free) | Claude / OpenAI | [`03-ai-llm-layer.md`](./03-ai-llm-layer.md) |
| Payments | — (none in P1) | **Razorpay** (P3) | [`10-roadmap-phases.md`](./10-roadmap-phases.md) |
| Alerts | — (none in P1) | WhatsApp via **Gupshup/MSG91**; SMS via MSG91/Twilio (P2) | doc 13 |

### 3.5 CI/CD & Ops
- **GitHub + GitHub Actions** — lint, type-check, test, deploy. Free.
- **Sentry (free tier)** — error tracking (backend + frontend).
- **Plausible / Umami** — privacy-friendly product analytics; **Vercel Analytics** for web vitals.
- **Docker Compose** — local dev (Postgres + Redis + API) so the stack runs identically on any machine.

---

## 4. Environment & config conventions

- All secrets in env vars (`.env` local, platform secrets in prod). Never commit keys.
- **Pluggable providers via config**, never hardcoded:
  ```
  DATA_PROVIDER = "yfinance"   # → "angelone" → "dhan"          (doc 02)
  LLM_PROVIDER  = "gemini"     # → "openrouter" → "anthropic"   (doc 03)
  LLM_MODEL     = "gemini-1.5-flash"
  ```
- Generate **TS types from FastAPI's OpenAPI schema** into `packages/shared-types` so frontend and backend never drift.

---

## 5. Why this stack scales fine without changes

- Picks/explanations/backtests are **pre-computed by cron and served from Redis** → zero heavy on-demand compute, near-zero cost scaling. 1 user or 10,000 users read the same cached daily picks.
- The expensive parts (data API, LLM) are called **~5 times/day total**, not per-user → free tiers stay irrelevant until real scale.
- First real bottlenecks (and when to address them) are documented in [`10-roadmap-phases.md`](./10-roadmap-phases.md) and [`13-future-vision.md`](./13-future-vision.md).

---

*Next: [`02-data-layer.md`](./02-data-layer.md) — the market-data dependency, the most important one to get right.*
