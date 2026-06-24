"""Event-driven backtest — signal on close[t], enter at open[t+1], net of costs.

Honest by construction (blueprint/05):
  - No look-ahead: features at row t use only data <= t; entries fill at the NEXT
    bar's open; exits evaluate bars at/after entry.
  - Net of costs: every round trip subtracts brokerage+STT+charges+slippage.
  - R-multiples + regime segmentation reported.
  - Same picker code path as production (app.quant.picker).

NOTE: the synthetic provider proves the harness RUNS and is internally consistent;
it is NOT evidence of real edge. Only a yfinance (real-data) run is (blueprint/05 §6).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from ..config import StrategyConfig, DEFAULT
from ..quant import picker as picker_mod
from ..quant import regime as regime_mod
from ..quant.exits import Position, check_bar, classify_exit
from ..quant.features import build_features
from .costs import CostModel, DEFAULT_COSTS
from .metrics import Trade, summarize, summarize_by_regime


@dataclass
class BacktestResult:
    trades: list[Trade]
    equity_curve: list[float]
    summary: dict
    by_regime: dict
    starting_capital: float
    config: StrategyConfig = field(repr=False, default=DEFAULT)


@dataclass
class _Live:
    pos: Position
    entry_date: pd.Timestamp
    regime: str
    risk_amount: float


def run_backtest(
    provider,
    start=None,
    end=None,
    capital: float = 100000.0,
    cfg: StrategyConfig = DEFAULT,
    costs: CostModel = DEFAULT_COSTS,
    trade_start=None,
) -> BacktestResult:
    """`trade_start` (optional) restricts NEW entries to dates >= it, while still
    using all earlier bars for warmup/features — used by walk_forward so each window
    shares prior history (standard anchored walk-forward)."""
    universe = provider.get_universe()
    index_close = provider.get_index(start, end)

    # Precompute features per symbol (no look-ahead inside a row).
    features: dict[str, pd.DataFrame] = {}
    raw: dict[str, pd.DataFrame] = {}
    for sym in universe:
        df = provider.get_ohlcv(sym, start, end)
        if df is None or df.empty or len(df) < cfg.warmup_bars + 5:
            continue
        raw[sym] = df
        features[sym] = build_features(df, index_close, cfg)

    if not features:
        return BacktestResult([], [capital], {"trades": 0, "note": "insufficient data"}, {}, capital, cfg)

    dates = index_close.index
    trade_start_ts = pd.Timestamp(trade_start) if trade_start is not None else None
    trades: list[Trade] = []
    equity = capital
    equity_curve: list[float] = []
    live: dict[str, _Live] = {}
    pending: list[tuple[str, object]] = []  # (symbol, TradePlan) queued at close[t] for open[t+1]

    start_i = cfg.warmup_bars
    for i in range(start_i, len(dates)):
        today = dates[i]

        # 1) Execute pending entries at today's OPEN (signalled at yesterday's close)
        for sym, plan in pending:
            if sym in live or len(live) >= cfg.max_open_positions:
                continue
            df = raw.get(sym)
            if df is None or today not in df.index:
                continue
            entry = float(df.loc[today, "open"])
            rps = plan.risk_per_share
            if rps <= 0 or plan.quantity <= 0:
                continue
            stop = entry - rps
            target_2 = entry + cfg.target_2_r * rps
            risk_amount = plan.quantity * rps
            # portfolio heat guard
            open_risk = [l.risk_amount for l in live.values()]
            if sum(open_risk + [risk_amount]) / capital * 100.0 > cfg.max_portfolio_heat_pct:
                continue
            live[sym] = _Live(
                pos=Position(symbol=sym, entry=entry, stop=stop, target_2=target_2,
                             quantity=plan.quantity, risk_per_share=rps, entry_index=i),
                entry_date=today,
                regime=regime_mod.regime_for_date(index_close, today, cfg),
                risk_amount=risk_amount,
            )
        pending = []

        # 2) Manage open positions against today's bar
        for sym in list(live.keys()):
            lv = live[sym]
            df = raw.get(sym)
            if df is None or today not in df.index:
                continue
            bar = df.loc[today]
            res = check_bar(lv.pos, float(bar["high"]), float(bar["low"]), cfg)
            exit_price = None
            reason = None
            status = None
            if res is not None:
                exit_price, reason, status = res.exit_price, res.reason, res.status
            elif (i - lv.pos.entry_index) >= cfg.max_hold_days:
                er = classify_exit(lv.pos, float(bar["close"]), "time")
                exit_price, reason, status = er.exit_price, er.reason, er.status

            if exit_price is not None:
                trades.append(_close_trade(lv, sym, today, exit_price, reason, status, costs))
                equity += trades[-1].pnl_inr
                del live[sym]

        equity_curve.append(round(equity, 2))

        # 3) Generate picks at today's CLOSE -> queue for tomorrow's open
        #    (only enter within the trade window; earlier bars are warmup only)
        in_window = trade_start_ts is None or today >= trade_start_ts
        if in_window and i + 1 < len(dates) and len(live) < cfg.max_open_positions:
            picks = picker_mod.get_top_picks(today, features, index_close, capital, cfg)
            free = cfg.max_open_positions - len(live)
            for p in picks:
                if p.symbol in live:
                    continue
                pending.append((p.symbol, p.plan))
                free -= 1
                if free <= 0:
                    break

    # close any still-open at the last close (mark to market)
    last = dates[-1]
    for sym, lv in list(live.items()):
        df = raw.get(sym)
        if df is None or last not in df.index:
            continue
        px = float(df.loc[last, "close"])
        er = classify_exit(lv.pos, px, "time")
        trades.append(_close_trade(lv, sym, last, er.exit_price, er.reason, er.status, costs))
        equity += trades[-1].pnl_inr
    equity_curve.append(round(equity, 2))

    summary = summarize(trades, equity_curve)
    summary["starting_capital"] = capital
    summary["ending_equity"] = round(equity, 2)
    summary["return_pct"] = round((equity - capital) / capital * 100.0, 2)
    return BacktestResult(trades, equity_curve, summary, summarize_by_regime(trades), capital, cfg)


def _close_trade(lv: _Live, sym, exit_date, exit_price, reason, status, costs: CostModel) -> Trade:
    pos = lv.pos
    qty = pos.quantity
    entry_value = qty * pos.entry
    exit_value = qty * exit_price
    cost = costs.round_trip_cost(entry_value, exit_value)
    pnl_gross = exit_value - entry_value
    pnl_net = pnl_gross - cost
    r_multiple = (exit_price - pos.entry) / pos.risk_per_share if pos.risk_per_share > 0 else 0.0
    hold_days = (exit_date - lv.entry_date).days
    return Trade(
        symbol=sym,
        entry_date=str(lv.entry_date.date()),
        exit_date=str(exit_date.date()),
        entry=round(pos.entry, 2),
        exit=round(exit_price, 2),
        quantity=qty,
        r_multiple=round(r_multiple, 3),
        pnl_inr=round(pnl_net, 2),
        pnl_pct=round((exit_price - pos.entry) / pos.entry * 100.0, 2),
        status=status,
        reason=reason,
        regime=lv.regime,
        hold_days=hold_days,
    )


def walk_forward(provider, n_windows: int = 3, **kwargs) -> dict:
    """Run the backtest over sequential time windows and report each.

    The default strategy is rule-based (no parameters fitted to data), so every
    window is effectively out-of-sample. When parameter optimization is added, the
    train window tunes and ONLY the test window is reported (blueprint/05 §3).
    """
    index_close = provider.get_index()
    dates = index_close.index
    if len(dates) == 0:
        return {"windows": []}
    n = len(dates)
    bounds = [dates[min(int(n * k / n_windows), n - 1)] for k in range(n_windows + 1)]
    out = []
    for w in range(n_windows):
        # Use ALL history up to this window's end for warmup/features; only ENTER
        # trades within [bounds[w], bounds[w+1]]. The first window may have few/no
        # trades (its span is consumed by the warmup period) — expected & honest.
        res = run_backtest(provider, start=None, end=bounds[w + 1],
                           trade_start=bounds[w], **kwargs)
        out.append({"window": w + 1, "start": str(bounds[w].date()),
                    "end": str(bounds[w + 1].date()), "summary": res.summary})
    return {"windows": out}
