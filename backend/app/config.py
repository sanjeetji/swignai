"""Tunable strategy parameters — the single source of truth for the picker.

Every number the picker/risk/exit logic uses lives here (blueprint/04-picker-strategy.md).
Keeping them in one dataclass makes the strategy auditable and lets the backtest
sweep parameters without touching logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StrategyConfig:
    # --- GATE 0: market regime (NIFTY) ---
    regime_index: str = "^NSEI"          # NIFTY 50
    regime_ema: int = 20                 # NIFTY EMA period for the bull/bear gate

    # --- STAGE 1: knockout filters ---
    min_turnover_cr: float = 25.0        # 20-day avg traded value, ₹ crore
    weekly_ema: int = 20                 # weekly tide (computed on resampled weekly closes)
    daily_trend_ema: int = 50            # price must be above this
    slope_ema: int = 20                  # this EMA must be sloping up
    # tightened from 8→4 after walk-forward research (blueprint/05): chasing over-extended
    # entries was the main bull-regime bleed; ≤4% above EMA20 generalises materially better.
    max_extension_pct: float = 4.0       # reject if price > X% above slope_ema
    atr_period: int = 14
    atr_min_pct: float = 1.5             # volatility floor (% of price)
    atr_max_pct: float = 5.0             # volatility ceiling
    min_rr: float = 2.0                  # a valid stop must allow >= this reward:risk
    # optional signal gates (0/False/≥1.5 = OFF; enabled only if walk-forward proves OOS edge).
    # ADX≥25 ADOPTED after round-2 walk-forward (research_edge.py): the only gate positive in
    # EVERY window — it flips the recent 2024–26 out-of-sample window +0.135→+0.157R avg and
    # −0.014→+0.015R recent (only trade stocks in a genuine strong trend). OBV/Bollinger rejected
    # (inconsistent across windows / negative recent window = overfit). Kept as knobs for future research.
    adx_min: float = 25.0                # require ADX(14) >= X (trend strength); 0 = off
    require_obv_accum: bool = False      # require OBV accumulation (volume confirming the move)
    bb_max_pct_b: float = 1.5            # reject if Bollinger %b > X (band over-extension); ≥1.5 = off

    # --- STAGE 2: weighted score (must sum to 100) ---
    w_rel_strength: float = 25.0
    w_trend_quality: float = 20.0
    w_setup_proximity: float = 20.0
    w_volume: float = 15.0
    w_momentum: float = 12.0
    w_rr_quality: float = 8.0

    # indicator params used by the score
    rsi_period: int = 14
    rsi_low: float = 50.0                # momentum sweet spot
    rsi_high: float = 60.0               # lowered 65→60 (walk-forward): avoid overbought chases
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    rel_strength_lookback: int = 20      # trading days vs index
    volume_avg_period: int = 20
    volume_surge: float = 1.5            # today vs 20d avg considered "confirmed"
    breakout_lookback: int = 20          # recent high used for setup proximity / entry

    # --- STAGE 3: risk engine / trade plan ---
    risk_pct: float = 1.0                # % of capital risked per trade
    atr_stop_mult: float = 1.5           # stop = entry - mult*ATR (or swing low, tighter)
    swing_low_lookback: int = 10
    target_1_r: float = 2.0
    target_2_r: float = 3.0
    max_open_positions: int = 4
    max_position_pct: float = 20.0       # max capital in one stock
    max_portfolio_heat_pct: float = 6.0  # sum of live risk across open positions

    # --- exits ---
    breakeven_trigger_pct: float = 3.0   # move stop to entry at +3%
    trail_trigger_pct: float = 6.0       # at +6% ...
    trail_lock_pct: float = 3.0          # ... lock stop at +3%
    max_hold_days: int = 15              # time stop (swing, not investment)

    # --- selection ---
    top_n: int = 5
    min_flags_required: int = 0          # all knockouts are hard; kept for future soft scoring
    warmup_bars: int = 220               # bars of history needed before signals are valid

    def total_weight(self) -> float:
        return (
            self.w_rel_strength + self.w_trend_quality + self.w_setup_proximity
            + self.w_volume + self.w_momentum + self.w_rr_quality
        )


DEFAULT = StrategyConfig()
