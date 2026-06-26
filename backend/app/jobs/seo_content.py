"""Weekly SEO content (blueprint/07,12) — generate a 'top setups this week' blog post
from the latest real picks. Deterministic + honest (no fabricated claims); published as a
CmsPage(type='blog') so it's admin-editable and served by the existing CMS endpoints.
Idempotent per week (upsert by slug).
"""
from __future__ import annotations

import logging

from sqlalchemy import desc, select

from ..core.db import SessionLocal
from ..models.cms import CmsPage, CmsSection
from ..models.trading import AIPick

logger = logging.getLogger("seo_content")


async def run() -> dict:
    async with SessionLocal() as db:
        latest = (await db.execute(
            select(AIPick.date_generated).order_by(desc(AIPick.date_generated)).limit(1)
        )).scalar_one_or_none()
        if not latest:
            return {"created": False, "reason": "no picks yet"}
        picks = (await db.execute(
            select(AIPick).where(AIPick.date_generated == latest).order_by(desc(AIPick.score)).limit(5)
        )).scalars().all()
        regime = (picks[0].regime if picks else "neutral") or "neutral"

        slug = f"weekly-{latest.isoformat()}"
        title = f"Top swing setups — week of {latest:%d %b %Y}"
        lines = [f"Market regime gate: **{regime}**.", ""]
        if not picks:
            lines.append("No qualifying setups this week — the regime filter kept us in capital-preservation mode.")
        else:
            lines.append(f"The screener surfaced {len(picks)} setups that passed every knockout filter:")
            lines.append("")
            for p in picks:
                lines.append(
                    f"- **{p.stock_symbol}** ({p.sector or 'NSE'}) — quant score {round(float(p.score or 0))}, "
                    f"entry ₹{p.entry_price}, stop ₹{p.stop_loss}, target ₹{p.target_1} (R:R {p.rr_ratio})."
                )
        lines += ["", "Every level is deterministic math on real prices — educational technical analysis, "
                      "not investment advice. Past or screened setups do not guarantee future returns."]
        body = "\n".join(lines)

        page = (await db.execute(select(CmsPage).where(CmsPage.slug == slug))).scalar_one_or_none()
        if page is None:
            page = CmsPage(slug=slug, type="blog", locale="en", title=title)
            db.add(page)
            await db.flush()
        page.title = title
        page.status = "published"
        page.nav_visible = False
        page.seo = {"title": f"{title} | SwingAI",
                    "description": f"The week's top {len(picks)} deterministic NSE swing setups ({regime} regime). "
                                   "Educational analysis, not advice.",
                    "canonical": f"/blog/{slug}"}
        for s in (await db.execute(select(CmsSection).where(CmsSection.page_id == page.id))).scalars().all():
            await db.delete(s)
        db.add(CmsSection(page_id=page.id, block_type="prose", sort_order=0, content={"markdown": body}))
        await db.commit()
        logger.info("seo_content: published %s (%d picks)", slug, len(picks))
        return {"created": True, "slug": slug, "picks": len(picks)}
