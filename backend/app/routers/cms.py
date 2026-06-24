"""Marketing CMS — public page render + admin management (blueprint/21)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.security import require_permissions
from ..models.cms import CmsPage, CmsSection, StatMetric, Testimonial

router = APIRouter(tags=["cms"])


# ---------------- Public (server-rendered by Next ISR) ----------------
@router.get("/api/cms/page/{slug}")
async def public_page(slug: str, locale: str = "en", db: AsyncSession = Depends(get_db)):
    page = (await db.execute(
        select(CmsPage).where(CmsPage.slug == slug, CmsPage.status == "published",
                              CmsPage.locale == locale)
    )).scalar_one_or_none()
    if page is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Page not found")
    sections = (await db.execute(
        select(CmsSection).where(CmsSection.page_id == page.id, CmsSection.is_enabled == True)  # noqa: E712
        .order_by(CmsSection.sort_order)
    )).scalars().all()
    return {
        "slug": page.slug, "title": page.title, "type": page.type, "seo": page.seo,
        "sections": [{"type": s.block_type, "content": s.content} for s in sections],
    }


@router.get("/api/cms/testimonials")
async def testimonials(locale: str = "en", db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(Testimonial).where(Testimonial.locale == locale).order_by(Testimonial.sort_order)
    )).scalars().all()
    return {"testimonials": [
        {"author": t.author_name, "role": t.role, "company": t.company,
         "quote": t.quote, "rating": t.rating, "featured": t.is_featured} for t in rows
    ]}


@router.get("/api/cms/stats")
async def stats(locale: str = "en", db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(StatMetric).where(StatMetric.locale == locale).order_by(StatMetric.sort_order)
    )).scalars().all()
    return {"stats": [
        {"key": s.key, "label": s.label, "value": s.value, "suffix": s.suffix, "live": s.is_live}
        for s in rows
    ]}


# ---------------- Admin (blueprint/21 §6) ----------------
@router.get("/api/admin/cms/pages")
async def admin_pages(_=Depends(require_permissions("content.manage")), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(CmsPage).order_by(CmsPage.sort_order))).scalars().all()
    return {"pages": [
        {"id": str(p.id), "slug": p.slug, "title": p.title, "type": p.type,
         "status": p.status, "locale": p.locale} for p in rows
    ]}
