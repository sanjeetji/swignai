# 11 — Verification & Testing

> 🧭 **Status:** 🧪 Partial (Phase 0 tests ✅) · **Tier:** ③ Advanced → **Target: 🏆 Best-in-class** · **Phase 0→all** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** How to know each layer actually works — not "the code runs," but "the math is correct, the risk rules are enforced, the track record is honest, and the user flow is sound." For a fintech tool whose moat is trust, a silent calculation bug is worse than a crash. This doc defines what to test per layer and the end-to-end check.

---

## 1. Picker & indicators (`quant/`)

- **Indicator unit tests:** EMA/RSI/MACD/ATR/etc. against **known reference values** (hand-computed or TA-Lib reference fixtures). A wrong RSI silently corrupts every pick.
- **Regime gate tests:** synthetic NIFTY series above/below EMA20 → asserts BULL/NEUTRAL/BEAR and that BEAR yields **zero picks**.
- **Knockout filter tests:** craft inputs that should pass/fail each of the 6 filters individually; assert no partial credit.
- **Scorer tests:** known feature inputs → expected weighted score + breakdown sums to total; ranking order correct.
- **Determinism test:** same inputs → identical output every run (the property the whole moat depends on — doc 00 #1).

## 2. Risk engine (`quant/risk.py`)

Property-based tests (e.g. Hypothesis):
- Position size **never** exceeds 20% of capital per stock.
- Portfolio **heat never exceeds the cap** when guards are applied.
- Every offered trade has **R:R ≥ 2** and a valid stop.
- `qty = floor(risk_amount / R)` exactly; position_size = qty × entry.
- Edge cases: tiny capital, huge price, zero/negative R rejected cleanly.

## 3. Exit engine (`quant/exits.py`)

- Simulated price paths → SL/target/breakeven/trail trigger **at the right level, in the right order**.
- Breakeven move happens at +3% (config); trail locks +3% at +6%.
- **Scratch classification correct** — a breakeven exit is a `scratch`, counted in the denominator (not silently dropped).
- Time-stop fires at max hold window.

## 4. Backtest harness (`backtest/`)

- **No look-ahead test:** assert the engine cannot access bar `t+1` data when deciding on bar `t`; entries fill on `t+1` open.
- **Cost model test:** known trade → expected net P&L after brokerage+STT+charges+slippage.
- **Walk-forward integrity:** test window never overlaps train window; reported metrics come only from test windows.
- **Point-in-time universe:** a name that delisted mid-history is included up to delisting, excluded after — no survivorship leak.
- **Regime segmentation:** per-regime metrics sum/reconcile to totals.

## 5. LLM / templates (`llm/`)

- **Snapshot tests** on generated explanations: **<60 words**, **disclaimer present**, **no imperative buy/sell** language (doc 09), ≈60/40 Hindi/English.
- **Fallback test:** simulate LLM failure → template is used, pipeline doesn't break (doc 07 §4).
- **No-number-origination guard:** the prompt only ever passes final numbers; add a test that the LLM output's quoted figures match the input pick (catch hallucinated numbers).
- **Human Hinglish review** before committing a model choice (quality can't be fully unit-tested) — read as a Hindi speaker would.

## 6. Track record honesty (the most important test)

- **Recompute `win%` independently** as `wins / (wins + losses + scratches)` and assert it **equals the displayed number exactly.** No code path may exclude scratches (doc 00 #2).
- Expectancy, profit factor, drawdown recomputed from the raw trade log match the stored/displayed analytics.
- Public `/track-record` numbers reconcile to `ai_picks` outcomes — auditable end to end.

## 7. Paper-trading engine & API (`paper/`, `routers/`)

- Buy enforces all server-side risk guards (rejects over-heat, over-concentration, R:R < 2, untrusted client size) — doc 07 §2.
- Capital correctly deducted/restored on open/close; P&L and r_multiple match hand-calc.
- Auth: protected endpoints reject missing/invalid JWT; users can't read others' trades (Supabase RLS, doc 06 §5).
- Idempotency on buy (no double-open from double-submit).

## 8. Frontend

- Component tests for the risk calculator (blocks invalid sizes, shows why).
- `middleware.ts`: unauth → login with callback preserved; admin routes reject non-admins.
- Public pages render with `noindex` on private routes; structured data present on SEO pages.
- E2E (Playwright): signup → see picks → paper-trade a pick → exit → analytics update.

## 8b. Platform-control layers (docs 14–20)

**RBAC & security (doc 19):**
- Every admin/sensitive endpoint rejects callers lacking the required permission (server-side) — test each role against each route.
- Admin 2FA enforced; step-up/re-auth required for secrets, blocking, role changes.
- Rate limiting + lockout fire under brute-force; CORS/TLS/secure-cookie config verified.

**Sessions & user control (doc 18):**
- Force-logout invalidates the session immediately (next request → re-auth).
- Block denies at the API gate + force-logs-out; unblock restores access; all transitions audit-logged.
- Session tracking records IP→city/region + device; geo lookups cached; **request latency not degraded** (perf assertion).
- Impersonation is banner-flagged, time-boxed, and audit-logged; cannot perform unlogged financial actions.
- Audit log is **append-only** (no update/delete path).

**Secrets vault (doc 17):**
- Secrets stored encrypted (ciphertext in DB); plaintext never in DB, logs, Sentry, or client responses.
- Test-Connection performs a real provider call; rotation takes effect on next call; reveal requires re-auth.

**i18n (doc 15):**
- **Coverage check:** no hardcoded user-facing strings (lint/CI); every key resolves in EN + HI; missing key → EN fallback, logged.
- ₹/number/date formatting locale-correct (Indian grouping); Devanagari renders.

**Theming (doc 14):**
- Theme/font/locale resolution = user override → admin default → fallback; **admin lock** forces the axis; no flash of wrong theme (pre-hydration).
- All contrast pairs pass WCAG AA in every preset (light + dark); `prefers-reduced-motion` honored.

**Business metrics (doc 20):**
- MRR/ARR/churn/cohort numbers **reconcile to source** (`subscriptions`/`payments`); revenue matches realized payments — no vanity inflation.
- User personal analytics headline = expectancy; win% = wins/(wins+losses+scratches) (matches §6).

**No-hardcoded-data audit (engineering principle, doc 00 §8.5):**
- Grep/lint gate: no mock/static data arrays in components, no hardcoded strings/colors/secrets. Every screen has real loading/empty/error states wired to an API.

**Event logs (doc 22):**
- `emit()` is fire-and-forget: an emit failure **never** breaks the request; an event rolls back with its caller's transaction (no log for an action that didn't happen).
- Events carry correct category/level/actor/`request_id`; SYSTEM events (no actor) record; related events group by `request_id`.
- **Append-only:** no UPDATE/DELETE path; retention TTL purges per policy; optional hash-chain verifies.
- Secrets' *values* never appear in any event payload/before/after.
- Audit-log view = event-log filtered to `category in (admin, security)`; alert rules fire on configured patterns (e.g. N failed logins/IP).

**DPDP (doc 09):**
- Consent recorded at signup; data export + account deletion work end-to-end; retention TTL purges old session/geo/login/event logs; `data_subject_requests` track statutory `due_at`.

**Marketing CMS (doc 21):**
- **SEO render check (critical):** marketing pages render content in **server HTML** (view-source shows it), not client-fetched — assert content + `seo_meta`/JSON-LD present in SSR output.
- Publishing triggers **on-demand revalidation** (page updates without redeploy); drafts are `noindex` + token-gated.
- **Seed check:** fresh DB → site renders real seeded pages/blocks/testimonials/stats; reseed is idempotent (won't clobber edits).
- Block content validated against per-type schemas; rich text sanitized (no script injection).
- **Versioning/rollback** restores prior content; live-bound stats show **real backend numbers** (no fabricated figures).
- Dynamic page creation → new slug routable + SEO-managed; sitemap/robots reflect published pages.
- CMS routes RBAC-gated + audit-logged.

## 9. End-to-end pipeline check (staging)

One pick flows the whole path:
```
data → picker → trade plan → LLM/template explain → ai_picks (DB) → Redis cache
     → /api/daily-picks → dashboard card → paper-trade buy → exit_checker closes
     → analytics recompute → /track-record reflects outcome
```
Run it on a staging environment with a known historical day and assert each hop's output.

## 10. CI gates (GitHub Actions)

- Lint + type-check (mypy/ruff for Python; tsc/eslint for TS).
- Unit + property tests must pass.
- Migrations apply cleanly on a fresh DB.
- Block merge on red. Snapshot/Hinglish reviews are manual but tracked.

---

## What "verified" means per phase

- **Phase 0:** backtest passes §4; expectancy positive net of costs out-of-sample (the real gate, doc 05).
- **Phase 1:** §1–8 green; E2E §9 passes; track-record honesty §6 proven.
- **Phase 2+:** add alert delivery tests, SEO structured-data validation, load/caching checks.

---

*Next: [`12-decisions-and-risks.md`](./12-decisions-and-risks.md) — the decision log and the risks to keep watching.*
