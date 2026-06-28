"""Digest emails (blueprint/13 retention) — keep users with the latest info.

- daily_digest  (4:00 PM IST, after the pipeline): today's screened setups + the user's open
  positions, to every opted-in user.
- weekly_digest (Sunday 6:00 PM IST): each active user's own week — trades, win%, net P&L, expectancy.

Email is best-effort (vault→.env SMTP); when unconfigured it's a no-op. An in-app notification is
always created so the digest is visible in the bell even without email set up. Honest framing only.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from ..core.db import SessionLocal
from ..models.platform import UserPreference
from ..models.trading import AIPick, PaperTrade
from ..models.user import User
from ..services import email as email_svc
from ..services.notify import push

logger = logging.getLogger("digest")

DISCLAIMER = "— SwingAI. Educational technical screening, not investment advice."


async def _recipients(db) -> list[User]:
    users = (await db.execute(select(User).where(User.is_blocked == False))).scalars().all()  # noqa: E712
    prefs = {p.user_id: p.email_digest for p in
             (await db.execute(select(UserPreference))).scalars().all()}
    return [u for u in users if prefs.get(u.id, True) is not False]


async def _deliver(db, user, subject: str, body: str, type_: str) -> bool:
    await push(db, user.id, type_, {"subject": subject, "body": body}, fanout=False)
    if user.email:
        return await email_svc.send_email(user.email, subject, body, db=db)
    return False


async def daily_digest() -> dict:
    sent = 0
    async with SessionLocal() as db:
        latest = (await db.execute(select(func.max(AIPick.date_generated)))).scalar()
        picks = []
        if latest:
            picks = (await db.execute(select(AIPick).where(AIPick.date_generated == latest)
                     .order_by(AIPick.score.desc()).limit(5))).scalars().all()
        regime = picks[0].regime if picks else "cash"
        head = [f"Market regime: {regime}", ""]
        if picks:
            head.append("Today's top screened setups (educational, not advice):")
            for p in picks:
                head.append(f"• {p.stock_symbol} — score {round(p.score)}, "
                            f"entry ₹{round(float(p.entry_price), 2)}, "
                            f"stop ₹{round(float(p.stop_loss), 2)}, "
                            f"target ₹{round(float(p.target_1), 2)}")
        else:
            head.append("No setups today — the regime filter is keeping us in cash. "
                        "Sitting out is a position.")
        subject = f"SwingAI — {len(picks)} setups today ({regime})"

        for u in await _recipients(db):
            body = list(head)
            opens = (await db.execute(select(PaperTrade).where(
                PaperTrade.user_id == u.id, PaperTrade.status == "open"))).scalars().all()
            if opens:
                body.append("")
                body.append("Your open positions:")
                for t in opens:
                    body.append(f"• {t.stock_symbol} (qty {t.quantity}, "
                                f"stop ₹{round(float(t.stop_loss_set or 0), 2)})")
            body.append("")
            body.append(DISCLAIMER)
            if await _deliver(db, u, subject, "\n".join(body), "digest.daily"):
                sent += 1
        await db.commit()
    logger.info("daily_digest: emailed %s users", sent)
    return {"sent": sent}


async def weekly_digest() -> dict:
    sent = 0
    since = datetime.now(timezone.utc) - timedelta(days=7)
    async with SessionLocal() as db:
        for u in await _recipients(db):
            trades = (await db.execute(select(PaperTrade).where(
                PaperTrade.user_id == u.id, PaperTrade.status != "open",
                PaperTrade.exit_date >= since))).scalars().all()
            if not trades:
                continue            # nothing happened this week — don't nag
            wins = [t for t in trades if (t.pnl_inr or 0) > 0]
            losses = [t for t in trades if (t.pnl_inr or 0) < 0]
            scratches = [t for t in trades if t not in wins and t not in losses]
            decided = len(wins) + len(losses) + len(scratches)
            total_pnl = sum(float(t.pnl_inr or 0) for t in trades)
            avg_r = sum(float(t.r_multiple or 0) for t in trades) / len(trades)
            win_pct = round(len(wins) / decided * 100) if decided else 0
            subject = f"SwingAI — your week: {len(trades)} trades, ₹{round(total_pnl)} P&L"
            body = [
                "Your paper-trading week (honest, R-based):", "",
                f"• Trades closed: {len(trades)}",
                f"• Win rate: {win_pct}% ({len(wins)}W / {len(losses)}L / {len(scratches)} scratch)",
                f"• Net P&L: ₹{round(total_pnl, 2)}",
                f"• Expectancy: {round(avg_r, 2)}R per trade", "",
                "Process over outcome — keep the risk fixed and let the edge play out.", "",
                DISCLAIMER,
            ]
            if await _deliver(db, u, subject, "\n".join(body), "digest.weekly"):
                sent += 1
        await db.commit()
    logger.info("weekly_digest: emailed %s users", sent)
    return {"sent": sent}
