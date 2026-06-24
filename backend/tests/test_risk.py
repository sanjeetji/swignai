"""Risk engine property tests (blueprint/11 §2)."""
import pandas as pd

from app.config import DEFAULT
from app.quant import risk


def _row(close=100.0, atr=2.0, swing_low=95.0):
    return pd.Series({"close": close, "atr": atr, "swing_low": swing_low})


def test_position_never_exceeds_max_pct():
    cfg = DEFAULT
    capital = 100000.0
    plan = risk.build_trade_plan(_row(close=10.0, atr=0.1, swing_low=9.95), capital, cfg)
    assert plan is not None
    assert plan.position_size <= capital * cfg.max_position_pct / 100.0 + 1e-6


def test_rr_at_least_target_ratio():
    plan = risk.build_trade_plan(_row(), 100000.0, DEFAULT)
    assert plan is not None
    assert plan.rr_ratio == DEFAULT.target_1_r


def test_stop_is_below_entry_and_risk_positive():
    plan = risk.build_trade_plan(_row(), 100000.0, DEFAULT)
    assert plan.stop < plan.entry
    assert plan.risk_per_share > 0


def test_tighter_stop_chosen():
    # swing low (98) is tighter than ATR stop (100 - 1.5*2 = 97) -> stop should be 98
    plan = risk.build_trade_plan(_row(close=100.0, atr=2.0, swing_low=98.0), 100000.0, DEFAULT)
    assert plan.stop == 98.0


def test_invalid_inputs_return_none():
    assert risk.build_trade_plan(_row(close=float("nan")), 100000.0, DEFAULT) is None
    assert risk.build_trade_plan(_row(atr=0.0), 100000.0, DEFAULT) is None


def test_portfolio_heat_and_can_open():
    cfg = DEFAULT
    cap = 100000.0
    open_risks = [1000.0, 1000.0]  # 2% heat
    assert risk.can_open(open_risks, 1000.0, cap, cfg) is True
    # exceed max positions
    full = [1000.0] * cfg.max_open_positions
    assert risk.can_open(full, 1000.0, cap, cfg) is False
    # exceed heat cap
    assert risk.can_open([5000.0], 5000.0, cap, cfg) is False  # 10% > 6%
