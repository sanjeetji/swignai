"""Canonical NSE sector classification for the covered universe (blueprint/12).

Factual large-cap sector mapping — drives the /sectors SEO pages, `ai_picks.sector`,
and the `best_sector` analytic. Bare NSE symbols (no .NS). Extend as the universe grows.
"""
from __future__ import annotations

SECTORS: dict[str, str] = {
    "BEL": "Defence", "HAL": "Defence",
    "ICICIBANK": "Banking", "HDFCBANK": "Banking", "SBIN": "Banking", "AXISBANK": "Banking",
    "SUNPHARMA": "Pharma", "DRREDDY": "Pharma",
    "INFY": "IT", "TCS": "IT", "HCLTECH": "IT",
    "BHARTIARTL": "Telecom",
    "MARUTI": "Auto", "M&M": "Auto",
    "LT": "Infrastructure",
    "NTPC": "Power", "POWERGRID": "Power",
    "RELIANCE": "Energy",
    "ITC": "FMCG", "HINDUNILVR": "FMCG",
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
