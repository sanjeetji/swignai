"""Transaction-cost model — a backtest net of costs is the only honest one (blueprint/05).

Rough Indian delivery-equity costs: brokerage (often ~0 for delivery), STT, exchange
+ SEBI + stamp charges, plus a slippage assumption (worse for thinner names). Tuned
to be conservative, not precise — the point is to not report fantasy gross returns.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostModel:
    brokerage_pct: float = 0.0      # delivery brokerage (many brokers ₹0)
    stt_pct: float = 0.1            # securities transaction tax (~0.1% each side, delivery)
    charges_pct: float = 0.012      # exchange + SEBI + stamp + GST, approx, per side
    slippage_pct: float = 0.15      # fill slippage per side (15-min delayed data, liquid names)

    def per_side_pct(self) -> float:
        return self.brokerage_pct + self.stt_pct + self.charges_pct + self.slippage_pct

    def round_trip_cost(self, entry_value: float, exit_value: float) -> float:
        """Total ₹ cost for entering at entry_value and exiting at exit_value."""
        return entry_value * self.per_side_pct() / 100.0 + exit_value * self.per_side_pct() / 100.0


DEFAULT_COSTS = CostModel()
