# SwingAI

An AI-native Indian swing-trading platform — **a risk-management & discipline platform that also gives stock ideas**, not a tip service. See [`blueprint/`](./blueprint/) for the complete spec.

> **Start here:** [`blueprint/README.md`](./blueprint/README.md) (index) → [`blueprint/HOW-TO-BUILD.md`](./blueprint/HOW-TO-BUILD.md) (build order + **resume prompt**).

## The 3 non-negotiables
1. Deterministic math picker (never AI) — the only thing that's backtestable.
2. Honest track record — `wins/(wins+losses+scratches)`, net of costs, in R-multiples.
3. "Analysis, not advice" framing (SEBI) — lawyer sign-off before public launch.

---

## Run the platform (Docker + scripts)

SwingAI ships with its own Postgres (`:5434`) + Redis (`:6380`) — separate from any other
local stack. One master script controls everything (see [`scripts/`](./scripts/)):

```bash
colima start                     # ensure the Docker runtime is up
scripts/swingai.sh start         # db + backend + frontend
scripts/swingai.sh status        # what's running (containers, processes, ports)
scripts/swingai.sh logs          # tail backend + frontend
scripts/swingai.sh stop          # stop everything (data preserved)
scripts/swingai.sh fresh         # reset DB volume + start (DESTRUCTIVE)
```

Per-component scripts: `scripts/db.sh`, `scripts/backend.sh`, `scripts/frontend.sh`,
`scripts/logs.sh` (each supports `start|stop|status|…`). After `start`:

- Marketing → http://localhost:9002 · Dashboard → http://localhost:9001 · API docs → http://localhost:9000/docs
- Seeded super admin: **admin@swingai.in / admin12345**

> The backend uses async SQLite by default (zero infra); the scripts point it at the
> Docker Postgres automatically. To rename the whole platform: [`brand/BRAND.md`](./brand/BRAND.md).

---

## Current state

**Phase 1 — MVP foundation built & running** (backend on Postgres, both Next apps scaffolded).
The trading **edge is still unproven** — Phase 0's real-data backtest is the gate; see
[`blueprint/05-validation-backtest.md`](./blueprint/05-validation-backtest.md) and the live
ledger in [`blueprint/HOW-TO-BUILD.md`](./blueprint/HOW-TO-BUILD.md).

```
backend/                  # Python 3.11+ — quant brain + backtest (Phase 0)
  app/quant/              # indicators, regime, filters, scorer, risk, exits, picker
  app/data/               # pluggable market-data providers (synthetic + yfinance)
  app/backtest/           # walk-forward, net-of-cost, R-multiple harness
  tests/                  # unit tests (synthetic data, run offline)
```

### Run it

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate      # optional
pip install -r requirements.txt                         # pandas, numpy (+ yfinance for real data)

# run the test suite (offline, synthetic data)
python -m pytest -q

# run a backtest on synthetic data (deterministic, offline)
python -m app.cli backtest --synthetic --days 400

# walk-forward (per-window, out-of-sample) on synthetic data
python -m app.cli walkforward --synthetic --days 800 --windows 3

# run a backtest on real NSE data (needs internet + yfinance) — the run that counts
python -m app.cli backtest --days 600

# scan: today's picks for a given date
python -m app.cli scan --synthetic
```

> Phase 1 (Next.js apps + FastAPI platform) begins only after Phase 0 shows positive net-of-cost expectancy. Build order in [`blueprint/HOW-TO-BUILD.md`](./blueprint/HOW-TO-BUILD.md).
