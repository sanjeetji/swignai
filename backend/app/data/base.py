"""MarketDataProvider interface — everything upstream depends on this, not a vendor."""
from __future__ import annotations

from typing import Protocol

import pandas as pd

OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]


class MarketDataProvider(Protocol):
    def get_universe(self) -> list[str]:
        """Tradeable symbols (point-in-time construction is the backtest's job)."""
        ...

    def get_ohlcv(self, symbol: str, start, end) -> pd.DataFrame:
        """Daily OHLCV with a DatetimeIndex and columns OHLCV_COLUMNS (ascending)."""
        ...

    def get_index(self, start, end) -> pd.Series:
        """Daily close of the regime index (NIFTY)."""
        ...
