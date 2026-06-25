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


# --- advanced indicators (educational analysis depth) ---
def bollinger(close: pd.Series, period: int = 20, mult: float = 2.0):
    """Returns (mid, upper, lower, %b). %b = position within the bands (0=lower,1=upper)."""
    mid = sma(close, period)
    sd = close.rolling(period, min_periods=period).std()
    upper, lower = mid + mult * sd, mid - mult * sd
    pct_b = (close - lower) / (upper - lower)
    return mid, upper, lower, pct_b


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k: int = 14, d: int = 3):
    """Stochastic oscillator %K and %D (0-100)."""
    ll = low.rolling(k, min_periods=k).min()
    hh = high.rolling(k, min_periods=k).max()
    pct_k = 100.0 * (close - ll) / (hh - ll)
    return pct_k, pct_k.rolling(d, min_periods=d).mean()


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average Directional Index — trend strength (not direction). >25 = trending."""
    up = high.diff()
    down = -low.diff()
    plus_dm = ((up > down) & (up > 0)) * up
    minus_dm = ((down > up) & (down > 0)) * down
    tr = true_range(high, low, close)
    atr_ = tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    plus_di = 100.0 * plus_dm.ewm(alpha=1.0 / period, adjust=False).mean() / atr_
    minus_di = 100.0 * minus_dm.ewm(alpha=1.0 / period, adjust=False).mean() / atr_
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, np.nan)
    return dx.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume — cumulative volume flow (accumulation/distribution)."""
    direction = np.sign(close.diff()).fillna(0.0)
    return (direction * volume).cumsum()


def pct_from_high(close: pd.Series, window: int = 252) -> pd.Series:
    """Distance below the rolling N-day high, in % (0 = at the high)."""
    roll_high = close.rolling(window, min_periods=1).max()
    return (close - roll_high) / roll_high * 100.0


def pct_from_low(close: pd.Series, window: int = 252) -> pd.Series:
    roll_low = close.rolling(window, min_periods=1).min()
    return (close - roll_low) / roll_low * 100.0
