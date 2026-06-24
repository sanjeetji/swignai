"""yfinance provider — free historical NSE/BSE data for Phase 0 backtests.

Honest caveats (blueprint/02): yfinance is unofficial, rate-limited, and has split/
adjustment quirks — fine for backtesting, NOT for the public production tracker
(move to Angel One for that). yfinance is imported lazily so the rest of the
harness (and the test suite) runs without it installed.
"""
from __future__ import annotations

import pandas as pd

from .base import OHLCV_COLUMNS

# A small, liquid seed universe across sectors (docs project context).
# Point-in-time universe construction is the backtest's responsibility (blueprint/05).
DEFAULT_UNIVERSE = [
    "BEL.NS", "HAL.NS", "ICICIBANK.NS", "HDFCBANK.NS", "SBIN.NS",
    "SUNPHARMA.NS", "DRREDDY.NS", "INFY.NS", "TCS.NS", "HCLTECH.NS",
    "TATAMOTORS.NS", "MARUTI.NS", "LT.NS", "NTPC.NS", "RELIANCE.NS",
    "ITC.NS", "HINDUNILVR.NS", "AXISBANK.NS", "M&M.NS", "POWERGRID.NS",
]
INDEX_SYMBOL = "^NSEI"


class YFinanceProvider:
    def __init__(self, universe: list[str] | None = None):
        self.universe = universe or DEFAULT_UNIVERSE

    def _yf(self):
        try:
            import yfinance as yf
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "yfinance is not installed. `pip install yfinance` for real data, "
                "or use the synthetic provider (--synthetic) for offline runs."
            ) from e
        return yf

    def _download(self, symbol: str, start, end) -> pd.DataFrame:
        yf = self._yf()
        df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)
        if df is None or df.empty:
            return pd.DataFrame(columns=OHLCV_COLUMNS)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.rename(columns=str.lower)
        df = df[["open", "high", "low", "close", "volume"]].dropna()
        df.index = pd.to_datetime(df.index)
        return df

    def get_universe(self) -> list[str]:
        return list(self.universe)

    def get_ohlcv(self, symbol: str, start=None, end=None) -> pd.DataFrame:
        return self._download(symbol, start, end)

    def get_index(self, start=None, end=None) -> pd.Series:
        df = self._download(INDEX_SYMBOL, start, end)
        return df["close"].rename(INDEX_SYMBOL) if not df.empty else pd.Series(dtype=float)
