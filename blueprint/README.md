# SwingAI — Documentation

> 🧭 **Status:** ✅ Living index · **Tier:** — → **Target: 🏆 Best-in-class** · **Phase all** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Single source of truth for building the entire SwingAI platform.**
> If development stops at any point, read these docs and resume from the exact phase.
> Written as a senior architect + quant/swing-trading specialist. Honest over optimistic.

SwingAI is **a risk-management and discipline platform that also gives swing-trade stock ideas** — *not* a tip service that mentions risk. Read [`00-overview-philosophy.md`](./00-overview-philosophy.md) first; it explains why that one distinction shapes everything.

---

## 📚 How to read these docs

Start at `00` and go in order if you're new. Otherwise jump to the doc for the layer you're working on. **Every doc is self-contained** with its own context header, so each one reads on its own.

| # | Doc | What it covers | Phase(s) |
|---|---|---|---|
| — | [README.md](./README.md) | This index + phase map + resume pointer | All |
| 00 | [00-overview-philosophy.md](./00-overview-philosophy.md) | The thesis, 3 non-negotiables, the 4 layers, KPI = expectancy | All |
| 01 | [01-architecture-techstack.md](./01-architecture-techstack.md) | One-monolith decision, monorepo layout, full tech stack + alternatives | All |
| 02 | [02-data-layer.md](./02-data-layer.md) | Market data: yfinance → Angel One → TrueData; pluggable; free→paid | P0→P3 |
| 03 | [03-ai-llm-layer.md](./03-ai-llm-layer.md) | LLM: Gemini/OpenRouter free → Claude/OpenAI → multi-agent; templates | P1→future |
| 04 | [04-picker-strategy.md](./04-picker-strategy.md) | Deterministic 4-stage funnel, all parameters, risk engine, exits; ML later | P0→P3 |
| 05 | [05-validation-backtest.md](./05-validation-backtest.md) | Phase 0 harness: point-in-time, no look-ahead, net-of-cost, walk-forward | P0 |
| 06 | [06-database-schema.md](./06-database-schema.md) | Postgres tables (picks, paper trades, analytics, subscriptions, future) | All |
| 07 | [07-backend-api-cron.md](./07-backend-api-cron.md) | FastAPI endpoints + cron jobs + error handling | All |
| 08 | [08-frontend-seo.md](./08-frontend-seo.md) | Next.js routes/rendering + SEO engine + dashboard + admin | All |
| 09 | [09-compliance-sebi.md](./09-compliance-sebi.md) | "Analysis not advice" framing, lawyer sign-off, RA license, F&O rules | All |
| 10 | [10-roadmap-phases.md](./10-roadmap-phases.md) | **FULL Phase 0→4 granular checklists** + costs + key question per phase | All |
| 11 | [11-verification-testing.md](./11-verification-testing.md) | How to verify each layer actually works | All |
| 12 | [12-decisions-and-risks.md](./12-decisions-and-risks.md) | ADR decision log + open risks | All |
| 13 | [13-future-vision.md](./13-future-vision.md) | **Advanced/futuristic**: ML scoring, real-time alerts, sentiment AI, multi-agent, F&O, broker execution, community, AI chat, mobile, adaptive risk | P3→future |
| 14 | [14-design-system-ui-ux.md](./14-design-system-ui-ux.md) | Theme presets, light/dark/system, fonts, animations, charts, responsive-first, a11y, perf budget | All |
| 15 | [15-internationalization.md](./15-internationalization.md) | Multi-language EN+HI, extensible (next-intl), ₹/date formatting, SEO hreflang | All |
| 16 | [16-admin-control-panel.md](./16-admin-control-panel.md) | Super Admin control plane: global theme/font/language defaults + lock, feature flags, maintenance, full-page screens | All |
| 17 | [17-integrations-secrets.md](./17-integrations-secrets.md) | Encrypted API-key/secret vault for all integrations, test-connection, rotate | All |
| 18 | [18-user-management-sessions.md](./18-user-management-sessions.md) | Track users, sessions, IP/city/device; force-logout, block/unblock, impersonate, audit log | All |
| 19 | [19-rbac-security.md](./19-rbac-security.md) | Roles + permissions, admin 2FA, secret encryption, rate limiting, DPDP, backups | All |
| 20 | [20-business-analytics.md](./20-business-analytics.md) | Role-based dashboards: revenue, MRR, ARR, churn, LTV, cohorts (admin) vs personal performance (user) | All |
| 21 | [21-marketing-cms.md](./21-marketing-cms.md) | Dynamic admin-controlled marketing site: block-based content, per-page SEO + JSON-LD, testimonials/stats/categories, dynamic pages, seed-then-edit, versioning | All |
| 22 | [22-event-logs.md](./22-event-logs.md) | Unified Super Admin event log (security/admin/system/integration/product/compliance) — `emit()` helper, correlation IDs, before/after diffs, live tail, alert rules, retention | All |
| — | [STATUS.md](./STATUS.md) | **Living tracker** — done/pending + maturity tier (basic→best-in-class) per feature; target = best-in-class | All |
| — | [HOW-TO-BUILD.md](./HOW-TO-BUILD.md) | **Build order, setup, and the RESUME PROMPT** to continue from any paused state | — |
| — | [OMNIMARK-REUSE.md](./OMNIMARK-REUSE.md) | What to **reuse/adapt/build-fresh** from your OmniMark Pro project (vault, RBAC, audit, CMS, theming, deploy) | — |
| — | [../brand/BRAND.md](../brand/BRAND.md) | Platform name, naming/domain decision, and the **one-command rename** procedure | — |

> Every doc carries a 🧭 **status badge** at the top (done/pending + maturity tier). Authoritative roll-up: [STATUS.md](./STATUS.md). **Folder note:** this `blueprint/` folder (renamed from `docs/`) is the living R&D / build spec.

---

## 🗺️ Phase map (at a glance)

| Phase | Window | Goal / Key question | Users | Cost |
|---|---|---|---|---|
| **0 — Validate** | Weeks 1–2 build → 90-day public run | *Does the strategy have real, net-of-cost edge?* | just you | ~₹5k total |
| **1 — MVP** | Months 1–4 | *Positive live expectancy? Do testers return?* | you + 20 | ₹800–1,500/mo |
| **2 — Beta** | Months 5–8 | *Do users check 4+ days/week?* | 100–500 | low |
| **3 — Business** | Months 9–18 | *Real revenue (subscriptions)?* | 1k–10k | scales |
| **4 — Scale + F&O** | Month 18+ | *Expand once swing is proven* | 10k+ | scales |

Full per-phase checklists live in [`10-roadmap-phases.md`](./10-roadmap-phases.md).

---

## ✅ Resume pointer (update this as you go)

- **Current status:** Docs complete. **Phase 0 harness BUILT & passing** (`backend/` — quant + backtest + 23 tests; synthetic backtest runs). See [`HOW-TO-BUILD.md`](./HOW-TO-BUILD.md) §3 for the live ledger.
- **Next code action:** **run the REAL-DATA backtest** (`cd backend && pip install yfinance && python -m app.cli backtest --days 600`) — the Phase-0 go/no-go gate. Then iterate `config.py` or proceed to Phase 1.
- **Exit criterion for Phase 0:** positive walk-forward expectancy *net of costs* + early audience signal. If not met → rework strategy or stop. This is the highest-risk unknown in the whole project.
- **To start or resume building:** see [`HOW-TO-BUILD.md`](./HOW-TO-BUILD.md) — it has the build order, the live **progress ledger** (§3), and the **copy-paste RESUME PROMPT** (§4) to continue from any paused state.

---

## ⚠️ The 3 non-negotiables (never violate)

1. **The picker is deterministic math, never AI.** Only deterministic logic is backtestable — and the honest track record is the entire moat.
2. **The track record is honest.** wins / (wins + losses + scratches), net of costs, in R-multiples. No metric massaging.
3. **Framing is "analysis/education," not "buy/sell advice."** SEBI regulates advice, not execution. "We don't execute" is NOT a legal shield. Lawyer sign-off before public launch.

## 🛠️ Engineering principles (platform-wide)

- **No dummy/static/hardcoded data.** Every screen is wired to a real backend/API endpoint with real loading/empty/error states. No mock rows, no hardcoded strings (i18n), no hardcoded colors (theme tokens), no hardcoded secrets (vault).
- **Role-based product.** Super Admin (platform control + business analytics) vs Normal User (trading) — enforced server-side via RBAC (doc 19).
- **Secure by default.** RBAC + admin 2FA + encrypted secrets + RLS + rate limiting + audit log + DPDP compliance (docs 17–19).
- **Multi-language + multi-theme from day one.** EN + HI (extensible), curated theme presets + light/dark/system, admin-default with user-override (docs 14–16).

*Docs v1.0 — generated as the master build spec for SwingAI.*
