"""Dhan data provider (blueprint/02 §4.2) — fallback to Angel One for NSE data.

Scaffold: implements the MarketDataProvider interface and reads credentials from
settings (DHAN_*). Lazy-imports the SDK so the backend boots without it. The HTTP calls
are stubbed behind a clear error until DHAN_ACCESS_TOKEN is configured — wire the live
endpoints when you add Dhan keys. Bare NSE symbols, same universe as Angel One.
"""
from __future__ import annotations

import pandas as pd

from .angelone_provider import DEFAULT_UNIVERSE
from .base import OHLCV_COLUMNS


class DhanProvider:
    def __init__(self, universe: list[str] | None = None):
        from ..core.config import settings
        self.s = settings
        self.universe = universe or DEFAULT_UNIVERSE

    def _require_creds(self):
        if not (self.s.DHAN_CLIENT_ID and self.s.DHAN_ACCESS_TOKEN):
            raise RuntimeError("Dhan credentials missing — set DHAN_CLIENT_ID / DHAN_ACCESS_TOKEN in backend/.env")

    def get_universe(self) -> list[str]:
        return list(self.universe)

    def get_ohlcv(self, symbol: str, start=None, end=None) -> pd.DataFrame:
        self._require_creds()
        # TODO: call Dhan historical-candle API with the configured token, map to OHLCV.
        raise RuntimeError("Dhan live fetch not wired yet — add the historical API call here.")
        return pd.DataFrame(columns=OHLCV_COLUMNS)  # noqa: unreachable (kept for shape clarity)

    def get_index(self, start=None, end=None) -> pd.Series:
        self._require_creds()
        raise RuntimeError("Dhan live fetch not wired yet — add the index API call here.")
        return pd.Series(dtype=float)  # noqa: unreachable
