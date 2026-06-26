"""Canonical NSE sector classification for the covered universe (blueprint/12).

Factual large-cap sector mapping — drives the /sectors SEO pages, `ai_picks.sector`,
and the `best_sector` analytic. Bare NSE symbols (no .NS). Extend as the universe grows.
"""
from __future__ import annotations

SECTORS: dict[str, str] = {
    # Banking
    "ICICIBANK": "Banking", "HDFCBANK": "Banking", "SBIN": "Banking", "AXISBANK": "Banking",
    "KOTAKBANK": "Banking", "INDUSINDBK": "Banking", "BANKBARODA": "Banking",
    # IT
    "INFY": "IT", "TCS": "IT", "HCLTECH": "IT", "WIPRO": "IT", "TECHM": "IT",
    # Auto
    "MARUTI": "Auto", "M&M": "Auto", "EICHERMOT": "Auto", "HEROMOTOCO": "Auto",
    "BAJAJ-AUTO": "Auto", "TVSMOTOR": "Auto",
    # Pharma
    "SUNPHARMA": "Pharma", "DRREDDY": "Pharma", "CIPLA": "Pharma", "DIVISLAB": "Pharma", "AUROPHARMA": "Pharma",
    # FMCG / Consumer
    "ITC": "FMCG", "HINDUNILVR": "FMCG", "NESTLEIND": "FMCG", "BRITANNIA": "FMCG", "DABUR": "FMCG",
    "TITAN": "Consumer", "DMART": "Consumer", "ASIANPAINT": "Consumer",
    # Energy / Power
    "RELIANCE": "Energy", "ONGC": "Energy", "COALINDIA": "Energy",
    "NTPC": "Power", "POWERGRID": "Power", "TATAPOWER": "Power",
    # Metals
    "TATASTEEL": "Metals", "JSWSTEEL": "Metals", "HINDALCO": "Metals", "VEDL": "Metals",
    # Infra / Cement
    "LT": "Infrastructure", "ULTRACEMCO": "Cement", "GRASIM": "Cement",
    # Telecom / Defence / Finance
    "BHARTIARTL": "Telecom", "BEL": "Defence", "HAL": "Defence",
    "BAJFINANCE": "Finance", "BAJAJFINSV": "Finance", "SBILIFE": "Finance", "HDFCLIFE": "Finance",
}


def sector_for(symbol: str) -> str | None:
    s = symbol.upper()
    if s.endswith(".NS"):
        s = s[:-3]
    return SECTORS.get(s)


def sectors_map() -> dict[str, list[str]]:
    """{sector: [symbols]} — sorted, for the /sectors index + pages."""
    out: dict[str, list[str]] = {}
    for sym, sec in SECTORS.items():
        out.setdefault(sec, []).append(sym)
    return {k: sorted(v) for k, v in sorted(out.items())}
