"""Marketing CMS — pages, blocks, SEO, testimonials, stats, nav, media (blueprint/21)."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base, TimestampMixin, uuid_pk


class CmsPage(Base, TimestampMixin):
    __tablename__ = "cms_pages"

    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(String(120), index=True)
    title: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(20), default="custom")  # landing/feature/pricing/about/custom
    status: Mapped[str] = mapped_column(String(12), default="draft")  # draft/published
    locale: Mapped[str] = mapped_column(String(8), default="en", index=True)
    nav_visible: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    seo: Mapped[dict] = mapped_column(JSON, default=dict)  # inline SeoMeta snapshot for the page


class CmsSection(Base, TimestampMixin):
    __tablename__ = "cms_sections"

    id: Mapped[uuid.UUID] = uuid_pk()
    page_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cms_pages.id", ondelete="CASCADE"), index=True)
    block_type: Mapped[str] = mapped_column(String(30))  # hero/features/testimonials/stats/faq/cta/pricing/richtext/media
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[dict] = mapped_column(JSON, default=dict)  # typed per block_type
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    locale: Mapped[str] = mapped_column(String(8), default="en")


class ContentCategory(Base, TimestampMixin):
    __tablename__ = "content_categories"

    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(String(120), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(String(500))
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("content_categories.id", ondelete="SET NULL"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ContentItem(Base, TimestampMixin):
    __tablename__ = "content_items"

    id: Mapped[uuid.UUID] = uuid_pk()
    category_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("content_categories.id", ondelete="SET NULL"))
    slug: Mapped[str] = mapped_column(String(120), index=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(12), default="draft")
    locale: Mapped[str] = mapped_column(String(8), default="en")
    seo: Mapped[dict] = mapped_column(JSON, default=dict)


class Testimonial(Base, TimestampMixin):
    __tablename__ = "testimonials"

    id: Mapped[uuid.UUID] = uuid_pk()
    author_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str | None] = mapped_column(String(120))
    company: Mapped[str | None] = mapped_column(String(120))
    avatar_url: Mapped[str | None] = mapped_column(String(400))
    quote: Mapped[str] = mapped_column(String(1000))
    rating: Mapped[int | None] = mapped_column(Integer)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    locale: Mapped[str] = mapped_column(String(8), default="en")


class StatMetric(Base, TimestampMixin):
    __tablename__ = "stats_metrics"

    id: Mapped[uuid.UUID] = uuid_pk()
    key: Mapped[str] = mapped_column(String(60), index=True)
    label: Mapped[str] = mapped_column(String(120))
    value: Mapped[str] = mapped_column(String(60))
    suffix: Mapped[str | None] = mapped_column(String(20))
    is_live: Mapped[bool] = mapped_column(Boolean, default=False)  # pull real backend number
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    locale: Mapped[str] = mapped_column(String(8), default="en")


class Faq(Base, TimestampMixin):
    __tablename__ = "faqs"

    id: Mapped[uuid.UUID] = uuid_pk()
    category: Mapped[str | None] = mapped_column(String(60))
    question: Mapped[str] = mapped_column(String(400))
    answer: Mapped[str] = mapped_column(String(2000))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    locale: Mapped[str] = mapped_column(String(8), default="en")


class NavigationMenu(Base, TimestampMixin):
    __tablename__ = "navigation_menus"

    id: Mapped[uuid.UUID] = uuid_pk()
    location: Mapped[str] = mapped_column(String(20))  # header/footer
    items: Mapped[list] = mapped_column(JSON, default=list)
    locale: Mapped[str] = mapped_column(String(8), default="en")


class MediaAsset(Base, TimestampMixin):
    __tablename__ = "media_assets"

    id: Mapped[uuid.UUID] = uuid_pk()
    url: Mapped[str] = mapped_column(String(500))
    type: Mapped[str | None] = mapped_column(String(20))
    alt_text: Mapped[str | None] = mapped_column(String(255))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)


class SeoMeta(Base, TimestampMixin):
    __tablename__ = "seo_meta"

    id: Mapped[uuid.UUID] = uuid_pk()
    owner_type: Mapped[str] = mapped_column(String(30))  # page/category/item/global
    owner_id: Mapped[str | None] = mapped_column(String(64), index=True)
    title: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(400))
    canonical: Mapped[str | None] = mapped_column(String(400))
    og: Mapped[dict] = mapped_column(JSON, default=dict)
    twitter: Mapped[dict] = mapped_column(JSON, default=dict)
    json_ld: Mapped[dict] = mapped_column(JSON, default=dict)
    robots: Mapped[str | None] = mapped_column(String(60))
    keywords: Mapped[str | None] = mapped_column(String(400))
    hreflang: Mapped[dict] = mapped_column(JSON, default=dict)


class ContentVersion(Base, TimestampMixin):
    __tablename__ = "content_versions"

    id: Mapped[uuid.UUID] = uuid_pk()
    owner_type: Mapped[str] = mapped_column(String(30))
    owner_id: Mapped[str] = mapped_column(String(64), index=True)
    snapshot: Mapped[dict] = mapped_column(JSON)
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    note: Mapped[str | None] = mapped_column(String(255))
