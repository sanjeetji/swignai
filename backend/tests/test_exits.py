"""Exit engine tests — SL/target/breakeven/scratch ordering (blueprint/11 §3)."""
from app.config import DEFAULT
from app.quant.exits import Position, check_bar, update_stop


def _pos(entry=100.0):
    rps = 5.0
    return Position(symbol="X", entry=entry, stop=entry - rps, target_2=entry + 3 * rps,
                    quantity=10, risk_per_share=rps, entry_index=0)


def test_breakeven_moves_stop_to_entry():
    pos = _pos()
    update_stop(pos, high=103.5, cfg=DEFAULT)  # +3.5% > breakeven_trigger 3%
    assert pos.stop == pos.entry
    assert pos.breakeven_done


def test_trail_locks_profit():
    pos = _pos()
    update_stop(pos, high=106.5, cfg=DEFAULT)  # +6.5% > trail_trigger 6%
    assert pos.stop == pos.entry * (1 + DEFAULT.trail_lock_pct / 100.0)
    assert pos.trail_done


def test_target_hit_is_profit():
    pos = _pos()
    res = check_bar(pos, bar_high=116.0, bar_low=101.0, cfg=DEFAULT)  # T2 = 115
    assert res is not None and res.status == "closed_profit" and res.reason == "target"


def test_stop_hit_is_loss():
    pos = _pos()
    res = check_bar(pos, bar_high=101.0, bar_low=94.0, cfg=DEFAULT)  # stop 95
    assert res is not None and res.status == "closed_loss" and res.reason == "stoploss"


def test_breakeven_then_flat_exit_is_scratch():
    pos = _pos()
    update_stop(pos, high=104.0, cfg=DEFAULT)        # stop -> entry (breakeven)
    res = check_bar(pos, bar_high=100.5, bar_low=99.5, cfg=DEFAULT)  # hits stop=entry
    assert res is not None and res.status == "scratch"


def test_stop_checked_before_target_when_both_in_bar():
    # a bar that spans both stop and target -> conservative: never a target win.
    # (the high also trails the stop up, so the exit is a loss/scratch, not a profit.)
    pos = _pos()
    res = check_bar(pos, bar_high=116.0, bar_low=94.0, cfg=DEFAULT)
    assert res is not None
    assert res.reason != "target"
    assert res.status != "closed_profit"
