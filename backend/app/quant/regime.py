"""GATE 0 — market regime. The single biggest win-rate lever (blueprint/04 §2).

If NIFTY is below its EMA, we generate ZERO picks (cash mode). Most retail loss
comes from buying in downtrends; this gate avoids that.
"""
from __future__ import annotations

import pandas as pd

from ..config import StrategyConfig
from . import indicators as ind


def regime_series(index_close: pd.Series, cfg: StrategyConfig) -> pd.Series:
    """Label each date bull / neutral / bear from NIFTY vs its EMA + slope."""
    e = ind.ema(index_close, cfg.regime_ema)
    rising = ind.slope_up(e, lookback=5)
    out = pd.Series("bear", index=index_close.index, dtype="object")
    above = index_close >= e
    out[above & rising] = "bull"
    out[above & ~rising] = "neutral"
    return out


def regime_for_date(index_close: pd.Series, date, cfg: StrategyConfig) -> str:
    s = regime_series(index_close, cfg)
    if date not in s.index:
        # use the most recent available label on/before date
        s = s[s.index <= date]
        if s.empty:
            return "bear"
        return str(s.iloc[-1])
    return str(s.loc[date])


def is_tradeable(regime: str) -> bool:
    return regime in ("bull", "neutral")
