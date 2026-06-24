# 02 — Market Data Layer

> 🧭 **Status:** 🧪 Partial (synthetic+yfinance built) · **Tier:** ③ Advanced → **Target: 🏆 Best-in-class** · **Phase 0→2** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** Market data is the most important external dependency in the entire platform. **Dirty data → unprovable track record → no moat.** The whole business rests on an honest, verifiable track record, and that is only as trustworthy as the price data underneath it. This doc compares every data source honestly, picks per-phase, and specifies the pluggable design so the source is a one-line config change.

---

## 1. Options compared (honest verdict)

| Source | Cost | Quality for NSE | Live? | Historical? | Verdict |
|---|---|---|---|---|---|
| **yfinance (Yahoo)** | Free | OK-ish. Unofficial scraping; rate limits, occasional gaps, bad splits/adjustments, against ToS for commercial use | 15-min delayed | Yes (decent) | **Phase 0 + early Phase 1 only** — fine for backtesting + 20 testers. NOT for paid scale or the public tracker. |
| **Google Finance** | Free | No official API; sparse/limited historical; brittle scraping | Spot only | Poor | **Reject as primary.** Use only for occasional manual sanity checks. |
| **NSE official (nsepython / direct endpoints)** | Free | Accurate, but heavy anti-bot + rate limits; fragile | Near-real-time | Limited | **Cross-check / backup source only.** Too fragile for production primary. |
| **Angel One SmartAPI** | **Free for account holders (you have one)** | Real official NSE data; live + historical; WebSocket streaming | Yes (real-time) | Yes | **Phase 1.5 / Phase 2 PRODUCTION PICK** — official, free, your own broker. Best free production-grade option. |
| **Dhan API / Upstox API** | Free tier | Good, official broker data | Yes | Yes | **Fallback / redundancy** to Angel One. |
| **Zerodha Kite** | ~₹2,000/mo | Excellent, widely used | Yes | Yes | Optional paid alternative if already a Zerodha user. |
| **TrueData / GlobalDatafeed** | ₹5k–25k/mo | Excellent, low-latency, reliable | Yes | Yes | **Phase 3 UPGRADE** at real scale. |

---

## 2. Decision — pick by phase (free now, paid later)

- **Phase 0 (backtesting):** **yfinance.** Free, historical data available immediately, zero setup, no scale pressure. Perfect for proving/killing the edge cheaply. **But clean and cross-check it** — yfinance has split/adjustment quirks that can quietly corrupt a backtest (see §4).
- **Phase 1.5 / Phase 2 (production):** **Angel One SmartAPI** as the live source. Official, accurate, free for you, with WebSocket streaming for future real-time alerts. **The public track record must be built on this, not yfinance** — yfinance is too dirty to defend publicly.
- **Redundancy:** **Dhan or Upstox** as a fallback provider (auto-failover if Angel One is down or rate-limited).
- **Phase 3 UPGRADE:** **TrueData** when free-tier rate limits or accuracy become the bottleneck at scale.

**Why "both" (yfinance AND Angel One):** yfinance gets you backtesting *today* with zero friction; Angel One gives you *trustworthy* live data that your moat depends on, also free. They serve different phases — use each where it fits.

---

## 3. Pluggable design (mandatory)

Build a single `MarketDataProvider` interface so swapping sources is one config line — never hardcode a vendor.

```python
# data/base.py
class MarketDataProvider(Protocol):
    def get_ohlcv(self, symbol: str, interval: str, lookback: int) -> "DataFrame": ...
    def get_quote(self, symbol: str) -> "Quote": ...          # latest price
    def get_universe(self) -> list[str]: ...                  # tradeable NSE symbols
    def get_index(self, index: str, interval: str, lookback: int) -> "DataFrame": ...  # NIFTY for regime
```

Implementations:
- `data/yfinance_provider.py` — `YFinanceProvider`
- `data/angelone_provider.py` — `AngelOneProvider`
- `data/dhan_provider.py` — `DhanProvider` (fallback)

Selected via config:
```
DATA_PROVIDER = "yfinance"   # → "angelone" → "dhan"
```

A thin factory returns the configured provider; everything upstream (picker, backtest, paper engine) depends only on the `MarketDataProvider` interface, never a concrete vendor. **Swapping yfinance → Angel One is a config change + one new class, not a rewrite.**

---

## 4. Data hygiene rules (non-negotiable — protects the moat)

1. **Adjust for splits/bonuses correctly.** yfinance auto-adjust quirks can silently corrupt historical bars. Use adjusted close consistently and cross-check a few known split events against NSE.
2. **Handle missing bars / holidays.** NSE trading calendar (incl. special sessions). Never forward-fill blindly — gaps must be explicit, not invented.
3. **Detect bad ticks.** Reject obviously broken bars (0 volume on a liquid name, >X% single-bar jumps that don't match NSE). Log to Sentry.
4. **Cross-check Phase-0 backtest data** against a second source (NSE) on a sample before trusting expectancy numbers. A backtest on dirty data is worse than no backtest — it gives false confidence.
5. **Timezone:** everything in IST. OHLCV timestamps normalized to IST market dates.

---

## 5. Caching (Redis — mandatory to dodge rate limits)

| Data | TTL | Why |
|---|---|---|
| Daily OHLCV bars | long (e.g. until next close) | Historical bars don't change intraday |
| Latest quote (intraday) | short (seconds–minutes) | Freshness for paper-trade fills |
| Tradeable universe list | daily | Changes rarely |
| NIFTY index series (regime) | long | Daily bar |

Because picks are computed **once/day** and served from Redis, the data API is hit a small, fixed number of times daily regardless of user count — free-tier rate limits stay irrelevant until real scale.

---

## 6. Rate-limit & failure handling (required)

- **Exponential backoff + retry** on every provider call (rate limits, transient network).
- **Auto-failover:** if primary provider fails after retries → try fallback provider (Angel One → Dhan).
- **Stale-cache fallback:** if all live calls fail, serve last-good cached data and flag it as stale (never crash the pipeline).
- **Alerting:** log all data failures to Sentry; a daily-pipeline data failure should page you (it means no picks that day).

---

## 7. The tradeable universe

- **Phase 0/1:** the curated sector watchlist (~100+ NSE names across Defence, Banking, Pharma, IT, Auto, Infra, Energy, FMCG — see the project context for the seed list).
- **Phase 2+:** expand toward the full liquid NSE universe (e.g. NIFTY 500 minus illiquid names), filtered by the liquidity knockout in the picker (doc 04).
- Universe construction for **backtesting must be point-in-time** (constituents *as of* each historical date) to avoid survivorship bias — see [`05-validation-backtest.md`](./05-validation-backtest.md).

---

## 8. Phase evolution summary

| Phase | Primary source | Purpose |
|---|---|---|
| 0 | yfinance (cleaned, cross-checked) | Backtesting the edge |
| 1 | yfinance → migrate to Angel One | MVP picks for 20 testers |
| 1.5 / 2 | **Angel One SmartAPI** (+ Dhan fallback) | Production live data, public tracker, real-time foundation |
| 3 | TrueData (paid) | Reliability + low latency at scale |
| Future | Angel One WebSocket streaming | Real-time intraday alerts (see doc 13) |

---

*Next: [`03-ai-llm-layer.md`](./03-ai-llm-layer.md) — the LLM "translator" layer and its free-now / paid-later options.*
