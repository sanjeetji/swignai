"""Per-symbol feature computation — turns OHLCV into the columns the picker needs.

Computed once per symbol over its full history; the picker/filters/scorer then read
the row for a given date. Deterministic. No look-ahead (every column at row t uses
only data up to and including t).
"""
from __future__ import annotations

import pandas as pd

from ..config import StrategyConfig
from . import indicators as ind


def build_features(df: pd.DataFrame, index_close: pd.Series, cfg: StrategyConfig) -> pd.DataFrame:
    """`df` must have columns: open, high, low, close, volume (DatetimeIndex, ascending)."""
    out = df.copy()
    close = out["close"]

    out["ema20"] = ind.ema(close, 20)
    out["ema50"] = ind.ema(close, cfg.daily_trend_ema)
    out["ema200"] = ind.ema(close, 200)
    out["slope_ema"] = ind.ema(close, cfg.slope_ema)
    out["slope_up"] = ind.slope_up(out["slope_ema"], lookback=5)
    out["weekly_ema"] = ind.weekly_ema_on_daily(close, cfg.weekly_ema)

    out["rsi"] = ind.rsi(close, cfg.rsi_period)
    macd_line, signal_line, hist = ind.macd(close, cfg.macd_fast, cfg.macd_slow, cfg.macd_signal)
    out["macd"] = macd_line
    out["macd_signal"] = signal_line
    out["macd_hist"] = hist

    out["atr"] = ind.atr(out["high"], out["low"], close, cfg.atr_period)
    out["atr_pct"] = (out["atr"] / close) * 100.0

    out["vol_ratio"] = ind.volume_ratio(out["volume"], cfg.volume_avg_period)
    # traded value in ₹ crore (value / 1e7), then 20-day average
    turnover_cr = (close * out["volume"]) / 1e7
    out["turnover_cr"] = turnover_cr.rolling(cfg.volume_avg_period, min_periods=cfg.volume_avg_period).mean()

    out["rel_strength"] = ind.relative_strength(close, index_close, cfg.rel_strength_lookback)

    # structure: recent high (breakout level) and swing low (stop reference)
    out["recent_high"] = out["high"].rolling(cfg.breakout_lookback, min_periods=1).max()
    out["swing_low"] = out["low"].rolling(cfg.swing_low_lookback, min_periods=1).min()
    out["dist_to_high_pct"] = ((out["recent_high"] - close) / close) * 100.0
    out["ext_above_slope_pct"] = ((close - out["slope_ema"]) / out["slope_ema"]) * 100.0

    return out
