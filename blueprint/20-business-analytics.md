# 20 — Business Analytics & Role-Based Dashboards

> 🧭 **Status:** 📝 Spec · **Tier:** 🏆 Best-in-class (design) → **Target: 🏆 Best-in-class** · **Phase 1→3** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** The platform shows **different dashboards by role** — the Super Admin sees platform-wide business health (revenue, MRR, ARR, churn, cohorts, growth), while a Normal User sees their personal trading performance. This doc defines both, the metric definitions (computed correctly from real data — no vanity or fake numbers), and the data sources. Everything is **backend-computed from live tables** (doc 06); nothing is hardcoded.

---

## 1. Two dashboards, one platform

| | **Super Admin** (`/admin`, doc 16) | **Normal User** (`/dashboard`, doc 08) |
|---|---|---|
| Purpose | Run the business | Improve their trading |
| Headline | Revenue, MRR, ARR, active users, churn | **Expectancy (avg R)**, P&L, discipline score |
| Data scope | Platform-wide (all users) | Their own data only (RLS-enforced, doc 19) |
| Access | `analytics.view` permission (RBAC) | Self only |

Both are role-gated server-side; a user can **never** see platform/other-user data.

---

## 2. Super Admin — business metrics

> Computed from `subscriptions`, `payments`, `users`, `user_sessions` (doc 06) by a nightly metrics job (doc 07) + on-demand queries. Definitions below are the honest, standard SaaS formulas.

**Revenue & recurring:**
| Metric | Definition |
|---|---|
| **MRR** (Monthly Recurring Revenue) | sum of normalized monthly subscription value of active subs |
| **ARR** (Annual Recurring Revenue) | `MRR × 12` |
| **New / Expansion / Churned / Net MRR** | MRR movements this period (new subs, upgrades, downgrades, cancellations) |
| **ARPU** | revenue ÷ active users |
| **LTV** | ARPU ÷ churn rate (or cohort-based) |
| **Total revenue** | realized payments over a period (gross + net of refunds) |

**Growth & retention:**
| Metric | Definition |
|---|---|
| **Active users** | DAU / WAU / MAU (from `user_sessions`/activity) |
| **Signups** | new users per period |
| **Free→Paid conversion** | paid ÷ total (track honestly — Indian fintech is low, doc 00) |
| **Churn rate** | cancelled ÷ active at period start (logo + revenue churn) |
| **Retention / cohorts** | % of a signup cohort still active over weeks/months |
| **Trial→Pro funnel** | step conversion through onboarding → first paper trade → subscribe |
| **Engagement** | % checking 4+ days/week (the Phase-2 key question, doc 10) |

**Operational health (on the overview):**
- Daily-pipeline status, integration health (docs 07, 17), error rate (Sentry), data-source status.
- Subscription mix by tier; refunds; failed payments (P3).

**Product/edge metrics (honest — ties to the moat):**
- Platform-wide **track-record expectancy / win% (incl. scratches)** — the public honest number (doc 00 #2).
- Pick → paper-trade adoption; average user discipline score trend.

---

## 3. Normal User — personal dashboard

> Their own data from `paper_trades`, `user_analytics` (doc 06). Headline is **expectancy, not win rate** (doc 00).

- **Expectancy (avg R)** — the headline KPI.
- P&L (₹ and %), profit factor, max drawdown, win% = wins/(wins+losses+scratches).
- Avg holding days, best sector, R:R achieved.
- **Discipline score** + post-trade review insights ("you exited winners early").
- **Equity curve** + per-trade R chart (doc 14 charts).
- Open positions, portfolio heat, capital remaining.
- Subscription status + usage vs tier limits.

This is Layers 1–2 made visible (doc 00) — the retention engine.

---

## 4. Data sources & computation

- **Source tables:** `subscriptions`, `payments`, `users`, `user_sessions`, `paper_trades`, `user_analytics`, `ai_picks` (doc 06).
- **Nightly metrics job** (doc 07) materializes heavy aggregates (MRR/ARR/cohorts/retention) into a metrics store/cache (Redis + a `platform_metrics` snapshot) so dashboards load instantly — **pre-computed, not heavy on-demand** (consistent with the platform's caching philosophy, doc 01).
- **Time-series** kept for trend charts (MRR over time, DAU over time).
- All numbers **reconcile to source data** and are **verifiable** (doc 11) — no inflated/vanity figures. Revenue reconciles to actual `payments`.

---

## 5. Visualization (doc 14)

- `KpiStatCard` with sparkline + count-up animation for MRR/ARR/active users.
- Recharts: MRR-over-time, revenue waterfall (new/expansion/churn), retention cohort heatmap, funnel chart, DAU/WAU/MAU.
- Responsive + theme-tokenized; touch-friendly on mobile (doc 14).
- Date-range + segment filters (by tier/cohort/region), server-driven.

---

## 6. Honest guardrails (don't fool yourself)

- **MRR/ARR are forward-looking estimates**, not cash in the bank — show realized revenue alongside.
- **Vanity-metric warning:** track the metrics that predict survival — **conversion, churn, retention, engagement, expectancy** — not just signups. Signups without retention is a leaking bucket (doc 12 R3 distribution risk).
- **Conversion reality:** Indian fintech free→paid is typically 2–4%; the dashboard should make this visible so growth targets stay grounded (doc 00 §8).
- The **public track record** number shown here is the same honest one users see — never a separate "internal" massaged figure (doc 00 #2).

---

## 7. Phase evolution

| Phase | Deliverable |
|---|---|
| 1 | User personal dashboard (expectancy, P&L, discipline, equity curve); admin overview (active users, signups, pipeline/integration health) — pre-revenue |
| 2 | Engagement/retention/cohort analytics, funnel, DAU/WAU/MAU; track-record expectancy platform-wide |
| 3 | **Full revenue suite: MRR, ARR, ARPU, LTV, churn, expansion, refunds** (with Razorpay live), tier mix, forecasting |
| Future | Predictive churn, LTV modeling, A/B test analytics, attribution, exportable BI / data warehouse |

---

*End of the admin/platform docs. Back to the [README index](./README.md).*
