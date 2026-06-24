# 09 — Compliance (SEBI)

> 🧭 **Status:** 📝 Spec (needs lawyer sign-off) · **Tier:** ③ Advanced → **Target: 🏆 Best-in-class** · **Phase 1 (gate)** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** This is a launch-blocking concern, **not a Phase-3 footnote.** Giving specific stock recommendations in India without a SEBI Research Analyst (RA) license is regulated activity, and SEBI's 2024–25 crackdown on "finfluencers" and unregistered advice was aggressive. This doc defines the framing that keeps SwingAI defensible, the hard rules enforced in code, and the licensing path. **None of this is legal advice — it is an engineering/product framing to be confirmed by a SEBI-specialist lawyer before public launch.**

---

## 1. The single most important correction

> **"We don't let users buy/sell on our platform, so we're not liable" is FALSE.**

SEBI does **not** regulate *execution*. It regulates **advice**. Whether a trade executes on your app, on Zerodha, or on a napkin is irrelevant to liability. The thing that triggers regulation is **the act of telling someone what to buy** — specifically a directive like *"Buy HAL at ₹4,200, SL ₹4,000, target ₹4,600."*

"I was just sharing analysis / educating" is exactly the defense every banned finfluencer used. Not executing trades saved none of them. So the risk is **not** in execution (we have none) — it's in the **specificity and framing of what we publish**.

---

## 2. The framing that survives

The fix is the **framing of what we display**, not who executes. Same information, different liability:

| ❌ Advice (liable) | ✅ Analysis (defensible) |
|---|---|
| "Buy HAL at 4,200, SL 4,000, target 4,600." | "HAL is trading above its 20-EMA, RSI 58, volume 1.7× average — historically these conditions have preceded continuation. **This is technical analysis for education, not a recommendation.**" |
| "Our AI's top picks to buy today" | "Stocks that currently meet our technical screening conditions" |
| Imperative verbs: *buy, sell, exit now* | Descriptive: *meets these conditions, historically associated with…* |

**Principle:** publish **screener output + technical analysis with educational framing**, describing *conditions and historical tendencies*, never issuing *commands*.

---

## 3. Hard rules enforced in code (not just policy)

These are wired into the system, not left to good intentions:

1. **LLM/template output filter (doc 03 §6):** generated explanations are validated to **contain the disclaimer** and **contain no imperative buy/sell language**. Fails → regenerate or fall back to a compliant template. Never publish unchecked copy.
2. **Disclaimer in the UX, not just the footer:** every picks view, stock page, and the track record show "Educational analysis only — not investment advice. We are not SEBI-registered investment advisers." prominently.
3. **No personalized advice:** the platform shows the *same* screener output to everyone (cached, identical) — it does not tailor "advice" to an individual's situation, which is a stronger trigger.
4. **Risk/position sizing is framed as an educational calculator**, not a directive ("here's how a 1% risk rule would size this", not "put ₹25,000 in").
5. **Track record framed as historical record of screened conditions**, presented honestly (doc 00 #2), not as a performance promise.

---

## 4. The licensing path

| Phase | Compliance posture |
|---|---|
| **0 (public log)** | Personal trading journal shared publicly, educational framing, heavy disclaimers. Lowest profile. Still — be careful with directive language even here. |
| **1 (20 testers)** | Closed group, educational tool, disclaimers in UX. Lawyer review recommended before *any* public exposure. |
| **2 (beta, public-ish)** | **Lawyer sign-off required before public launch.** Lock the "analysis not advice" framing across all surfaces. |
| **3 (revenue/scale)** | Pursue **SEBI Research Analyst (RA) license** when revenue justifies it — this is what lets you give genuine, defensible analysis at scale and removes much of the framing tightrope. Budget time + cost. |
| **4 (F&O)** | Higher scrutiny (see §5). |

**Action item carried in the risk log (doc 12):** engage a SEBI-specialist lawyer to (a) review the framing, (b) draft the disclaimers/terms, (c) advise on RA timing. Cheapest insurance in the project.

---

## 5. F&O-specific compliance (Phase 4 — extra caution)

- SEBI has been **actively discouraging retail F&O** (2024 data: ~90%+ of retail F&O traders lose money, publicized hard). Building anything that pushes beginners into naked option-buying is reputationally and regulatorily radioactive.
- The defensible F&O product is **risk-defined strategies + education** (capital-defined spreads with explicit max loss, taught properly), **never** naked directional option buy-calls.
- **Prerequisite:** only add F&O after the swing track record is proven and (ideally) RA licensing is in place. See [`13-future-vision.md`](./13-future-vision.md).

---

## 6. Data & privacy — DPDP Act (launch-gating, not optional)

Tracking user **IP + approximate (city/region) location + device + sessions** (doc 18) is processing of **personal data** under India's **Digital Personal Data Protection (DPDP) Act** → these are hard requirements before public launch:

- **Consent at signup** — explicit, for collecting IP/location/device for security, fraud-prevention, and support. No covert tracking.
- **Clear, localized privacy policy** (doc 15) — what is collected, why, how long, who can see it.
- **Purpose limitation** — use session/geo data only for the stated purposes (security/support), not for unrelated profiling.
- **Retention limits** — TTL on session/geo/login logs; auto-purge (the `retention_cleanup` job, doc 07). Don't keep forever.
- **Right to access/export + erasure** — self-service data export and account deletion (`/api/me/export`, `DELETE /api/me`, doc 07), plus admin tooling (doc 18).
- **Least-privilege + audit** — PII access restricted by RBAC and audit-logged (docs 18, 19).
- **Secrets/keys** — encrypted vault, never exposed (doc 17).
- Respect data-source ToS (yfinance is unofficial — another reason to move to Angel One's official API for production, doc 02).
- Payment data (Phase 3): never store card data; Razorpay handles PCI scope.

> Both SEBI framing (§1–5) and DPDP (§6) are **launch-gating compliance items** — confirm both with a lawyer before public exposure (doc 12 risks R2 + DPDP).

---

## 7. The honest bottom line

You can build and run SwingAI. You **cannot**:
1. Rely on "no execution = no liability" (false).
2. Publish directive buy/sell calls under an "educational" footer and assume it protects you (it's thin).
3. Skip the lawyer until Phase 3 (the framing must be right *before* public exposure).

The survivable posture: **honest technical analysis + transparent track record + educational framing + lawyer sign-off + RA license when you scale.** Same code, compliant framing — and the framing is enforced in the pipeline, not left to chance.

---

*Next: [`10-roadmap-phases.md`](./10-roadmap-phases.md) — the full phase-by-phase build plan.*
