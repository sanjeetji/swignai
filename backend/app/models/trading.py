"""Trading domain — picks, paper trades, analytics, regime, backtests (blueprint/06)."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base, TimestampMixin, uuid_pk


class AIPick(Base, TimestampMixin):
    __tablename__ = "ai_picks"
    __table_args__ = (UniqueConstraint("stock_symbol", "date_generated", name="uq_pick_symbol_date"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    stock_symbol: Mapped[str] = mapped_column(String(40), index=True)
    sector: Mapped[str | None] = mapped_column(String(60))
    date_generated: Mapped[date] = mapped_column(Date, index=True)
    score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    regime: Mapped[str | None] = mapped_column(String(10))
    entry_price: Mapped[float | None] = mapped_column(Numeric(12, 2))
    stop_loss: Mapped[float | None] = mapped_column(Numeric(12, 2))
    target_1: Mapped[float | None] = mapped_column(Numeric(12, 2))
    target_2: Mapped[float | None] = mapped_column(Numeric(12, 2))
    rr_ratio: Mapped[float | None] = mapped_column(Numeric(6, 2))
    position_size_suggested: Mapped[float | None] = mapped_column(Numeric(14, 2))
    indicators: Mapped[dict] = mapped_column(JSON, default=dict)  # rsi, macd, emas, atr_pct, vol_ratio, rel_strength
    explanation_hinglish: Mapped[str | None] = mapped_column(String(1000))
    actual_result: Mapped[str | None] = mapped_column(String(20))  # hit_target/hit_stoploss/scratch/still_open
    actual_r_multiple: Mapped[float | None] = mapped_column(Numeric(6, 3))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PaperTrade(Base, TimestampMixin):
    __tablename__ = "paper_trades"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    ai_pick_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ai_picks.id", ondelete="SET NULL"))
    stock_symbol: Mapped[str] = mapped_column(String(40))
    entry_price: Mapped[float] = mapped_column(Numeric(12, 2))
    entry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    quantity: Mapped[int] = mapped_column(Integer)
    position_size_inr: Mapped[float] = mapped_column(Numeric(14, 2))
    stop_loss_set: Mapped[float | None] = mapped_column(Numeric(12, 2))
    target_set: Mapped[float | None] = mapped_column(Numeric(12, 2))
    exit_price: Mapped[float | None] = mapped_column(Numeric(12, 2))
    exit_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pnl_inr: Mapped[float | None] = mapped_column(Numeric(14, 2))
    pnl_percent: Mapped[float | None] = mapped_column(Numeric(7, 3))
    r_multiple: Mapped[float | None] = mapped_column(Numeric(6, 3))
    status: Mapped[str] = mapped_column(String(20), default="open")  # open/closed_profit/closed_loss/scratch
    entry_reason: Mapped[str | None] = mapped_column(String(500))
    exit_reason: Mapped[str | None] = mapped_column(String(500))


class UserAnalytics(Base):
    __tablename__ = "user_analytics"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    total_trades: Mapped[int] = mapped_column(Integer, default=0)
    winning_trades: Mapped[int] = mapped_column(Integer, default=0)
    win_rate_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    expectancy_r: Mapped[float] = mapped_column(Numeric(6, 3), default=0)
    profit_factor: Mapped[float | None] = mapped_column(Numeric(6, 2))
    total_pnl_inr: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    avg_holding_days: Mapped[float | None] = mapped_column(Numeric(5, 1))
    best_sector: Mapped[str | None] = mapped_column(String(60))
    discipline_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    last_updated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RegimeLog(Base):
    __tablename__ = "regime_log"

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    nifty_close: Mapped[float | None] = mapped_column(Numeric(12, 2))
    nifty_ema20: Mapped[float | None] = mapped_column(Numeric(12, 2))
    regime: Mapped[str | None] = mapped_column(String(10))
    picks_generated: Mapped[int] = mapped_column(Integer, default=0)


class BacktestRun(Base, TimestampMixin):
    __tablename__ = "backtest_runs"

    id: Mapped[uuid.UUID] = uuid_pk()
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    trade_log: Mapped[list] = mapped_column(JSON, default=list)
