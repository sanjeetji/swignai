# 12 — Decisions Log & Risks

> 🧭 **Status:** ✅ Living (ADRs + risks) · **Tier:** — → **Target: 🏆 Best-in-class** · **Phase all** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** A running record of *why* the platform is built the way it is (Architecture Decision Records), plus the honest risks to keep watching. When future-you (or a collaborator) asks "why did we choose X?", the answer lives here. Update it whenever a significant decision or risk changes.

---

## Part A — Decision Log (ADRs)

| # | Decision | Why | Doc |
|---|---|---|---|
| 1 | **One Next.js monolith** (not split marketing + app sites) | SEO engine lives inside the app anyway; one domain = one SEO authority; less maintenance for a solo founder | 01 |
| 2 | **Deterministic math picker; LLM translation-only** | Only deterministic logic is backtestable; the honest track record is the moat; LLMs hallucinate numbers | 04, 03 |
| 3 | **Honest R-based tracker incl. scratches** (`wins/(wins+losses+scratches)`) | Trust is the product; a faked tracker becomes the gravestone | 00, 11 |
| 4 | **Python + FastAPI backend** | The quant ecosystem (TA-Lib/pandas/numpy/backtesting) is Python; the math must live there | 01 |
| 5 | **yfinance (backtest) → Angel One (production) data path** | yfinance is free + immediate for backtesting but too dirty/ToS-risky for the public tracker; Angel One is official + free + accurate | 02 |
| 6 | **Gemini/OpenRouter free now → Claude/OpenAI post-revenue** (config swap) | LLM is decoration on final math; quality barely matters; spend nothing until revenue | 03 |
| 7 | **Survival + Process layers (1–2) before Signals (3)** | Users churn from blow-ups, not bad picks; retention drives revenue; incentives align owner & user | 00 |
| 8 | **"Analysis not advice" framing + lawyer sign-off pre-launch** | SEBI regulates advice, not execution; "we don't execute" is not a shield | 09 |
| 9 | **Expectancy (avg R) as headline KPI, not win rate** | Win rate tempts dishonesty and misleads; expectancy is what determines profitability | 00 |
| 10 | **Supabase Auth, not custom auth** | Saves weeks; secure defaults; middleware-friendly | 01 |
| 11 | **Validate edge (Phase 0) before building UI** | ~₹5k to prove or kill the core assumption; saves a year if no edge | 05 |
| 12 | **Rules-based scoring now; ML only Phase 3+ and only if it beats the baseline out-of-sample** | Rules are explainable + backtestable + need no data; ML risks an unexplainable black box that breaks transparency | 04 |
| 13 | **Pluggable provider interfaces** (data, LLM) via config | Swap vendors with one line; no rewrites at upgrade time | 01, 02, 03 |
| 14 | **Templates as guaranteed LLM fallback** | Zero cost, zero hallucination, SEBI-safe; pipeline never blocks on narration | 03 |
| 15 | **next-intl for i18n (EN+HI, extensible)** | App-Router-native SSR; add a locale via registry, no code change | 15 |
| 16 | **next-themes + CSS-variable tokens** | Light/dark/system + presets re-skin whole app via tokens; admin-controlled | 14, 16 |
| 17 | **Curated theme presets now; custom token editor later** | Consistent, hard-to-make-ugly, fast to ship well; full editor is Phase 3 | 14, 16 |
| 18 | **Personalization: admin default + user override + optional lock** | Flexible + standard; admin can still force an axis platform-wide | 16 |
| 19 | **IP-based city/region geolocation (no GPS)** | No permission friction; sufficient for admin/security; honest about approximation | 18 |
| 20 | **Encrypted secrets vault; master key in env/KMS** | DB compromise alone never reveals secrets; admin manages keys without deploys | 17 |
| 21 | **RBAC (roles+permissions), server-enforced + admin 2FA** | Secure by default; UI hiding is not security | 19 |
| 22 | **Full-page admin screens, never dialogs** | Per requirement; better UX for substantial flows; back-button nav | 16, 18 |
| 23 | **No dummy/static/hardcoded data — everything API-driven** | Real states, no drift; trust + maintainability | 00, 11 |
| 24 | **Pre-computed metrics (MRR/ARR/cohorts) nightly** | Instant admin dashboards; consistent with caching philosophy | 20 |
| 25 | **Dynamic marketing CMS rendered SSR/ISR (not client-fetch)** | DB-driven content stays SEO-strong; on-demand revalidate on publish | 21 |
| 26 | **Block/section content model (not freeform HTML)** | Consistent, on-brand, responsive, themed, XSS-safe; admin edits content not styling | 21 |
| 27 | **Seed-then-edit + content versioning/rollback** | Site works first boot; bad edits are reversible; nothing hardcoded in components | 21 |
| 28 | **Per-page editable SEO + JSON-LD (+ llms.txt)** | Genuine value: Google rich results + AI-LLM citation, admin-controlled | 21 |
| 29 | **REVISED: monorepo with TWO Next apps (marketing + dashboard), not one monolith** | Evidence from OmniMark: marketing stays Lighthouse-100, dashboard can be heavy, shared `packages/*`, direct OmniMark reuse. Supersedes ADR #1. | 01, OMNIMARK-REUSE |
| 30 | **Reuse OmniMark infra (vault, RBAC, 2FA, audit, CMS, theming, deploy); build trading engine + i18n fresh** | Proven code shortcut for platform plane; quant + i18n don't exist in OmniMark | OMNIMARK-REUSE |
| 31 | **Turborepo + async SQLAlchemy + Tremor/sonner/TipTap/dnd confirmed** | Matches OmniMark's working stack; adopt from start | 01, 14, 21 |
| 32 | **Unified event log (audit = filtered view); `emit()` fire-and-forget; append-only** | One stream for security/admin/system/integration/product; audit log is a category filter; logging never breaks the request path | 22 |

> **Note:** ADR #1 (single monolith) is **superseded by #29** after reviewing OmniMark. The single-app option remains viable but is no longer the default.

---

## Part B — Open Risks (watch & mitigate)

### R1 — Does the strategy actually have an edge? 🔴 **HIGHEST RISK**
- **What:** the textbook-indicator funnel may show no durable, net-of-cost edge out-of-sample. Everything downstream assumes positive expectancy; nothing has confirmed it.
- **Mitigation:** Phase 0 backtest + 90-day public live run *before* building the platform (doc 05). If no edge, iterate on the real edge sources (relative strength, regime, setups, risk/exit) — not more known indicators — or stop.
- **Status:** UNRESOLVED until Phase 0.

### R2 — SEBI framing legality 🔴
- **What:** specific buy/SL/target calls = advice; "educational" footer is a thin shield; 2024–25 finfluencer crackdown was aggressive.
- **Mitigation:** "analysis not advice" framing enforced in code (doc 09 §3); **SEBI-specialist lawyer sign-off before public launch**; RA license at Phase 3.
- **Status:** OPEN — lawyer not yet engaged.

### R3 — Distribution 🟠
- **What:** ₹1–6 Cr ARR needs ~1,700–10,000 payers → ~125k–250k free users at realistic 2–4% conversion. A marketing/founder-time problem no code solves.
- **Mitigation:** build a public, honest track record on YouTube/Twitter/Reddit *during* Phase 0; SEO compounding from Phase 2 (but it's a 12–18 month game).
- **Status:** OPEN.

### R4 — Data cleanliness (yfinance) 🟠
- **What:** split/adjustment quirks, gaps, ToS — a backtest on dirty data gives false confidence.
- **Mitigation:** data hygiene rules + cross-check vs NSE on a sample (doc 02 §4); move production to Angel One.
- **Status:** managed by process.

### R5 — Hinglish quality of free models 🟡
- **What:** small open models do Hindi/Hinglish poorly.
- **Mitigation:** test real outputs as a Hindi speaker before committing; Gemini Flash as primary; template fallback (doc 03).
- **Status:** test before launch.

### R6 — Free-tier limits / vendor changes 🟡
- **What:** free data/LLM tiers throttle or vanish; no SLA.
- **Mitigation:** aggressive Redis caching (~5 calls/day total); pluggable providers + failover; budgeted upgrade path (Angel One, TrueData, Claude).
- **Status:** managed by architecture.

### R7 — Behavior gap (paper → real) 🟡
- **What:** users calm on paper panic with real money; even a good system won't make most users profitable.
- **Mitigation:** honest framing (process/protection/proof, never "profit"); discipline score + post-trade review to build real habits. Set expectations openly.
- **Status:** inherent; managed by honesty.

### R8 — Never launching 🟡
- **What:** the most common startup killer — perfecting code instead of shipping.
- **Mitigation:** Phase 0 in weeks, not months; launch the MVP ugly to 20 testers; real feedback over perfect code.
- **Status:** discipline item.
- **Note:** the expanded platform scope (admin plane, i18n, theming, RBAC, sessions) *increases* this risk — keep Phase 1 focused on Layers 1–2 + the minimum admin/security needed; defer custom theme editor, extra languages, and full revenue analytics to later phases (doc 10).

### R9 — DPDP / location tracking 🔴
- **What:** collecting IP/approximate-location/device/session data is regulated personal-data processing; non-compliance risks penalties.
- **Mitigation:** consent at signup, localized privacy policy, purpose limitation, retention TTL + purge job, export/erasure, least-privilege + audit (docs 09, 18, 19). Lawyer sign-off alongside SEBI (R2).
- **Status:** OPEN — launch-gating.

### R10 — Secret-management blast radius 🟠
- **What:** the vault concentrates all third-party keys; a leak compromises many integrations at once.
- **Mitigation:** encryption at rest with master key in env/KMS (not DB), backend-only decryption, never to client/logs, re-auth to reveal/rotate, audit logging, rotation support (doc 17).
- **Status:** managed by design; revisit with KMS/HSM at scale.

### R11 — Animation/UX performance vs SEO 🟡
- **What:** "cool" animations + heavy charts can hurt Core Web Vitals, which drive SEO (the free-user engine).
- **Mitigation:** performance budget, code-split heavy libs, keep marketing routes lean, GPU-friendly motion, `prefers-reduced-motion`, set theme/font pre-hydration (doc 14 §7).
- **Status:** managed by design.

### R12 — Scope creep / over-building the platform plane 🟠
- **What:** the admin/control/analytics/**CMS** surface is large and can eat time before the *edge* (R1) is even proven.
- **Mitigation:** Phase 0 (edge validation) still comes first and needs **none** of this; build admin/security/CMS to the minimum for Phase 1 (seeded content + core blocks), expand per doc 10. Strongly consider a headless CMS (Payload) to avoid hand-building (doc 21 §2). Don't let the control plane delay proving the product works.
- **Status:** discipline item.

### R13 — Marketing CMS SEO regression 🟠
- **What:** a DB-driven marketing site rendered client-side would be near-invisible to Google/AI crawlers — destroying the free-user engine.
- **Mitigation:** marketing content **must** render SSR/ISR with on-demand revalidation; content in server HTML, not client fetch (docs 21, 08); verified by the SEO render test (doc 11).
- **Status:** managed by design — but verify in CI (it's an easy regression).

---

## Part C — How to use this doc

- Add an ADR row whenever you make a decision that future-you might question.
- Update a risk's **status** when it changes; move resolved risks to a "Resolved" section with the outcome.
- The 🔴 risks (R1 edge, R2 SEBI, R9 DPDP) are **go/no-go gates** — do not scale past Phase 2 with any unresolved. R1 is provable *before* building (Phase 0); R2 + R9 are launch-gating legal items (one lawyer engagement covers both).

---

*Next: [`13-future-vision.md`](./13-future-vision.md) — the advanced/futuristic platform.*
