"""Technical indicators — pure pandas/numpy (no TA-Lib native dependency).

We deliberately avoid TA-Lib here so the harness runs on any machine without a
native build. The math is standard (Wilder's RSI/ATR, EMA/MACD); it can be
swapped for TA-Lib later behind the same function signatures if desired.
All functions are deterministic and operate on a price/volume Series or DataFrame.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period, min_periods=period).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's RSI."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    # Wilder smoothing == EMA with alpha = 1/period
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100.0 - (100.0 / (1.0 + rs))
    # if avg_loss == 0 and avg_gain > 0 -> RSI 100; if both 0 -> 50 (neutral)
    out = out.where(avg_loss != 0, other=100.0)
    out = out.where(~((avg_loss == 0) & (avg_gain == 0)), other=50.0)
    return out


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Returns (macd_line, signal_line, histogram)."""
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line, macd_line - signal_line


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's ATR."""
    tr = true_range(high, low, close)
    return tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def volume_ratio(volume: pd.Series, period: int = 20) -> pd.Series:
    return volume / sma(volume, period)


def slope_up(series: pd.Series, lookback: int = 5) -> pd.Series:
    """True where the series is higher than `lookback` bars ago (rising)."""
    return series > series.shift(lookback)


def weekly_ema_on_daily(close: pd.Series, period: int = 20) -> pd.Series:
    """Compute a weekly EMA and forward-fill onto the daily index (the 'tide')."""
    weekly = close.resample("W-FRI").last()
    w_ema = ema(weekly, period)
    return w_ema.reindex(close.index, method="ffill")


def relative_strength(close: pd.Series, index_close: pd.Series, lookback: int = 20) -> pd.Series:
    """Stock return minus index return over `lookback` bars (in %). >0 = outperforming."""
    idx = index_close.reindex(close.index, method="ffill")
    stock_ret = close.pct_change(lookback) * 100.0
    index_ret = idx.pct_change(lookback) * 100.0
    return stock_ret - index_ret
