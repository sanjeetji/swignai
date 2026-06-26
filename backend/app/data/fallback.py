"""FallbackProvider (blueprint/02 §4.2) — wrap a primary data source with a backup.

If the primary errors or returns empty for a symbol/index, transparently retry against
the fallback. Keeps the live pipeline resilient when one vendor (Angel One) hiccups,
without any caller changes — it satisfies the same MarketDataProvider interface.
"""
from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger("fallback_provider")


class FallbackProvider:
    def __init__(self, primary, fallback):
        self.primary = primary
        self.fallback = fallback

    def get_universe(self) -> list[str]:
        try:
            u = self.primary.get_universe()
            if u:
                return u
        except Exception as e:  # pragma: no cover
            logger.warning("primary get_universe failed (%s); using fallback", e)
        return self.fallback.get_universe()

    def get_ohlcv(self, symbol, start=None, end=None) -> pd.DataFrame:
        try:
            df = self.primary.get_ohlcv(symbol, start, end)
            if df is not None and not df.empty:
                return df
        except Exception as e:
            logger.warning("primary get_ohlcv(%s) failed (%s); trying fallback", symbol, e)
        try:
            return self.fallback.get_ohlcv(symbol, start, end)
        except Exception as e:  # pragma: no cover
            logger.warning("fallback get_ohlcv(%s) failed (%s)", symbol, e)
            return pd.DataFrame()

    def get_index(self, start=None, end=None) -> pd.Series:
        try:
            s = self.primary.get_index(start, end)
            if s is not None and len(s):
                return s
        except Exception as e:
            logger.warning("primary get_index failed (%s); trying fallback", e)
        return self.fallback.get_index(start, end)
