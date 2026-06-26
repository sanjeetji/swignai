"""Angel One SmartAPI provider — official, free NSE data for production (blueprint/02).

Login: API key + client code + MPIN + TOTP (auto-generated via pyotp from the saved
secret). Maps NSE symbols → instrument tokens via the SmartAPI scrip master, then pulls
daily candles. Lazy-imports the SDK so the backend boots without it installed.

Credentials come from settings (backend/.env or the encrypted vault) — never hardcoded.
"""
from __future__ import annotations

import time

import pandas as pd

from .base import OHLCV_COLUMNS

SCRIP_MASTER_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
NIFTY_TOKEN = "99926000"   # NIFTY 50 index token on NSE

# Curated NSE watchlist (no exchange suffix — Angel uses bare symbols).
# NOTE: TATAMOTORS is intentionally absent — Angel's current NSE-EQ scrip master
# doesn't list it (2025 Tata Motors demerger); BHARTIARTL used instead (telecom).
DEFAULT_UNIVERSE = [
    "BEL", "HAL", "ICICIBANK", "HDFCBANK", "SBIN", "SUNPHARMA", "DRREDDY", "INFY",
    "TCS", "HCLTECH", "BHARTIARTL", "MARUTI", "LT", "NTPC", "RELIANCE", "ITC",
    "HINDUNILVR", "AXISBANK", "M&M", "POWERGRID",
]


class AngelOneProvider:
    def __init__(self, universe: list[str] | None = None):
        from ..core.config import settings
        self.s = settings
        self.universe = universe or DEFAULT_UNIVERSE
        self._smart = None
        self._scrip: dict[str, str] | None = None

    # --- auth (cached for the process) ---
    def _connect(self):
        if self._smart is not None:
            return self._smart
        try:
            from SmartApi import SmartConnect
            import pyotp
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "smartapi-python not installed. Run: backend/.venv/bin/pip install smartapi-python"
            ) from e
        if not all([self.s.ANGELONE_API_KEY, self.s.ANGELONE_CLIENT_CODE,
                    self.s.ANGELONE_MPIN, self.s.ANGELONE_TOTP_SECRET]):
            raise RuntimeError("Angel One credentials missing — set ANGELONE_* in backend/.env")
        obj = SmartConnect(api_key=self.s.ANGELONE_API_KEY)
        totp = pyotp.TOTP(self.s.ANGELONE_TOTP_SECRET).now()
        sess = obj.generateSession(self.s.ANGELONE_CLIENT_CODE, self.s.ANGELONE_MPIN, totp)
        if not sess.get("status"):
            raise RuntimeError(f"Angel One login failed: {sess.get('message') or sess}")
        self._smart = obj
        return obj

    # --- symbol → token via the scrip master (downloaded once, cached) ---
    def _load_scrip(self) -> dict[str, str]:
        if self._scrip is not None:
            return self._scrip
        import requests  # bundles certifi → avoids macOS framework-python SSL issues
        data = requests.get(SCRIP_MASTER_URL, timeout=90).json()
        m: dict[str, str] = {}
        for row in data:
            sym = str(row.get("symbol", ""))
            if row.get("exch_seg") == "NSE" and sym.endswith("-EQ"):
                m[sym[:-3].upper()] = str(row.get("token"))
        self._scrip = m
        return m

    def _token(self, symbol: str) -> str | None:
        return self._load_scrip().get(symbol.upper())

    def _candles(self, token: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        obj = self._connect()
        resp = obj.getCandleData({
            "exchange": "NSE", "symboltoken": token, "interval": "ONE_DAY",
            "fromdate": start.strftime("%Y-%m-%d 09:15"),
            "todate": end.strftime("%Y-%m-%d 15:30"),
        })
        rows = (resp or {}).get("data") or []
        time.sleep(0.34)  # respect ~3 req/s historical limit
        if not rows:
            return pd.DataFrame(columns=OHLCV_COLUMNS)
        df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
        idx = pd.to_datetime(df["ts"], utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
        df.index = idx.dt.normalize()
        return df[["open", "high", "low", "close", "volume"]].astype(float)

    # --- MarketDataProvider interface ---
    def get_universe(self) -> list[str]:
        return list(self.universe)

    def get_ohlcv(self, symbol: str, start=None, end=None) -> pd.DataFrame:
        end = pd.Timestamp(end) if end else pd.Timestamp.today().normalize()
        start = pd.Timestamp(start) if start else end - pd.Timedelta(days=750)
        token = self._token(symbol)
        if not token:
            return pd.DataFrame(columns=OHLCV_COLUMNS)
        return self._candles(token, start, end)

    def get_index(self, start=None, end=None) -> pd.Series:
        end = pd.Timestamp(end) if end else pd.Timestamp.today().normalize()
        start = pd.Timestamp(start) if start else end - pd.Timedelta(days=750)
        df = self._candles(NIFTY_TOKEN, start, end)
        return df["close"].rename("NIFTY") if not df.empty else pd.Series(dtype=float)
