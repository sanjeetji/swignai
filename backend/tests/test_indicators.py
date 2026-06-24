"""Indicator math vs known/sane reference values (blueprint/11 §1)."""
import numpy as np
import pandas as pd

from app.quant import indicators as ind


def test_ema_matches_pandas_ewm():
    s = pd.Series([1, 2, 3, 4, 5], dtype=float)
    expected = s.ewm(span=3, adjust=False).mean()
    pd.testing.assert_series_equal(ind.ema(s, 3), expected)


def test_rsi_all_gains_is_100():
    s = pd.Series(np.arange(1, 40, dtype=float))  # strictly increasing
    rsi = ind.rsi(s, 14).dropna()
    assert (rsi > 99.0).all()


def test_rsi_all_losses_is_low():
    s = pd.Series(np.arange(40, 1, -1, dtype=float))  # strictly decreasing
    rsi = ind.rsi(s, 14).dropna()
    assert (rsi < 1.0).all()


def test_rsi_bounded_0_100():
    rng = np.random.default_rng(0)
    s = pd.Series(100 + np.cumsum(rng.normal(0, 1, 200)))
    rsi = ind.rsi(s, 14).dropna()
    assert rsi.between(0, 100).all()


def test_atr_positive():
    rng = np.random.default_rng(1)
    close = pd.Series(100 + np.cumsum(rng.normal(0, 1, 100)))
    high = close + 1.0
    low = close - 1.0
    atr = ind.atr(high, low, close, 14).dropna()
    assert (atr > 0).all()


def test_macd_signal_is_ema_of_macd():
    rng = np.random.default_rng(2)
    s = pd.Series(100 + np.cumsum(rng.normal(0, 1, 100)))
    macd_line, signal, hist = ind.macd(s)
    pd.testing.assert_series_equal(signal, ind.ema(macd_line, 9), check_names=False)
    pd.testing.assert_series_equal(hist, macd_line - signal, check_names=False)
