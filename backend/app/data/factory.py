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
    # Phase 1.5+: angelone, dhan (blueprint/02)
    raise ValueError(f"Unknown data provider: {name!r}")
