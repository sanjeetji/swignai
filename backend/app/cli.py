"""CLI for the Phase 0 harness.

    python -m app.cli backtest --synthetic --days 400
    python -m app.cli backtest --days 600              # real NSE data via yfinance
    python -m app.cli scan --synthetic
    python -m app.cli walkforward --synthetic --windows 3
"""
from __future__ import annotations

import argparse
import json

import pandas as pd

from .config import DEFAULT
from .data.factory import get_provider
from .backtest.engine import run_backtest, walk_forward
from .quant import picker as picker_mod
from .quant.features import build_features


def _provider(args):
    if args.synthetic:
        return get_provider("synthetic", days=args.days, seed=args.seed)
    return get_provider("yfinance")


def _date_range(args):
    """For real data, derive an explicit start/end so yfinance returns enough bars
    (calendar days ≈ 1.6× trading days). Synthetic ignores this."""
    if args.synthetic:
        return None, None
    end = pd.Timestamp.today().normalize()
    start = end - pd.Timedelta(days=int(args.days * 1.6) + 30)
    return start, end


def cmd_backtest(args):
    provider = _provider(args)
    start, end = _date_range(args)
    res = run_backtest(provider, start=start, end=end, capital=args.capital)
    print("\n=== BACKTEST SUMMARY (net of costs) ===")
    print(json.dumps(res.summary, indent=2))
    print("\n=== BY REGIME ===")
    print(json.dumps(res.by_regime, indent=2))
    if res.trades:
        print(f"\nFirst 5 of {len(res.trades)} trades:")
        for t in res.trades[:5]:
            print(f"  {t.entry_date}->{t.exit_date} {t.symbol:10} "
                  f"R={t.r_multiple:+.2f} pnl=₹{t.pnl_inr:+.0f} {t.status} ({t.reason}) [{t.regime}]")
    if not args.synthetic:
        print("\n(Real-data run — this is the one that counts as edge evidence, blueprint/05.)")


def cmd_walkforward(args):
    provider = _provider(args)
    out = walk_forward(provider, n_windows=args.windows, capital=args.capital)
    print(json.dumps(out, indent=2))


def cmd_scan(args):
    provider = _provider(args)
    index_close = provider.get_index()
    features = {}
    for sym in provider.get_universe():
        df = provider.get_ohlcv(sym)
        if df is not None and not df.empty and len(df) >= DEFAULT.warmup_bars + 5:
            features[sym] = build_features(df, index_close, DEFAULT)
    date = pd.Timestamp(args.date) if args.date else index_close.index[-1]
    picks = picker_mod.get_top_picks(date, features, index_close, args.capital, DEFAULT)
    print(f"\n=== PICKS for {date.date()} ===")
    if not picks:
        print("  CASH MODE — no picks (bear regime or no qualifying setups).")
        return
    for p in picks:
        pl = p.plan
        print(f"  {p.symbol:10} score={p.score:5.1f}  entry=₹{pl.entry} stop=₹{pl.stop} "
              f"T1=₹{pl.target_1} T2=₹{pl.target_2} R:R={pl.rr_ratio} qty={pl.quantity} "
              f"[{p.regime}] RSI={p.rsi} RS={p.rel_strength}")
        print(f"             breakdown={p.breakdown}")


def main():
    # common flags shared by all subcommands (usable after the subcommand name)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--synthetic", action="store_true", help="use offline synthetic data")
    common.add_argument("--days", type=int, default=500, help="synthetic days of history")
    common.add_argument("--seed", type=int, default=42)
    common.add_argument("--capital", type=float, default=100000.0)

    ap = argparse.ArgumentParser(prog="app.cli", description="SwingAI Phase 0 harness")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_bt = sub.add_parser("backtest", parents=[common]); p_bt.set_defaults(func=cmd_backtest)
    p_wf = sub.add_parser("walkforward", parents=[common]); p_wf.add_argument("--windows", type=int, default=3); p_wf.set_defaults(func=cmd_walkforward)
    p_sc = sub.add_parser("scan", parents=[common]); p_sc.add_argument("--date", type=str, default=None); p_sc.set_defaults(func=cmd_scan)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
