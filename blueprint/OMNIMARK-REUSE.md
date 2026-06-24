# OMNIMARK-REUSE — Reusing patterns from the OmniMark Pro project

> 🧭 **Status:** ✅ Reference · **Tier:** — → **Target: 🏆 Best-in-class** · **Phase —** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** You have a mature, working project — **OmniMark Pro** (an AI marketing/sales/analytics platform) — built on the same kind of stack SwingAI needs. This doc maps **what to reuse, adapt, or build fresh** for SwingAI, based on a direct read of the OmniMark `feat-integration-imporvments` branch. It turns "copy my other project" into a concrete, honest plan.
>
> **How this was produced:** the public repo was cloned and inspected (structure, `package.json`s, `requirements.txt`, `backend/app/db/models.py` table list, services). Exact file-level adaptation happens at build time — clone OmniMark into the workspace when building so its code is readable.

---

## 1. Headline: OmniMark validates the SwingAI architecture — with ONE correction

OmniMark is a **Turborepo monorepo** with **two separate Next.js apps** (`apps/marketing` + `apps/dashboard`) sharing `packages/ui` + `packages/api-client`, backed by **one FastAPI service** (`backend/`). Its own README says the split exists *"so we can ship marketing changes daily and hit Lighthouse 100."*

**This is a better-evidenced approach than the single-monolith I originally recommended** (doc 01) — and since you want to reuse OmniMark, SwingAI should **match this structure**. See the revised decision in [`01-architecture-techstack.md`](./01-architecture-techstack.md) §1. (One repo, two Next apps, shared packages; one domain still achievable via routing/subdomain.)

---

## 2. Confirmed stack overlap (SwingAI docs were right)

| Area | OmniMark uses | SwingAI doc | Status |
|---|---|---|---|
| Monorepo | Turborepo + npm workspaces, `apps/*` + `packages/*` | 01 | ✅ matches (add Turborepo) |
| Backend | FastAPI + **async** SQLAlchemy 2.0 + Alembic + asyncpg | 01, 07 | ✅ matches (note: async) |
| Workers | Celery + Redis | 07 | OmniMark uses Celery; SwingAI can start with APScheduler, adopt Celery at scale |
| Auth | python-jose (JWT) + passlib/bcrypt | 19 | ✅ matches |
| Theming | **next-themes** (dark/light/system) | 14 | ✅ exact |
| Animation | **Framer Motion** | 14 | ✅ exact |
| UI | **shadcn + Tailwind + cva + tailwind-merge + tw-animate-css + lucide** | 14 | ✅ matches |
| Data/state | **TanStack Query + TanStack Table + Zustand** | 01, 08 | ✅ exact |
| Charts | **Recharts + @tremor/react** | 14, 20 | ✅ matches (Tremor is a nice add for analytics) |
| Toasts | **sonner** | 14 | ✅ add |
| Next.js | 14.x (App Router) | 01 | ✅ matches |

**Takeaway:** the SwingAI tech-stack docs are well-aligned with your proven choices. Minor additions folded in: **Tremor** (analytics widgets), **sonner** (toasts), **async SQLAlchemy**, **Turborepo**.

---

## 3. Directly reusable infrastructure (copy → adapt)

These OmniMark modules solve exactly what SwingAI's admin/security/CMS docs specify. Reuse them rather than rebuilding.

| SwingAI need (doc) | OmniMark source (path) | Reuse level |
|---|---|---|
| **Encrypted secrets vault** (17, 19) | `backend/app/core/secrets.py`, `backend/app/services/secret_box.py` + envelope encryption (DEK / `data_encryption_keys`) | **Reuse** — this is the exact vault pattern; adapt provider list |
| **API-key / integrations management** (17) | tables `integrations`, `platform_integrations`, `platform_integration_usage`, `integration_directory`; services `api_keys_service.py`, `ai_keys_service.py`, `ai_config_service.py` | **Reuse/adapt** — swap providers to LLM+market-data |
| **RBAC** (19) | `roles` table (+ permissions), auth/JWT, 2FA via `pyotp` + `qrcode` | **Reuse** — same model |
| **Audit log** (18) | `audit_logs` / `audit_log_events` tables, `audit_log_service.py`, `audit_service.py` | **Reuse** |
| **Event logs** (22) | `audit_logs` (with `level`/`category`/`location` + SYSTEM events), `security_events` + `security_event_service.py` (`emit()` fire-and-forget), `data_subject_requests` | **Reuse the pattern** — adapt to unified `event_logs`; add trading event types, request_id tracing, live tail, alert rules (the "more advanced" parts) |
| **Sessions / visitor tracking** (18) | `visitor_sessions`, `session_recordings` tables | **Adapt** — take session + IP/geo; drop recordings unless wanted |
| **Platform settings** (16) | `platform_settings`, `system_settings_kv` | **Reuse** — add theme/font/locale defaults + locks |
| **Marketing CMS** (21) | `testimonials`, `content_posts`, `content_categories`, `landing_pages`, `seo_*` tables; CMS editing via **TipTap** + **@hello-pangea/dnd**; admin tables via **TanStack Table** | **Adapt** — take the content/SEO model + editor; map to SwingAI's block model |
| **Analytics dashboards** (20) | Tremor/Recharts widgets, `analytics_advanced.py`, attribution/cohort services | **Adapt** — reuse chart components; swap metrics to MRR/ARR/expectancy |
| **Admin map / IP geo display** (18) | `leaflet` | **Reuse** — for the session location view |
| **Deploy/infra** (01) | `render.yaml`, `docker-compose.yml`, `turbo.json`, `omnimark.sh`, `start-*.sh`, `free-deployment-production/` | **Adapt** — proven Render + Docker + Turbo configs |

---

## 4. Build fresh for SwingAI (NOT in OmniMark)

Be honest about what can't be copied:

- **The entire quant/trading engine** — picker, indicators, regime, risk, exits, backtest, paper trading (docs 04, 05). OmniMark is marketing software; **there is nothing here to reuse.** This is also your #1 risk (doc 12 R1) and the thing that actually matters. Build it first (Phase 0), from scratch.
- **i18n / multi-language (EN+HI).** No i18n/next-intl found in OmniMark (it appears English-only). **Doc 15 is net-new work** — build it fresh; don't expect to copy it.
- **SEBI / DPDP compliance specifics** (doc 09) — India-fintech-specific; new.
- **Market-data layer** (doc 02) — yfinance/Angel One providers; new (OmniMark has marketing-data integrations, different domain).
- **Honest track-record / expectancy** logic (docs 00, 20) — domain-specific; new.

---

## 5. Practical reuse workflow

1. Keep OmniMark cloned in the workspace (e.g. `…/omnimark-ref`) so its code is readable during the build.
2. When building a SwingAI infra unit (vault, RBAC, audit, CMS, theming), **open the matching OmniMark file (§3), copy the pattern, adapt names/providers** to SwingAI, and wire to SwingAI's schema (doc 06).
3. For the trading engine and i18n (§4), build fresh per the docs.
4. Mirror OmniMark's **monorepo + two-Next-app** layout (§1) so shared `packages/ui` and `packages/api-client` can be lifted across with minimal change.
5. Reuse OmniMark's `render.yaml` / `docker-compose.yml` / `turbo.json` as deployment starting points.

---

## 6. Honest caution

OmniMark is **large and feature-dense** (ads, SEO suite, automation, CRM, AI agents — a 6,000-line models file). **Do not import its full scope.** Take the *infrastructure* (vault, RBAC, audit, settings, CMS, theming, charts, deploy) and leave the marketing-domain features behind. Pulling in too much OmniMark surface area would recreate the scope-creep risk (doc 12 R12) and bury the one thing that makes SwingAI work — the trading edge.

---

*Back to the [README index](./README.md) · build order in [HOW-TO-BUILD.md](./HOW-TO-BUILD.md).*
