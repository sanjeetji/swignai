"""Provider factory — select the data source by name (one config line).

If DATA_PROVIDER_FALLBACK is set (and differs from the primary), the primary is wrapped
in a FallbackProvider so a vendor hiccup transparently fails over (blueprint/02 §4.2).
"""
from __future__ import annotations


def _make(name: str, **kwargs):
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
    if name == "dhan":
        from .dhan_provider import DhanProvider
        return DhanProvider(**kwargs)
    raise ValueError(f"Unknown data provider: {name!r}")


def get_provider(name: str = "synthetic", **kwargs):
    primary = _make(name, **kwargs)
    from ..core.config import settings
    fb = settings.DATA_PROVIDER_FALLBACK
    if fb and fb.lower() != (name or "").lower():
        from .fallback import FallbackProvider
        return FallbackProvider(primary, _make(fb, **kwargs))
    return primary
