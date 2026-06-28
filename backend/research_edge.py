"""Edge research (blueprint/05) — test principled, economically-motivated strategy
variants with WALK-FORWARD (out-of-sample) on real data. Hypothesis from the Phase-0
finding: bull-regime entries chase over-extension and revert, so tighter over-extension
+ no-overbought entries (buy pullbacks, not chases) should generalise better.

Honest discipline: small number of variants, evaluated on EACH window (no in-sample
cherry-picking); the recent window is the most relevant. Run:  python research_edge.py
"""
from dataclasses import replace

import pandas as pd

from app.backtest.engine import walk_forward
from app.config import DEFAULT
from app.data.yfinance_provider import YFinanceProvider


class CachedProvider:
    """Fetch the 5y universe + index ONCE; serve filtered slices so every variant/window
    reuses the same data (fast, no repeat yfinance calls)."""
    def __init__(self):
        base = YFinanceProvider()
        self._idx = base.get_index()
        self._cache = {}
        for s in base.get_universe():
            df = base.get_ohlcv(s)
            if df is not None and not df.empty:
                self._cache[s] = df
        print(f"cached {len(self._cache)} symbols, index {len(self._idx)} bars "
              f"({self._idx.index[0].date()} → {self._idx.index[-1].date()})")

    def get_universe(self):
        return list(self._cache.keys())

    def get_ohlcv(self, sym, start=None, end=None):
        df = self._cache.get(sym)
        if df is None:
            return None
        if end is not None:
            df = df[df.index <= pd.Timestamp(end)]
        if start is not None:
            df = df[df.index >= pd.Timestamp(start)]
        return df

    def get_index(self, start=None, end=None):
        s = self._idx
        if end is not None:
            s = s[s.index <= pd.Timestamp(end)]
        if start is not None:
            s = s[s.index >= pd.Timestamp(start)]
        return s


VARIANTS = {
    "baseline (current DEFAULT)": DEFAULT,
    # --- round 2: new signal gates (ADX / OBV / Bollinger) — keep only if OOS-positive ---
    "adx>=20 (trend strength)": replace(DEFAULT, adx_min=20.0),
    "adx>=25 (strong trend)": replace(DEFAULT, adx_min=25.0),
    "obv_accum (volume confirms)": replace(DEFAULT, require_obv_accum=True),
    "bb%b<=0.95 (not band-extended)": replace(DEFAULT, bb_max_pct_b=0.95),
    "adx>=20 + obv_accum": replace(DEFAULT, adx_min=20.0, require_obv_accum=True),
    "adx>=20 + bb%b<=0.95": replace(DEFAULT, adx_min=20.0, bb_max_pct_b=0.95),
    "all three (adx20+obv+bb)": replace(DEFAULT, adx_min=20.0, require_obv_accum=True, bb_max_pct_b=0.95),
}


def main():
    p = CachedProvider()
    print(f"\n{'variant':<34} | W1 (21-23) | W2 (23-24) | W3 (24-26, recent) | avg")
    print("-" * 92)
    for name, cfg in VARIANTS.items():
        wf = walk_forward(p, n_windows=3, cfg=cfg)
        rows = []
        for w in wf["windows"]:
            s = w["summary"]
            rows.append(s["expectancy_r"] if s.get("trades", 0) > 0 else None)
        cells = [f"{r:+.3f}R" if r is not None else "  n/a " for r in rows]
        vals = [r for r in rows if r is not None]
        avg = sum(vals) / len(vals) if vals else 0.0
        print(f"{name:<34} | {cells[0]:^9} | {cells[0 if len(cells)<2 else 1]:^9} | {cells[-1]:^17} | {avg:+.3f}R")


if __name__ == "__main__":
    main()
