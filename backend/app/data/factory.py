"""Provider factory — select the data source by name (one config line)."""
from __future__ import annotations


def get_provider(name: str = "synthetic", **kwargs):
    name = (name or "synthetic").lower()
    if name == "synthetic":
        from .synthetic import SyntheticProvider
        return SyntheticProvider(**kwargs)
    if name in ("yfinance", "yahoo"):
        from .yfinance_provider import YFinanceProvider
        return YFinanceProvider(**kwargs)
    if name in ("angelone", "angel"):
        from .angelone_provider import AngelOneProvider
        return AngelOneProvider(**kwargs)
    # Phase 2+: dhan fallback (blueprint/02)
    raise ValueError(f"Unknown data provider: {name!r}")
