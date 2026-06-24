"""Exit management — deterministic; report scratches honestly (blueprint/04 §6).

Initial stop -> breakeven at +3% -> trail-lock +3% at +6% -> time stop.
A breakeven exit at ~0% is a SCRATCH and is counted in the denominator of the
track record (never excluded to inflate win rate — blueprint/00 non-negotiable #2).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..config import StrategyConfig


@dataclass
class Position:
    symbol: str
    entry: float
    stop: float
    target_2: float
    quantity: int
    risk_per_share: float
    entry_index: int                 # bar index of entry (for max-hold)
    stop0: float = field(default=0.0)  # original stop (for scratch classification)
    breakeven_done: bool = False
    trail_done: bool = False

    def __post_init__(self):
        if not self.stop0:
            self.stop0 = self.stop


@dataclass
class ExitResult:
    exit_price: float
    reason: str            # target / stoploss / scratch / time
    status: str            # closed_profit / closed_loss / scratch


def update_stop(pos: Position, high: float, cfg: StrategyConfig) -> None:
    """Ratchet the stop up based on intrabar high (breakeven, then trail-lock)."""
    gain_pct = (high - pos.entry) / pos.entry * 100.0
    if gain_pct >= cfg.trail_trigger_pct and not pos.trail_done:
        pos.stop = max(pos.stop, pos.entry * (1 + cfg.trail_lock_pct / 100.0))
        pos.trail_done = True
        pos.breakeven_done = True
    elif gain_pct >= cfg.breakeven_trigger_pct and not pos.breakeven_done:
        pos.stop = max(pos.stop, pos.entry)
        pos.breakeven_done = True


SCRATCH_BAND_PCT = 0.5  # exits within ±0.5% of entry are "essentially breakeven"


def classify_exit(pos: Position, exit_price: float, reason: str) -> ExitResult:
    """Classify by REALIZED move, honestly:
      - target hit                     -> closed_profit
      - exit >= +0.5%  (incl. trail-locked gains) -> closed_profit
      - exit <= -0.5%                  -> closed_loss
      - within ±0.5% of entry          -> scratch (counted in the denominator, blueprint/00 #2)
    A 'scratch' means essentially flat — NOT a hidden small win or loss.
    """
    pnl_pct = (exit_price - pos.entry) / pos.entry * 100.0
    if reason == "target":
        return ExitResult(exit_price, "target", "closed_profit")
    if pnl_pct >= SCRATCH_BAND_PCT:
        return ExitResult(exit_price, reason, "closed_profit")
    if pnl_pct <= -SCRATCH_BAND_PCT:
        return ExitResult(exit_price, reason, "closed_loss")
    return ExitResult(exit_price, "scratch", "scratch")


def check_bar(pos: Position, bar_high: float, bar_low: float,
              cfg: StrategyConfig) -> ExitResult | None:
    """Evaluate one daily bar against an open position.

    Standard convention to avoid intrabar artifacts:
      1. Exits are checked against the stop as it stands at the START of the bar.
      2. Conservative ordering: stop (low) is checked BEFORE target (high), so a bar
         spanning both is treated as a stop.
      3. Only if no exit occurs do we trail the stop from this bar's high — protecting
         SUBSEQUENT bars, never causing a same-bar stop-out after the target was hit.
    Time stop is handled by the caller (exit at bar close)."""
    start_stop = pos.stop

    if bar_low <= start_stop:
        return classify_exit(pos, start_stop, "stoploss")
    if bar_high >= pos.target_2:
        return classify_exit(pos, pos.target_2, "target")

    # no exit -> ratchet the stop up for future bars
    update_stop(pos, bar_high, cfg)
    return None
