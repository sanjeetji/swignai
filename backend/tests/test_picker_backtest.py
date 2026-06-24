"""Picker + backtest integration & honesty checks (blueprint/11 §1, §4, §6)."""
import pandas as pd

from app.config import DEFAULT
from app.data.synthetic import SyntheticProvider
from app.quant import picker as picker_mod
from app.quant import regime as regime_mod
from app.quant.features import build_features
from app.backtest.engine import run_backtest
from app.backtest.metrics import summarize


def _features(provider):
    index_close = provider.get_index()
    feats = {}
    for sym in provider.get_universe():
        df = provider.get_ohlcv(sym)
        feats[sym] = build_features(df, index_close, DEFAULT)
    return feats, index_close


def test_bear_regime_yields_zero_picks():
    provider = SyntheticProvider(days=400, seed=7)
    feats, index_close = _features(provider)
    reg = regime_mod.regime_series(index_close, DEFAULT)
    bear_dates = reg.index[reg == "bear"]
    assert len(bear_dates) > 0, "synthetic data should include a bear stretch"
    # pick a bear date well past warmup
    bear_after_warmup = [d for d in bear_dates if index_close.index.get_loc(d) > DEFAULT.warmup_bars]
    assert bear_after_warmup, "need a bear date past warmup"
    picks = picker_mod.get_top_picks(bear_after_warmup[0], feats, index_close, 100000.0, DEFAULT)
    assert picks == []


def test_picker_deterministic():
    provider = SyntheticProvider(days=400, seed=7)
    feats, index_close = _features(provider)
    date = index_close.index[-1]
    a = picker_mod.get_top_picks(date, feats, index_close, 100000.0, DEFAULT)
    b = picker_mod.get_top_picks(date, feats, index_close, 100000.0, DEFAULT)
    assert [p.symbol for p in a] == [p.symbol for p in b]
    assert [p.score for p in a] == [p.score for p in b]


def test_picks_respect_top_n_and_have_valid_plans():
    provider = SyntheticProvider(days=500, seed=3)
    feats, index_close = _features(provider)
    for date in index_close.index[DEFAULT.warmup_bars::20]:
        picks = picker_mod.get_top_picks(date, feats, index_close, 100000.0, DEFAULT)
        assert len(picks) <= DEFAULT.top_n
        for p in picks:
            assert p.plan.rr_ratio >= DEFAULT.min_rr
            assert p.plan.stop < p.plan.entry
            assert p.plan.quantity > 0
            assert p.plan.position_size <= 100000.0 * DEFAULT.max_position_pct / 100.0 + 1e-6


def test_backtest_runs_and_is_consistent():
    provider = SyntheticProvider(days=500, seed=11)
    res = run_backtest(provider, capital=100000.0)
    s = res.summary
    assert s["trades"] >= 0
    if s["trades"] > 0:
        # honest win rate: wins/(wins+losses+scratches) reconciles
        decided = s["wins"] + s["losses"] + s["scratches"]
        assert decided == s["trades"]
        recomputed = round(s["wins"] / decided * 100.0, 1)
        assert recomputed == s["win_rate_pct"]


def test_win_rate_includes_scratches_in_denominator():
    from app.backtest.metrics import Trade
    trades = [
        Trade("A", "2025-01-01", "2025-01-05", 100, 110, 10, 2.0, 100, 10, "closed_profit", "target", "bull", 4),
        Trade("B", "2025-01-01", "2025-01-05", 100, 95, 10, -1.0, -50, -5, "closed_loss", "stoploss", "bull", 4),
        Trade("C", "2025-01-01", "2025-01-05", 100, 100, 10, 0.0, -5, 0, "scratch", "scratch", "bull", 4),
    ]
    s = summarize(trades)
    # 1 win out of 3 decided (incl. scratch) = 33.3%, NOT 1/2 = 50%
    assert s["win_rate_pct"] == 33.3
