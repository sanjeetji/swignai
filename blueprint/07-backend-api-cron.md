# 07 — Backend: API, Cron & Error Handling

> 🧭 **Status:** 🧪 Partial (quant+CLI built; FastAPI/cron pending) · **Tier:** ③ Advanced → **Target: 🏆 Best-in-class** · **Phase 0→1** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** The FastAPI backend is the "quant brain." It runs the daily pipeline (compute picks → narrate → store → cache), serves cached data to the frontend, and runs the paper-trading engine. This doc defines the endpoints, the scheduled jobs, and the error-handling contract (which is not optional — a fintech tool that silently serves stale/wrong data destroys trust).

---

## 1. Design principles

- **Heavy compute happens in cron, not in request handlers.** Picks, explanations, and backtests are pre-computed and cached in Redis. Endpoints are thin readers → near-zero latency, near-zero cost scaling (1 user or 10,000 read the same cached daily picks).
- **Stateless API**, JWT-authenticated via Supabase. Public endpoints need no auth; private ones validate the Supabase JWT; admin ones check `is_admin`.
- **Every external call (data, LLM) is wrapped** with retry + fallback (§4).

---

## 2. Endpoints

### Public (no auth — these also power SEO pages)
```
GET  /api/daily-picks            → today's cached top picks (+ regime banner)
GET  /api/stocks/{symbol}        → analysis for the SEO page (latest pick + indicators)
GET  /api/sectors/{sector}       → sector analysis aggregate
GET  /api/backtest?from=&to=     → cached backtest results (expectancy, log) for /backtest tool
GET  /api/track-record           → honest public scorecard (R-based, net, all trades incl. scratches)
GET  /api/regime                 → today's market regime + plain-language reason
```

### Authenticated (Supabase JWT)
```
POST /api/paper-trade/buy        → {symbol, entry, stop_loss, target, quantity, entry_reason}
                                    → validate risk guards → deduct virtual capital → store (status=open)
POST /api/paper-trade/{id}/close → {exit_price, exit_reason} → compute pnl + r_multiple → close
GET  /api/paper-trade/{id}       → single trade
GET  /api/portfolio              → open trades, total P&L, current portfolio heat, capital remaining
GET  /api/analytics              → personal expectancy, win%, profit factor, discipline score, best sector
GET  /api/me                     → user profile + capital + risk settings
PATCH /api/me                    → update capital_amount / risk_pct / preferences
```

### Admin (RBAC permission-gated — doc 19; full-page UIs in docs 16–20)
```
# Health & pipeline
GET  /api/admin/health                    → pipeline status, job runs, integration health
POST /api/admin/override-pick             → adjust/suppress a pick (audit-logged)
POST /api/admin/rerun-pipeline            → re-trigger daily pipeline (idempotent)

# Appearance / settings / flags (docs 14–16)
GET/PUT /api/admin/settings               → platform_settings (theme/font/locale defaults, locks, maintenance)
GET/POST/PUT/DELETE /api/admin/theme-presets
GET/PUT /api/admin/feature-flags

# Integrations & secrets vault (doc 17) — secrets never returned to client
GET  /api/admin/integrations              → list (masked status only)
PUT  /api/admin/integrations/{provider}   → save/rotate credentials (encrypted), re-auth required
POST /api/admin/integrations/{provider}/test → live connection test

# Users, sessions, blocks, impersonation (doc 18)
GET  /api/admin/users                     → list (server-side search/filter/sort/paginate)
GET  /api/admin/users/{id}                → detail (profile, sessions, activity)
GET  /api/admin/users/{id}/sessions
POST /api/admin/users/{id}/force-logout   → revoke session(s)
POST /api/admin/users/{id}/block          → block (reason) + force-logout
POST /api/admin/users/{id}/unblock
POST /api/admin/users/{id}/impersonate    → start "view as" (audit-logged, time-boxed)
PUT  /api/admin/users/{id}/role           → change role (permission-gated, re-auth)

# Event logs & audit (doc 22) — audit-log = event-log filtered to category in (admin,security)
GET  /api/admin/event-logs                → unified stream, filter/search/paginate (server-side)
GET  /api/admin/event-logs/{id}           → detail + before/after diff + related (by request_id)
GET  /api/admin/event-logs/stream         → SSE/WebSocket live tail
GET  /api/admin/event-logs/export         → CSV/JSON of filtered set
...  /api/admin/event-logs/{alert-rules|saved-filters}
GET  /api/admin/audit-log                 → = event-logs?category=admin,security
GET  /api/admin/metrics                   → MRR/ARR/ARPU/LTV/churn/cohorts/DAU-WAU-MAU

# Marketing CMS (doc 21) — content + per-page SEO, drafts/publish/rollback
GET/POST/PUT/DELETE /api/admin/cms/pages          → pages (create dynamic pages)
PUT  /api/admin/cms/pages/{id}/sections           → block composer (reorder/edit/toggle)
GET/PUT /api/admin/cms/pages/{id}/seo             → per-page SEO + JSON-LD
POST /api/admin/cms/pages/{id}/publish            → snapshot version + revalidate path
GET  /api/admin/cms/pages/{id}/preview            → draft preview (token, noindex)
POST /api/admin/cms/pages/{id}/rollback           → restore a content_version
...  /api/admin/cms/{categories|testimonials|stats|faqs|navigation|media|seo-defaults}
```

### Public CMS (rendered server-side; doc 21)
```
GET  /api/cms/page/{slug}        → published page + sections + seo_meta (for ISR render)
GET  /api/cms/categories/{slug}  → category + content items
GET  /sitemap.xml  /robots.txt  /llms.txt   → auto-generated from published content
```
> Next.js server components read these (or the DB directly) and render via ISR; `generateMetadata()` pulls `seo_meta`. Publishing triggers on-demand revalidation — no redeploy.

### User self-service (authed) — settings & privacy (docs 14–15, 18–19)
```
GET/PUT /api/me/preferences   → theme_mode/preset/font/locale override (if not admin-locked)
GET  /api/me/sessions         → own active sessions; POST .../logout-all
POST /api/me/2fa/...          → enable/verify 2FA
GET  /api/me/export           → DPDP data export
DELETE /api/me                → DPDP account deletion (right to erasure)
```

### Platform (public)
```
GET  /api/platform/appearance → resolved public defaults (presets/fonts/locales) for first paint
```

### Validation rules on `POST /api/paper-trade/buy` (the risk engine, enforced server-side)
- Reject if it would breach **max open positions**, **20% per-stock cap**, or **portfolio heat cap** (doc 04 §5).
- Reject if **R:R < 2** or no valid stop.
- Recompute `position_size` server-side from the user's capital + `risk_pct`; don't trust client-sent size.
- All enforcement is server-side — the UI guidance is convenience, the API is the gate.

---

## 3. Cron jobs (IST)

| Time | Job | Action |
|---|---|---|
| **3:30 PM** | `daily_pipeline` | Gate 0 regime → run picker funnel (doc 04) → compute trade plans → LLM/template explain (doc 03) → upsert `ai_picks` → write `regime_log` → cache picks in Redis |
| **3:45 PM** | `exit_checker` | For every **open** paper trade: fetch price → apply exit rules (SL/target/breakeven/trail, doc 04 §6) → close or update → recompute P&L |
| **nightly** | `update_old_picks` | Resolve still-open `ai_picks` against real prices → set `actual_result`, `actual_r_multiple` → updates the public track record |
| **nightly** | `recompute_analytics` | Rebuild `user_analytics` (expectancy, win% = wins/(wins+losses+scratches), profit factor, discipline score) |
| **weekly (Mon AM)** | `seo_content` | Generate "Top swing setups this week" blog from real data (LLM, doc 03) → `blog_posts` |
| **nightly** | `recompute_metrics` | Materialize MRR/ARR/cohorts/retention/DAU → `platform_metrics` (doc 20) |
| **hourly** | `integration_health` | Test critical integrations → update status, alert on failure (doc 17) |
| **nightly** | `retention_cleanup` | Expire old sessions + purge session/geo/login logs past DPDP TTL (docs 18, 19) |
| **Phase 2+** | `alerts_dispatch` | Push WhatsApp/SMS when a target/SL is hit (doc 13) |

**Scheduler:** APScheduler in-process **or** Railway/Render native cron (preferred for isolation). Not Celery until scale demands it.

**Idempotency:** `daily_pipeline` upserts on `(stock_symbol, date_generated)` — safe to re-run.

---

## 4. Error-handling contract (NOT optional)

Anticipate failure at every external boundary. A swing tool that serves wrong/stale data silently is worse than one that's honestly down.

| Failure | Handling |
|---|---|
| **Data API rate limit / timeout** (yfinance, Angel One) | Exponential backoff + retry → failover to fallback provider (doc 02) → serve last-good cached bar flagged stale → if pipeline can't get data, **don't publish picks**; alert admin |
| **Redis connection failure** | Fall back to reading from Postgres; degrade gracefully (slower, not broken); never 500 the whole page |
| **LLM failure / rate limit / bad output** | Fall back to **template explanation** (doc 03 §5); never block a pick on the narration |
| **Partial pipeline failure** | Per-stock isolation — one stock erroring must not kill the whole run; log the failure, continue with the rest |
| **Paper-trade race / double-submit** | Idempotency key on buy; DB constraints; reject duplicate open of same symbol if business rule says so |
| **Bad market data tick** | Reject implausible bars (doc 02 §4); don't act on them in exit_checker |

**Observability:** every job logs start/end/duration/row-counts; all exceptions → **Sentry**; `/api/admin/health` surfaces last-run status of each job and each data source. A failed `daily_pipeline` should page you (no picks = visible problem).

---

## 5. Caching keys (Redis)

```
picks:YYYY-MM-DD                → today's picks payload (TTL ~24h)
explanation:{pick_id}           → Hinglish text (TTL 24h)
quote:{symbol}                  → latest price (TTL seconds–minutes)
ohlcv:{symbol}:{interval}       → bars (TTL until next close)
backtest:{params_hash}          → backtest result (TTL long; recompute on demand/cron)
track_record                    → public scorecard payload (TTL until nightly recompute)
```

---

## 6. Module layout (`apps/api/`)

```
api/
├── core/        # settings, config (DATA_PROVIDER, LLM_PROVIDER…), db session, redis client, security(JWT)
├── data/        # market data providers (doc 02)
├── quant/       # picker, indicators, regime, risk, exits (doc 04)
├── backtest/    # validation harness (doc 05)
├── llm/         # pluggable LLM + templates (doc 03)
├── paper/       # paper-trading engine (buy/close/portfolio/heat)
├── models/      # SQLAlchemy models (doc 06)
├── schemas/     # Pydantic request/response
├── routers/     # daily_picks, stocks, backtest, track_record, paper, analytics, admin
├── jobs/        # daily_pipeline, exit_checker, update_old_picks, recompute_analytics, seo_content
└── main.py      # FastAPI app, router registration, middleware, scheduler bootstrap
```

---

## 7. Middleware stack (request pipeline)

Applied to authenticated requests, in order — fast, async, must not slow the request:
1. **Auth:** validate Supabase JWT; derive `user_id` from token (never trust client).
2. **Block gate:** reject if user is blocked (`user_blocks`, doc 18) → 403 + force re-auth.
3. **RBAC:** check the route's required permission against the user's roles (doc 19).
4. **Session tracking:** upsert `user_sessions` (last_active, device from UA) + resolve **IP → city/region/ISP** via cached geo lookup; write `login_history` on auth events (doc 18). Throttled/async; geo cached in Redis.
5. **Rate limiting:** Redis-backed counters on auth + sensitive + public endpoints (doc 19).
6. **Correlation id:** assign a `request_id` per request/job and thread it through so all emitted **event-log** entries (doc 22) of one request/job correlate for tracing.

> **Event emission:** modules call the fire-and-forget `event_log.emit(...)` helper after noteworthy actions (auth, admin changes, integration access, pipeline steps, risk-guard blocks) — caller-commit semantics, never breaks the request path (doc 22 §4).

## 8. Security essentials

- Validate Supabase JWT on every authed route; never trust client-sent `user_id`.
- **RBAC permission checks server-side** on every admin/sensitive endpoint (doc 19) — UI hiding is not security.
- **Admin 2FA + step-up re-auth** for secrets, blocking, role changes (doc 19).
- **Secrets:** encrypted vault (doc 17); decrypt backend-only at call time; never returned to client, never logged (scrub from Sentry).
- **RLS** so users touch only their own rows; service key backend-only (doc 06/19).
- Rate-limit + brute-force lockout; CORS locked to the web origin; TLS/HSTS, secure cookies.
- All privileged actions **audit-logged** append-only (doc 18).

---

*Next: [`08-frontend-seo.md`](./08-frontend-seo.md) — the Next.js routes, rendering strategy, and SEO engine.*
