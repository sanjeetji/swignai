# 00 — Overview & Philosophy

> 🧭 **Status:** ✅ Done (living) · **Tier:** 🏆 Best-in-class → **Target: 🏆 Best-in-class** · **Phase —** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Read this first.** It explains *what* SwingAI is, *why* it is built the way it is, and the principles every other doc inherits. If you only read one file, read this one.

---

## 1. What SwingAI is (the honest one-liner)

**SwingAI is a risk-management and discipline platform that *also* gives swing-trade stock ideas — not a tip service that mentions risk.**

That inversion is the entire strategy. Internalize it before writing a line of code.

- A **tip service** sells "we'll tell you what to buy." It lives or dies on this quarter's picks, makes money even when users lose, and dies the first bad market month when the picks miss and users churn.
- A **discipline platform** sells "we keep you systematic, sized correctly, and out of bad markets — and we prove our results honestly." It earns subscription revenue from *tooling and process* regardless of whether this week's picks won, and survives bad months because capital preservation is itself a feature.

We are building the second one. The stock ideas are the *hook*; risk management and transparency are the *product*.

---

## 2. Who it's for

- **Primary user:** Indian retail swing trader, beginner-to-intermediate, Android-first, often Hindi/Hinglish-preferring, ₹50k–₹5L capital, moderate risk appetite.
- **The problem they actually have:** not "I don't know which stock" — it's "I have no process, I oversize, I don't use stops, I revenge-trade, and I can't tell if anything I do works." ~90% of Indian retail lose money in year one (SEBI data). That is a *discipline and psychology* problem, not an *information* problem.
- **What we genuinely fix:** we keep them out of bad regimes, enforce position sizing and stops, give a repeatable process, make them journal and review, and show them transparently what works. Even with average picks, a disciplined, risk-managed trader has a fighting chance; an undisciplined one with great picks still blows up.

---

## 3. The alignment principle (why owner AND user win together)

```
Owner earns  ⟸  users retain  ⟸  users don't blow up  ⟸  risk is ENFORCED
```

This is the core of the business model. If we built a "guaranteed profit" tipper, the owner would profit while users lost — misaligned, and doomed. By building survival-first, the only way the owner makes durable money is by keeping users alive and improving. **Build for survival, and the incentives lock together.**

A blunt corollary you must accept: **most users will still not get rich, and many will still lose** — markets are hard and behavior is hard. Our honest promise is *process, protection, and proof* — never *profit*. "We make you money" is a promise we cannot keep and would eventually be punished for (refunds, reviews, SEBI). "We make you systematic and we never lie to you about results" is a promise we *can* keep.

---

## 4. The 3 non-negotiables (violating any one kills the business)

### 4.1 The picker is deterministic math — never AI
Only a deterministic function can be **backtested over history** and **shown transparently**. The honest, verifiable track record is our entire moat — and you cannot backtest an LLM's judgment. The moment AI "judgment" enters stock selection, the track record becomes unprovable and the moat evaporates. (See [`04-picker-strategy.md`](./04-picker-strategy.md).)

### 4.2 The track record is honest
Reported as **wins / (wins + losses + scratches)**, **net of costs** (brokerage + STT + slippage), in **R-multiples**. No metric massaging — specifically, **do not exclude breakeven scratches from the denominator** to inflate win rate. A faked tracker is the fastest way to convert your only moat into your gravestone: the first user who recomputes the math honestly and finds a discrepancy ends your credibility. (See [`05-validation-backtest.md`](./05-validation-backtest.md) and [`11-verification-testing.md`](./11-verification-testing.md).)

### 4.3 Framing is "analysis/education," not "buy/sell advice"
SEBI regulates *advice*, not *execution*. "We don't let users buy/sell on our platform" is **not** a legal shield — every banned finfluencer tried that defense. Specific "buy X at ₹A, SL ₹B, target ₹C" is advice in substance. We publish **screener output + technical analysis** with educational framing, and we get a **SEBI-specialist lawyer sign-off before public launch.** (See [`09-compliance-sebi.md`](./09-compliance-sebi.md).)

---

## 5. The KPI correction: expectancy, not win rate

**Win rate is the wrong headline metric** and tempts dishonesty. Train the whole platform around **R-multiples** and **expectancy** (average R earned per trade).

- A **45%-win / 1:2.5 R:R** system is highly profitable.
- A **65%-win / 1:0.8 R:R** system bleeds out.

So we measure and display **expectancy, profit factor, max drawdown, and average hold time** — and we measure our *own* success by **user retention and user-expectancy improvement**, not by a vanity win-rate number. When users get better and stay alive, they retain, pay, and refer. That's the flywheel.

---

## 6. The 4 product layers (build in this order of value)

The picks are deliberately near the *bottom*. The value is at the top.

```
Layer 1 — SURVIVAL   (the moat; build FIRST)
  • Risk / position-size calculator — ENFORCED, not suggested
  • Portfolio heat + concentration limits
  • Market-regime gatekeeper ("trade / reduce / cash")
  • Stop-loss + trailing rules engine

Layer 2 — PROCESS    (the retention engine)
  • Paper trading with real prices
  • Auto trade journal (why entered, planned R, outcome)
  • Post-trade review ("you exited 7 of last 10 winners early")
  • Personal expectancy dashboard (their R, discipline score)

Layer 3 — SIGNALS    (the hook, NOT the core value)
  • Daily deterministic screener output (analysis framing)
  • Relative-strength + regime-filtered candidates
  • Full technical breakdown per stock

Layer 4 — TRUST      (the marketing weapon)
  • Honest public track record (net of costs, all trades, R-based)
  • Hinglish explanations (LLM = translation only)
```

Why this order matters operationally: most Indian tip-apps build Layer 3 first and die. We build Layers 1–2 first because *that* is what keeps users alive and retained — which is what makes the owner money.

---

## 7. The "Two Brains" (never conflate them)

| | Role | Tech | Affects edge? |
|---|---|---|---|
| **Brain 1 — The Quant** | Picker + risk engine + exits. Does all the math, applies filters, scores, sizes. | Python, TA-Lib, pandas | **YES — determines 100% of the edge** |
| **Brain 2 — The Guru** | Translator. Turns final numbers into a beginner-friendly Hinglish story. Builds trust & retention. | LLM (free now, Claude later) | **NO — adds zero mathematical accuracy** |

**Golden rule:** the LLM is the PR department, not the Research department. It receives finished numbers and narrates them. It NEVER picks a stock or originates a number. (Precise nuance: Brain 1 is not *just* the picker — it's picker **+ risk sizing + exit management**, and the last two matter as much as selection. See [`04-picker-strategy.md`](./04-picker-strategy.md).)

---

## 8. Honest business read (so nobody is deluded later)

- **Revenue engine is process + education + community, not "our picks win."** Subscriptions (₹499 Pro / ₹999 Premium), education/cohorts, and broker referrals pay even in a flat market.
- **The hard problem is distribution, not code.** Hitting ₹1–6 Cr ARR needs ~1,700–10,000 payers, which at a realistic 2–4% Indian fintech free→paid conversion means **125k–250k free users.** That's a marketing/founder-time problem no code solves. Near-term channel: building a public, honest track record on YouTube/Twitter/Reddit.
- **Realistic outcome distribution:** ~60% modest ₹10–40L/year business; ~25% fails to get traction; ~15% the transparency angle catches and it becomes ₹1Cr+. The unicorn scenario is the tail, not the base case. For a solo technical founder with ~₹1,500/mo burn, that's still excellent risk/reward.

---

## 8.5 Engineering principles (platform-wide, non-negotiable)

These bind every doc and every screen:

1. **No dummy/static/hardcoded data — ever.** Every feature is backend/API-driven with real loading/empty/error states. No mock rows, no placeholder series in charts, no hardcoded user-facing strings (everything via i18n, doc 15), no hardcoded colors (everything via theme tokens, doc 14), no hardcoded secrets (everything via the encrypted vault, doc 17). A "no-hardcoded-data" audit is part of verification (doc 11).
2. **Role-based product.** Super Admin / admin / support / user are real, server-enforced roles (RBAC, doc 19). Super Admin gets a full control plane (docs 16–18) + business analytics (doc 20); users get their trading dashboard. The frontend hiding a control is convenience; the API is the gate.
3. **Secure by default.** Admin 2FA, encrypted secrets, Row-Level Security, rate limiting, append-only audit log, and DPDP compliance (consent + privacy + retention + export/delete) are foundational, not Phase-3 add-ons (docs 18, 19).
4. **Multi-language + multi-theme from day one.** EN + HI (extensible to more), curated theme presets + light/dark/system + multiple fonts, with **admin-set defaults that users can override** (admin may lock an axis). Built mobile-first and fully responsive (docs 14–16).
5. **Honesty extends to the business too.** Revenue/MRR/ARR and the public track record are computed from real data and reconcile to source — no vanity or massaged numbers (docs 20, 11). Same principle as non-negotiable #2, applied to the whole platform.

---

## 9. The smartest first move (do this before building anything)

**Validate the edge in public before building the platform.** Build the picker + an honest backtest harness, run it over history (point-in-time, net-of-cost, walk-forward), and if expectancy is positive, run it **live in public** for 90 days with brutally honest accounting. Cost: ~₹5k. If the edge is real, *then* build the platform on proven ground. If it isn't, you've saved a year. This is Phase 0. (See [`05-validation-backtest.md`](./05-validation-backtest.md).)

---

*Next: [`01-architecture-techstack.md`](./01-architecture-techstack.md) — how the whole thing is structured and what it's built on.*
