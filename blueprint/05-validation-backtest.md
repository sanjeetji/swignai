# 05 — Validation & Backtest Harness (Phase 0)

> 🧭 **Status:** ✅ Done — harness built (real-data run pending) · **Tier:** ③ Advanced → **Target: 🏆 Best-in-class** · **Phase 0** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** This is the single most important — and cheapest — step in the entire project. Before building a UI, a database, or anything user-facing, **prove the strategy has a real edge.** Cost: ~₹5k and ~2 weeks of build + a 90-day public run. If the edge is real, you build the platform on solid ground. If it isn't, you've saved a year. The strategy having positive net-of-cost expectancy is the **highest-risk unknown in the project** — everything downstream assumes it, and nothing has confirmed it yet.

---

## 1. The goal

Answer one question honestly: **Does the Section-6 funnel (doc 04) produce positive expectancy, net of costs, out-of-sample?**

Not "does it look good on a chart." Not "did it work in the 2023 bull run." **Positive expectancy on data the rules were not tuned on, after realistic costs.**

---

## 2. The biases that make beginners over-trust a backtest (avoid ALL)

A backtest is trivial to fake yourself into believing. These are the killers:

| Bias | What it is | How we avoid it |
|---|---|---|
| **Survivorship** | Backtesting only today's winners (BEL, HAL, etc. that already ran) | **Point-in-time universe** — use the constituents/liquidity *as of each historical date*, including names that later delisted or fell out |
| **Look-ahead** | Using information not available at decision time (e.g. trading a bar's close using that same close, or today's indicators to trade yesterday) | Compute signals on bar `t`, **execute on bar `t+1` open**. Never use future bars. |
| **In-sample over-fitting** | Tuning parameters on the same data you report results on | **Walk-forward** — tune on window A, test on the *next unseen* window B. Report only out-of-sample. |
| **Ignoring costs** | Reporting gross returns | Model **brokerage + STT + exchange charges + slippage** on every fill |
| **Cherry-picked window** | Reporting only a favorable period | Test across **multiple years and all regimes** (bull/neutral/bear) and report each |
| **Ignoring liquidity** | Assuming you can fill any size at the printed price | Apply the liquidity knockout + slippage model; skip fills that aren't realistic |

---

## 3. Required methodology

1. **Point-in-time universe.** Reconstruct the tradeable list as it would have been on each historical date (liquidity-filtered). No future knowledge of which names succeeded.
2. **Next-bar execution.** Signal computed on close of day `t` → enter at **open of day `t+1`** (mirrors the real 3:30 PM-compute, next-day-act flow). Exits likewise on next available bar.
3. **Net-of-cost fills.** Per round trip, subtract: brokerage (or zero-brokerage delivery model, whichever matches the real broker), **STT**, exchange + SEBI + stamp charges, and a **slippage** assumption (e.g. 0.1–0.3% depending on liquidity; larger for thinner names). Account for the **15-min data delay** in entry price realism.
4. **Walk-forward.** Split history into rolling train/test windows. Tune parameters (if any) only on train; report only test. This is what separates a real edge from curve-fitting.
5. **Regime segmentation.** Report performance **separately for bull / neutral / bear** months. A healthy system should be roughly flat-or-cash in bear months (Gate 0 working), not bleeding.
6. **Same code path as production.** The backtest calls the **exact same** `picker.get_top_picks_daily()` and risk/exit modules (doc 04) — so what you validate is what you ship. No separate "backtest strategy."

---

## 4. Metrics that actually matter (report all)

Do **not** lead with win rate. Lead with expectancy.

| Metric | Definition | Why it matters |
|---|---|---|
| **Expectancy (avg R)** | mean R-multiple per trade | The headline. Positive = edge. |
| **Win rate** | `wins / (wins + losses + scratches)` | Context only — never the headline; **scratches included** |
| **Profit factor** | gross profit / gross loss | >1 required; >1.5 healthy |
| **Max drawdown** | largest peak-to-trough equity drop | Survivability / psychological tolerance |
| **Avg hold (days)** | mean trading days held | Confirms it's actually swing (2–15d) |
| **Trade count** | total trades | Statistical significance (need enough) |
| **Exposure / time-in-cash** | % of days with positions | Confirms Gate 0 keeps you out in bad regimes |
| **Per-regime breakdown** | all the above, split bull/neutral/bear | Where the edge does/doesn't come from |

Output a **full trade log** (every entry/exit/R) so results are auditable — by you now, and by users later on the public `/backtest` page.

---

## 5. Module layout (`apps/api/backtest/`)

```
backtest/
├── engine.py        # walk-forward loop, next-bar execution, equity curve
├── costs.py         # brokerage + STT + charges + slippage model
├── universe.py      # point-in-time universe reconstruction
├── metrics.py       # expectancy, profit factor, drawdown, per-regime stats
└── report.py        # trade log + summary (JSON for /backtest, console for dev)
```

Reuses `data/` (yfinance provider, doc 02) and `quant/` (the live picker, doc 04). Results cached to `backtest_runs` (doc 06) for the public `/backtest` tool.

---

## 6. The Phase-0 deliverable & exit criterion

**Build:** the picker (doc 04) + this harness + yfinance provider (cleaned/cross-checked, doc 02).

**Run:**
1. Backtest over multiple years, walk-forward, net of costs, regime-segmented.
2. **If walk-forward expectancy is positive** → run the strategy **LIVE in public** for 90 days: a free Telegram/Twitter log, every pick and outcome posted honestly in R-multiples (this also tests whether you can attract an audience — the other hard unknown).

**Exit criterion (go/no-go for building the platform):**
- ✅ Positive walk-forward expectancy **net of costs**, with sane per-regime behavior (≈flat/cash in bear), over a statistically meaningful trade count, **AND** early audience signal from the public log → **build Phase 1.**
- ❌ Negative/marginal expectancy, or only-works-in-bull, or no audience interest → **rework the strategy or stop.** Do not build a platform around an unproven edge.

**Cost:** ~₹5k. This is the best money you'll spend on the project.

---

## 7. Honest expectations

- It is entirely possible the textbook-indicator funnel shows **no durable edge** out-of-sample. That's not failure — that's the harness doing its job *before* you waste a year. If so, iterate on the genuine edge sources (relative strength, regime, better setups, risk/exit tuning) — not by adding more known indicators.
- Even a positive backtest **will not** translate 1:1 to live results (slippage, behavior, regime shifts). Treat the live 90-day public run as the real test; the backtest is the gate that earns the right to run it.

---

*Next: [`06-database-schema.md`](./06-database-schema.md) — the data model that stores picks, paper trades, analytics, and the public record.*
