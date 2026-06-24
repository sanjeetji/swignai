# 04 — The Picker & Strategy (Brain 1)

> 🧭 **Status:** ✅ Done — built + tested · **Tier:** ③ Advanced → **Target: 🏆 Best-in-class** · **Phase 0** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** This is the heart of the product — the deterministic math that selects stocks, sizes positions, and manages exits. It is "Brain 1." It determines **100% of the edge**. It is **never** an LLM, because only deterministic logic can be backtested and shown transparently, and the honest track record is the entire moat. This doc specifies the full 4-stage funnel with every parameter, the risk engine, the exit logic, and how it evolves toward ML later.
>
> **Honest caveat up front:** the indicators below (EMA/RSI/MACD/volume) are the most widely-known signals on earth — there is no secret edge in them. The real edge here comes from (a) the **regime gate**, (b) **relative-strength ranking**, (c) **enforced risk sizing**, and (d) **disciplined exits** — and even then, *whether positive expectancy exists is unknown until the Phase-0 backtest proves it.* See [`05-validation-backtest.md`](./05-validation-backtest.md). Do not assume these numbers produce >60% win rate; assume nothing until walk-forward expectancy says so.

---

## 1. Architecture: a funnel, not a flat score

Think **funnel**, not "score everything and take the top 5." Knock out the disqualified first (cheap, strict), then rank only the survivors. This separates *"is this even tradeable?"* from *"how good is it?"*

```
GATE 0  →  Market regime (binary; can kill the whole day)
STAGE 1 →  Knockout filters (must pass ALL; defines a VALID setup)
STAGE 2 →  Weighted score 0–100 (ranks survivors)
STAGE 3 →  Trade plan + risk sizing + exits (the RISK ENGINE)
STAGE 4 →  LLM translation (Hinglish narration — doc 03)
```

All calculations run at **3:30 PM IST** daily (after close). Every parameter below lives in `quant/config.py` as a tunable constant — never hardcode in logic.

---

## 2. GATE 0 — Market regime (binary; kills everything)

The single biggest win-rate lever. Most retail loss is buying in downtrends.

- Fetch **NIFTY 50** daily close. Compute **EMA(20)** (and EMA(50) for context/labeling).
- **Rule:**
  - `NIFTY_close ≥ NIFTY_EMA20` → **BULL/NEUTRAL** → proceed to stock selection.
  - `NIFTY_close < NIFTY_EMA20` → **BEAR → ZERO PICKS → CASH MODE.** Show "why we're sitting out" educational content. Capital preserved = a *feature*, celebrated in the UX (doc 08).
- **Regime labeling (for analytics & the public record):**
  - **Bull:** NIFTY > EMA20 and EMA20 rising.
  - **Neutral:** NIFTY > EMA20 but flat/choppy → reduce position count / size.
  - **Bear:** NIFTY < EMA20 → no buys.
- Log every day's regime to `regime_log` (doc 06) for the transparent public record.

---

## 3. STAGE 1 — Knockout filters (must pass ALL)

No scoring here — these define whether a stock is a *valid* candidate at all. Fail any → out, no partial credit.

| # | Filter | Parameter (tunable) | Why |
|---|---|---|---|
| 1 | **Liquidity** | 20-day avg traded value > **₹25–50 cr** | Slippage on illiquid names eats the edge |
| 2 | **Weekly tide** | `price > Weekly EMA(20)` | Don't fight the higher timeframe (the "tide") |
| 3 | **Daily trend** | `price > EMA(50)` AND `EMA(20)` slope > 0 | Trade with the short-term trend (the "wave") |
| 4 | **Not over-extended** | `price ≤ 7–8%` above EMA(20) | Don't chase a stock that already ran |
| 5 | **Volatility sane** | ATR(14) between **1.5% and 5%** of price | Too quiet = no move; too wild = stop-hunted |
| 6 | **Valid stop exists** | a logical stop yielding **R:R ≥ 2** must exist | If no stop gives 1:2, the trade isn't worth taking — **risk filter** |

> Timeframe model: **Weekly chart = the tide (filter)** — if below 20-week EMA, reject immediately. **Daily chart = the waves (execution)** — find the entry trigger. Filter 2 is the tide; filters 3–4 are the waves.

---

## 4. STAGE 2 — Weighted score (0–100; ranks survivors)

Only stocks passing all knockouts get scored. **Relative strength carries the most weight on purpose** — it's the closest thing to a genuine, researchable edge, not the textbook oscillators everyone has.

| Factor | Signal | Weight |
|---|---|---|
| **Relative strength vs NIFTY** | outperformance over 20/50 trading days | **25** |
| **Trend quality** | EMA stack `20 > 50 > 200` + slope strength | 20 |
| **Setup proximity** | distance to a clean breakout / tight consolidation base | 20 |
| **Volume confirmation** | today's volume vs 20-day average (>1.5× ideal) | 15 |
| **Momentum** | RSI(14) in **50–65** sweet spot; MACD(12,26,9) line > signal | 12 |
| **R:R quality** | room to logical target vs stop distance | 8 |
| | **Total** | **100** |

- Each factor is normalized to its weight (e.g. RS contributes 0–25). Store the **per-factor breakdown** (jsonb) so the dashboard can show *why* a stock scored what it did — transparency = trust + education (doc 08).
- Sort survivors by total score; take **top N (default 5)**, subject to portfolio guards (§5). In **Neutral** regime, reduce N and/or size.

---

## 5. STAGE 3 — Trade plan + risk engine (per pick)

This is the **risk engine** — the actual product value (Layer 1, doc 00). Every number is deterministic.

**Entry trigger:** breakout / close above the identified resistance / base high.

**Stop loss (logical, not a flat %):** the *tighter-justified* of:
- recent **swing low**, or
- `entry − 1.5 × ATR(14)`.

Define **R = entry − stop** (the per-share risk).

**Targets:** **T1 = entry + 2R**, **T2 = entry + 3R** (minimum 1:2 R:R, consistent with knockout #6).

**Position sizing (the core discipline feature):**
```
risk_pct      = 1%                          # of total capital, per trade (tunable)
risk_amount   = capital × risk_pct
qty           = floor(risk_amount / R)
position_size = qty × entry
```
The user **never sizes by gut.** This single rule is what separates survivors from blow-ups.

**Portfolio guards (enforced, not suggested):**
- Max **3–4** open positions at once.
- Max **20%** of capital in any one stock.
- Max total **portfolio heat** = sum of live risk across all open positions ≤ a cap (e.g. 4–6% of capital). If a new pick would breach heat, it's not offered.

---

## 6. Exit management (deterministic; report honestly)

Exits matter as much as selection. The rules:
- **Initial stop:** as set in §5 (logical, ATR/swing-based).
- **Breakeven move:** when price reaches **+3%** (or +1R, whichever the config specifies), move stop to **entry** → converts many potential losses into 0% scratches.
- **Trail / lock-in:** at **+6%** (or +2R), trail stop to **+3%** lock-in. Continue trailing by rule toward T2.
- **Time stop (optional):** exit if the trade hasn't worked within the max hold window (e.g. 12–15 trading days) — swing trades shouldn't become investments.

> **Honesty rule (critical):** scratches (breakeven exits) are **counted in the denominator** of the track record: `win% = wins / (wins + losses + scratches)`. **Never exclude scratches to inflate the number.** The breakeven hack improves *real* outcomes (fewer full losses); it must not be used to fake the *reported* metric. (See doc 00 non-negotiable #2 and doc 11 verification.)

---

## 7. STAGE 4 — LLM translation

The finished Stage 0–3 numbers go to the LLM (doc 03), which writes the <60-word Hinglish explanation + risk warning + disclaimer. **It receives numbers; it never produces them.** Fallback to template on failure.

---

## 8. What the user sees on "scan" (transparency = differentiator)

The dashboard shows, per pick:
- **Score with full breakdown** (RS 22/25, Trend 18/20, Setup 16/20, Volume 11/15, Momentum 9/12, R:R 7/8).
- **Which knockout filters passed** (all 6, with values).
- **Full trade plan**: entry, stop, T1, T2, R:R, suggested quantity & position size (from *their* capital), portfolio-heat impact.
- **Hinglish explanation** on top.
- **Regime banner**: today's market state and whether we're buying or in cash.

Showing the math *is* the moat versus black-box tip apps. It also doubles as education.

---

## 9. Module layout (`apps/api/quant/`)

```
quant/
├── config.py        # ALL tunable parameters (single source)
├── indicators.py    # EMA, RSI, MACD, ATR, Bollinger, Stochastic, volume ratio (TA-Lib)
├── regime.py        # GATE 0 — NIFTY regime
├── filters.py       # STAGE 1 — knockout filters
├── scorer.py        # STAGE 2 — weighted score + breakdown
├── risk.py          # STAGE 3 — stop/targets/position size/portfolio guards
├── exits.py         # exit & trailing logic, scratch classification
└── picker.py        # orchestrates GATE 0 → STAGE 3, returns ranked picks + plans
```
`picker.get_top_picks_daily(limit=5)` is the single entry point used by both the live cron pipeline (doc 07) and the backtest engine (doc 05) — **the exact same code path**, so what you backtest is what you ship.

---

## 10. Evolution: rules now, ML later (Phase 3+)

- **Phase 0–2: transparent rule-based scoring.** Explainable, backtestable, needs no training data, and the score breakdown is itself a trust/education feature. Do not start with ML.
- **Phase 3+: ML scoring (optional, disciplined).** Once you have *honest labeled history* (every pick + outcome), consider a **learning-to-rank** model (e.g. gradient-boosted trees) to *weight* the same features. Strict guardrails: walk-forward validation, no look-ahead features, explainability (SHAP) retained, and it must **beat the rule-based baseline out-of-sample** before replacing it. ML must never become an unexplainable black box that breaks the transparency promise. Full detail in [`13-future-vision.md`](./13-future-vision.md).
- **F&O (Phase 4):** a *different* engine — risk-defined option strategies, not directional picks. The simple R-model doesn't translate to options (theta/IV/gamma). See doc 09 (compliance) and doc 13 (vision).

---

*Next: [`05-validation-backtest.md`](./05-validation-backtest.md) — how to prove this strategy actually has an edge before building anything else.*
