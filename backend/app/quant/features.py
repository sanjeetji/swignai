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

    # --- advanced mathematical indicators (transparent, deterministic) ---
    out["ema100"] = ind.ema(close, 100)
    out["sma200"] = ind.sma(close, 200)
    _, out["bb_upper"], out["bb_lower"], out["bb_pct_b"] = ind.bollinger(close, 20, 2.0)
    out["stoch_k"], out["stoch_d"] = ind.stochastic(out["high"], out["low"], close, 14, 3)
    out["adx"] = ind.adx(out["high"], out["low"], close, 14)            # trend strength
    out["obv"] = ind.obv(close, out["volume"])
    out["obv_slope_up"] = ind.slope_up(ind.ema(out["obv"], 20), lookback=10)  # volume accumulation
    out["pct_from_52w_high"] = ind.pct_from_high(close, 252)
    out["pct_from_52w_low"] = ind.pct_from_low(close, 252)

    return out


def analysis_dict(row) -> dict:
    """Flat, JSON-friendly snapshot of the computed math for a given bar (educational)."""
    def num(key, nd=2):
        v = row.get(key)
        try:
            return round(float(v), nd)
        except (TypeError, ValueError):
            return None
    return {
        "close": num("close"),
        "ema20": num("ema20"), "ema50": num("ema50"), "ema100": num("ema100"),
        "ema200": num("ema200"), "sma200": num("sma200"),
        "rsi": num("rsi"), "macd": num("macd", 4), "macd_signal": num("macd_signal", 4),
        "atr_pct": num("atr_pct", 2), "adx": num("adx", 1),
        "stoch_k": num("stoch_k", 1), "stoch_d": num("stoch_d", 1),
        "bb_pct_b": num("bb_pct_b", 3), "bb_upper": num("bb_upper"), "bb_lower": num("bb_lower"),
        "vol_ratio": num("vol_ratio", 2), "turnover_cr": num("turnover_cr", 1),
        "rel_strength": num("rel_strength", 2),
        "pct_from_52w_high": num("pct_from_52w_high", 1), "pct_from_52w_low": num("pct_from_52w_low", 1),
        "dist_to_breakout_pct": num("dist_to_high_pct", 2),
        "obv_accumulating": bool(row.get("obv_slope_up", False)),
        "trend_stack_bullish": bool(row.get("ema20", 0) > row.get("ema50", 0) > row.get("ema200", 0)),
    }
