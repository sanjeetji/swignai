"""Synthetic, deterministic OHLCV generator — for offline tests and demos.

This is a TEST/DEV FIXTURE, not product data. It lets the backtest and unit tests
run with zero network and reproducible results (seeded). Real backtests use the
yfinance provider. (blueprint/11 explicitly tests on synthetic price paths.)

It generates trending + mean-reverting + noisy series so the strategy has both
valid setups and traps — a fair, if artificial, test bed. It is NOT evidence of
real edge; only the yfinance backtest is (blueprint/05).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .base import OHLCV_COLUMNS


def _business_days(n: int, end: pd.Timestamp) -> pd.DatetimeIndex:
    return pd.bdate_range(end=end, periods=n)


def _series(rng: np.random.Generator, n: int, start_price: float, drift: float, vol: float) -> np.ndarray:
    rets = rng.normal(loc=drift, scale=vol, size=n)
    price = start_price * np.exp(np.cumsum(rets))
    return price


def _ohlcv_from_close(rng: np.random.Generator, close: np.ndarray, base_vol: float) -> pd.DataFrame:
    n = len(close)
    intraday = np.abs(rng.normal(0.0, 0.012, size=n)) + 0.002
    high = close * (1 + intraday)
    low = close * (1 - intraday)
    open_ = np.empty(n)
    open_[0] = close[0]
    open_[1:] = close[:-1] * (1 + rng.normal(0.0, 0.004, size=n - 1))
    open_ = np.clip(open_, low, high)
    volume = (base_vol * (1 + np.abs(rng.normal(0, 0.5, size=n)))).astype(np.int64)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume}
    )


class SyntheticProvider:
    """Deterministic provider. Same seed -> identical data every run."""

    def __init__(self, n_symbols: int = 12, days: int = 500, seed: int = 42,
                 end: pd.Timestamp | None = None):
        self.seed = seed
        self.days = days
        self.end = end or pd.Timestamp("2025-12-31")
        self.index_dates = _business_days(days, self.end)
        self._symbols = [f"SYN{i:02d}" for i in range(n_symbols)]
        self._cache: dict[str, pd.DataFrame] = {}
        self._index: pd.Series | None = None
        self._build()

    def _build(self) -> None:
        rng = np.random.default_rng(self.seed)
        # Index: a regime with bull and bear stretches
        idx_close = _series(rng, self.days, 22000.0, drift=0.0006, vol=0.008)
        # inject a clear downtrend in the middle so bear regime is exercised
        mid = self.days // 2
        idx_close[mid:mid + 60] *= np.exp(np.linspace(0, -0.12, 60))
        self._index = pd.Series(idx_close, index=self.index_dates, name="^NSEI")

        for i, sym in enumerate(self._symbols):
            sub = np.random.default_rng(self.seed + 1000 + i)
            drift = 0.0010 if i % 3 == 0 else (0.0 if i % 3 == 1 else -0.0004)
            vol = 0.018 + 0.004 * (i % 4)
            close = _series(sub, self.days, 100.0 + 50 * (i % 5), drift, vol)
            df = _ohlcv_from_close(sub, close, base_vol=800000 + 100000 * (i % 6))
            df.index = self.index_dates
            self._cache[sym] = df

    # --- MarketDataProvider interface ---
    def get_universe(self) -> list[str]:
        return list(self._symbols)

    def get_ohlcv(self, symbol: str, start=None, end=None) -> pd.DataFrame:
        df = self._cache[symbol]
        if start is not None:
            df = df[df.index >= pd.Timestamp(start)]
        if end is not None:
            df = df[df.index <= pd.Timestamp(end)]
        return df[OHLCV_COLUMNS].copy()

    def get_index(self, start=None, end=None) -> pd.Series:
        s = self._index
        if start is not None:
            s = s[s.index >= pd.Timestamp(start)]
        if end is not None:
            s = s[s.index <= pd.Timestamp(end)]
        return s.copy()
