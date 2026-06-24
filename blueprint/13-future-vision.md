# 13 — Future Vision (Advanced / Futuristic)

> 🧭 **Status:** 📝 Spec (deferred) · **Tier:** 🏆 Best-in-class (design) → **Target: 🏆 Best-in-class** · **Phase 3→** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** This doc captures where SwingAI goes *after* the MVP is proven — the advanced, forward-looking platform. Everything here is **Phase 3+ / future**, deliberately deferred so the team doesn't over-build before the core edge and retention are validated (docs 05, 10). Each item lists *what it is*, *why it matters*, and *the honest preconditions* (because several of these are tempting traps if built too early). The non-negotiables from [`00-overview-philosophy.md`](./00-overview-philosophy.md) still bind every item here — especially: deterministic picks, honest tracker, analysis-not-advice.

---

## 1. ML-based scoring (learning-to-rank)

- **What:** replace/augment the rule-based Stage-2 score (doc 04) with a model — e.g. **gradient-boosted trees** or a learning-to-rank model — that *weights the same features* using the platform's accumulated honest outcome history.
- **Why:** once you have thousands of labeled picks (features → real R-multiple outcome), a model can find non-obvious feature interactions the hand-weights miss.
- **Preconditions (strict):** large honest labeled dataset; **walk-forward validation**; no look-ahead features; **explainability retained** (SHAP values surfaced so the dashboard still shows *why*); must **beat the rule-based baseline out-of-sample** before replacing it. Never let ML become an unexplainable black box — that breaks the transparency moat. Keep the rule-based picker as the fallback/benchmark forever.

## 2. Real-time intraday infrastructure

- **What:** **Angel One WebSocket streaming** for live prices → real-time stop/target monitoring and intraday position management (vs the current 3:45 PM batch exit-checker).
- **Why:** swing traders still need timely "your stop is about to hit" signals during the day.
- **Preconditions:** production data on Angel One (doc 02); robust connection handling (reconnect, dedupe); careful cost/scale (streaming many symbols). Likely pairs with a paid feed (TrueData) at scale.

## 3. News & sentiment AI layer

- **What:** ingest news, earnings, corporate actions, and (carefully) social sentiment per stock → a sentiment score feeding the screen as **context** (e.g. avoid a technical breakout into an earnings event) and surfaced on `/stocks/[symbol]`.
- **Why:** pure technicals miss catalysts; an earnings-date awareness alone prevents many bad entries.
- **Preconditions:** reliable Indian news/earnings-calendar source; sentiment must be **context/filter**, not a pick-originator (golden rule, doc 03); `news_sentiment` table (doc 06). Beware noisy social sentiment — weight it low or omit.

## 4. Multi-agent AI system

- **What:** distinct LLM "agents" (really: different prompts to the pluggable layer, doc 03) for specialized jobs:
  - **Explanation agent** — Hinglish pick narration (exists Phase 1).
  - **SEO content agent** — weekly blog/stock-page copy from real data (Phase 2).
  - **Risk-coach agent** — personalized post-trade review ("you exited winners early; your discipline score fell").
  - **Market-summary agent** — daily regime narration.
  - **Onboarding/education agent** — guides beginners through risk concepts.
- **Why:** different surfaces need different voices/contexts; coaching is a real retention lever.
- **Preconditions:** don't build an agent *framework* — keep it as orchestrated prompts; each agent still **never originates picks/numbers**; cache aggressively. (doc 03 §8)

## 5. AI chat assistant ("ask about any stock")

- **What:** a conversational assistant grounded **strictly via RAG on our own computed numbers** (indicators, score, regime, track record) — "Why isn't HAL a pick today?" → explains from the actual filter results.
- **Why:** huge engagement + education value; natural for the Hinglish audience.
- **Preconditions:** **must not free-form picks or advice** — answers only describe our computed analysis with the disclaimer (doc 09); RAG-grounded to prevent hallucinated numbers; rate-limit + cache for cost.

## 6. F&O — risk-defined strategies + education (Phase 4)

- **What:** extend to Futures & Options, but **only** as **capital-defined option strategies** (spreads with explicit max loss) plus heavy education — never naked directional option buy-calls.
- **Why:** large market demand; natural expansion once swing is proven.
- **Honest preconditions (this is a trap if rushed):** swing track record proven; ideally **RA license** in place; new risk engine (the simple R-model breaks on options — theta/IV/gamma are non-linear); SEBI is **actively discouraging retail F&O** (~90%+ lose) so framing + compliance scrutiny are higher (doc 09 §5). Build the *education* before the *signals*.

## 7. Broker integration / one-click execution

- **What:** connect Angel One / Zerodha / Upstox so users can act on analysis (and broker referral revenue).
- **Why:** convenience + a revenue stream (₹300–500/referred account).
- **Honest preconditions:** **compliance-gated** — execution integration changes the regulatory posture; lawyer + likely RA license required first (doc 09). Until then, referral links (not in-app execution) are the safer revenue path.

## 8. Community, social proof & leaderboards

- **What:** anonymized **paper-trading leaderboards**, shareable track records, discussion, "follow top paper-traders."
- **Why:** retention + viral distribution (the hard problem, doc 12 R3); social proof of the honest tracker.
- **Preconditions:** privacy controls; **measure leaderboard by expectancy/discipline, not raw P&L** (don't incentivize reckless betting); moderation; `leaderboard_stats` table (doc 06).

## 9. Adaptive / personalized risk

- **What:** tailor position sizing, max heat, and pick count to the *individual's* capital, demonstrated discipline, and drawdown tolerance — e.g. tighten risk automatically after a losing streak.
- **Why:** the core value (survival) becomes personalized and stickier.
- **Preconditions:** enough per-user history; still framed as an **educational calculator**, not personalized *advice* (doc 09); keep it explainable.

## 10. Native mobile app (Android-first)

- **What:** **Kotlin + Jetpack Compose** Android app (founder's core skill), Android-first because ~85% of Indian traders are on Android.
- **Why:** push notifications, better mobile UX, app-store discovery.
- **Preconditions:** stabilize the web product + API first; the FastAPI backend already serves the app (same endpoints, doc 07). Consider a PWA as the bridge before native.

## 11. Algo-readiness & portfolio intelligence

- **What:** correlation-aware position sizing (avoid 4 correlated bank stocks), sector-exposure limits, regime-adaptive strategy switching, and eventual (compliance-gated) automated execution.
- **Why:** portfolio-level risk is the next maturity step beyond per-trade risk.
- **Preconditions:** proven single-trade engine; heavy compliance for any automation; keep everything explainable + backtestable.

---

## Sequencing guardrail (so the future doesn't eat the present)

Build these **only after** the corresponding gate:
- After **Phase 0** proves edge → nothing here yet.
- After **Phase 1–2** prove retention → SEO agent, risk-coach agent, alerts, community basics.
- After **Phase 3** revenue + (ideally) RA license → ML scoring, real-time infra, chat assistant, broker integration, native app.
- After **swing fully proven** → F&O, algo-readiness.

Every item above still obeys the three non-negotiables: **deterministic picks, honest tracker, analysis-not-advice.** The future is more capability — not a relaxation of the principles that make the platform trustworthy.

---

*End of docs. Back to the [README index](./README.md).*
