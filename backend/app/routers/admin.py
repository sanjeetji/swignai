"""Super Admin control plane — users, appearance, integrations, events (blueprint/16-19,22).

All endpoints permission-gated server-side. Full-page UIs consume these (blueprint/16).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.security import require_permissions
from ..models.event import EventLog
from ..models.platform import FeatureFlag, Integration, PlatformSetting
from ..models.session import LoginHistory, UserBlock, UserSession
from ..models.user import User
from ..schemas import AppearanceIn, IntegrationIn, PlanIn
from ..services import event_log as ev
from ..services import secret_box

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ---------------- Users (blueprint/18) ----------------
@router.get("/users")
async def list_users(q: str | None = None, page: int = 1, size: int = 25,
                     _=Depends(require_permissions("users.read")), db: AsyncSession = Depends(get_db)):
    stmt = select(User)
    if q:
        stmt = stmt.where(User.email.ilike(f"%{q}%"))
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    rows = (await db.execute(stmt.order_by(desc(User.created_at)).offset((page - 1) * size).limit(size))).scalars().all()
    return {
        "total": total, "page": page, "size": size,
        "users": [
            {"id": str(u.id), "email": u.email, "name": u.name, "tier": u.subscription_tier,
             "blocked": u.is_blocked, "created_at": str(u.created_at)}
            for u in rows
        ],
    }


@router.post("/users/{user_id}/block")
async def block_user(user_id: str, req: Request, admin=Depends(require_permissions("users.block")),
                     db: AsyncSession = Depends(get_db)):
    user = await db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    user.is_blocked = True
    db.add(UserBlock(user_id=user.id, blocked_by=admin.id, reason="admin action"))
    # revoke sessions
    for s in (await db.execute(select(UserSession).where(UserSession.user_id == user.id))).scalars():
        s.is_active = False
        s.revoked_at = datetime.now(timezone.utc)
    await ev.admin(db, "user.blocked", level="warning", user=admin, resource="user", resource_id=user.id,
                   ip=req.client.host if req.client else None)
    await db.commit()
    return {"id": str(user.id), "blocked": True}


@router.post("/users/{user_id}/force-logout")
async def force_logout(user_id: str, admin=Depends(require_permissions("users.read")),
                       db: AsyncSession = Depends(get_db)):
    user = await db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    n = 0
    for s in (await db.execute(select(UserSession).where(UserSession.user_id == user.id))).scalars():
        if s.is_active:
            s.is_active = False
            s.revoked_at = datetime.now(timezone.utc)
            n += 1
    await ev.admin(db, "session.force_logout", user=admin, resource="user", resource_id=user.id,
                   payload={"revoked": n})
    await db.commit()
    return {"id": str(user.id), "revoked": n}


@router.post("/users/{user_id}/impersonate")
async def impersonate(user_id: str, admin=Depends(require_permissions("users.impersonate")),
                      db: AsyncSession = Depends(get_db)):
    """Issue a session token for a target user — support 'view as'. Audit-logged; the token
    carries an `imp` claim (the admin's id) so impersonated activity is traceable."""
    from ..core.config import settings
    from ..core.security import create_access_token, create_refresh_token

    target = await db.get(User, uuid.UUID(user_id))
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if target.is_blocked:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User is blocked")
    now = datetime.now(timezone.utc)
    sess = UserSession(user_id=target.id, is_active=True, last_active_at=now, geo={},
                       device="impersonation",
                       expires_at=now + timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS))
    db.add(sess)
    await db.flush()
    await ev.admin(db, "user.impersonated", level="warning", user=admin, resource="user",
                   resource_id=user_id, payload={"target": target.email})
    await db.commit()
    return {"access_token": create_access_token(str(target.id), extra={"sid": str(sess.id), "imp": str(admin.id)}),
            "refresh_token": create_refresh_token(str(target.id), str(sess.id)),
            "email": target.email}


@router.post("/users/{user_id}/unblock")
async def unblock_user(user_id: str, admin=Depends(require_permissions("users.block")),
                       db: AsyncSession = Depends(get_db)):
    user = await db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    user.is_blocked = False
    await ev.admin(db, "user.unblocked", user=admin, resource="user", resource_id=user.id)
    await db.commit()
    return {"id": str(user.id), "blocked": False}


@router.get("/users/{user_id}")
async def user_detail(user_id: str, _=Depends(require_permissions("users.read")),
                      db: AsyncSession = Depends(get_db)):
    """Profile + active/recent sessions (IP, geo, device) + recent login history (blueprint/18)."""
    user = await db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    sessions = (await db.execute(
        select(UserSession).where(UserSession.user_id == user.id)
        .order_by(desc(UserSession.created_at)).limit(20)
    )).scalars().all()
    logins = (await db.execute(
        select(LoginHistory).where(LoginHistory.user_id == user.id)
        .order_by(desc(LoginHistory.created_at)).limit(20)
    )).scalars().all()
    return {
        "id": str(user.id), "email": user.email, "name": user.name,
        "tier": user.subscription_tier, "blocked": user.is_blocked,
        "capital_amount": float(user.capital_amount), "risk_pct": float(user.risk_pct),
        "created_at": str(user.created_at),
        "sessions": [
            {"id": str(s.id), "ip": s.ip, "geo": s.geo, "device": s.device, "browser": s.browser,
             "os": s.os, "active": s.is_active, "last_active_at": str(s.last_active_at) if s.last_active_at else None,
             "created_at": str(s.created_at)} for s in sessions
        ],
        "login_history": [
            {"ip": h.ip, "geo": h.geo, "device": h.device, "success": h.success,
             "reason": h.reason, "at": str(h.created_at)} for h in logins
        ],
    }


# ---------------- Appearance / settings (blueprint/16) ----------------
async def _settings(db) -> PlatformSetting:
    ps = (await db.execute(select(PlatformSetting).limit(1))).scalar_one_or_none()
    if ps is None:
        ps = PlatformSetting()
        db.add(ps)
        await db.flush()
    return ps


@router.get("/settings/appearance")
async def get_appearance(_=Depends(require_permissions("settings.appearance")),
                         db: AsyncSession = Depends(get_db)):
    ps = await _settings(db)
    await db.commit()
    return {"default_theme_mode": ps.default_theme_mode, "default_preset": ps.default_preset,
            "default_font": ps.default_font, "default_locale": ps.default_locale,
            "locked_axes": ps.locked_axes, "enabled_locales": ps.enabled_locales,
            "maintenance_mode": ps.maintenance_mode, "maintenance_message": ps.maintenance_message}


@router.put("/settings/appearance")
async def set_appearance(body: AppearanceIn, admin=Depends(require_permissions("settings.appearance")),
                         db: AsyncSession = Depends(get_db)):
    ps = await _settings(db)
    before = {"mode": ps.default_theme_mode, "preset": ps.default_preset, "font": ps.default_font,
              "locale": ps.default_locale}
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(ps, field, val)
    await ev.admin(db, "settings.appearance.updated", user=admin, resource="platform_settings",
                   before=before, after=body.model_dump(exclude_none=True))
    await db.commit()
    return {"ok": True}


# ---------------- Integrations / secrets vault (blueprint/17) ----------------
@router.get("/integrations")
async def list_integrations(_=Depends(require_permissions("integrations.manage")),
                            db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Integration))).scalars().all()
    return {"integrations": [
        {"id": str(i.id), "category": i.category, "provider": i.provider, "enabled": i.enabled,
         "role": i.role, "config": i.config, "secret_set": i.secret_ciphertext is not None,
         "secret_hint": i.secret_meta.get("hint"), "last_status": i.last_status}
        for i in rows
    ]}


@router.put("/integrations/{provider}")
async def upsert_integration(provider: str, body: IntegrationIn,
                             admin=Depends(require_permissions("integrations.manage")),
                             db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(Integration).where(Integration.provider == provider))).scalar_one_or_none()
    if row is None:
        row = Integration(category=body.category, provider=provider)
        db.add(row)
    row.category, row.enabled, row.role, row.config = body.category, body.enabled, body.role, body.config
    if body.secret:  # encrypt at rest; never store/return plaintext
        row.secret_ciphertext = secret_box.encrypt(body.secret)
        row.secret_meta = {"hint": secret_box.mask(body.secret)}
    await ev.admin(db, "integration.upserted", level="warning", user=admin, resource="integration",
                   resource_id=provider, payload={"provider": provider})  # value NEVER logged
    await db.commit()
    return {"provider": provider, "ok": True}


@router.post("/integrations/{provider}/test")
async def test_integration(provider: str, admin=Depends(require_permissions("integrations.manage")),
                           db: AsyncSession = Depends(get_db)):
    """Connection test — decrypts the stored secret (backend-only) and pings the provider.

    Phase 1 returns a structural check (secret present + decryptable); the real per-provider
    call (LLM completion / data quote / payments ping) wires in with each provider (blueprint/17 §4).
    """
    row = (await db.execute(select(Integration).where(Integration.provider == provider))).scalar_one_or_none()
    if row is None or row.secret_ciphertext is None:
        status_label = "no_secret"
    else:
        try:
            secret_box.decrypt(row.secret_ciphertext)  # never returned to client
            status_label = "ok"
        except Exception:
            status_label = "decrypt_failed"
    if row is not None:
        row.last_status = status_label
    await ev.admin(db, "integration.test", user=admin, resource="integration", resource_id=provider,
                   payload={"status": status_label})
    await db.commit()
    return {"provider": provider, "status": status_label}


# ---------------- Event logs (blueprint/22) ----------------
@router.get("/event-logs")
async def event_logs(category: str | None = None, level: str | None = None,
                     limit: int = Query(100, ge=1, le=500),
                     _=Depends(require_permissions("events.read")), db: AsyncSession = Depends(get_db)):
    stmt = select(EventLog).order_by(desc(EventLog.created_at)).limit(limit)
    if category:
        stmt = stmt.where(EventLog.category == category)
    if level:
        stmt = stmt.where(EventLog.level == level)
    rows = (await db.execute(stmt)).scalars().all()
    return {"events": [
        {"id": str(e.id), "type": e.event_type, "category": e.category, "level": e.level,
         "actor": str(e.actor_user_id) if e.actor_user_id else None, "source": e.source,
         "resource": e.resource, "resource_id": e.resource_id, "ip": e.ip,
         "request_id": e.request_id, "created_at": str(e.created_at), "payload": e.payload}
        for e in rows
    ]}


@router.get("/event-logs/export")
async def export_event_logs(category: str | None = None, level: str | None = None,
                            limit: int = Query(5000, ge=1, le=50000),
                            _=Depends(require_permissions("events.read")), db: AsyncSession = Depends(get_db)):
    """Same filters as the viewer, streamed as a CSV download (audit/export, blueprint/22)."""
    import csv
    import io

    stmt = select(EventLog).order_by(desc(EventLog.created_at)).limit(limit)
    if category:
        stmt = stmt.where(EventLog.category == category)
    if level:
        stmt = stmt.where(EventLog.level == level)
    rows = (await db.execute(stmt)).scalars().all()

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "created_at", "type", "category", "level", "actor", "source",
                "resource", "resource_id", "ip", "request_id"])
    for e in rows:
        w.writerow([str(e.id), str(e.created_at), e.event_type, e.category, e.level,
                    str(e.actor_user_id) if e.actor_user_id else "", e.source,
                    e.resource or "", e.resource_id or "", e.ip or "", e.request_id or ""])
    return Response(
        content=buf.getvalue(), media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="event-logs.csv"'},
    )


# ---------------- Feature flags (blueprint/16) ----------------
class FeatureFlagIn(BaseModel):
    enabled: bool | None = None
    targeting: dict | None = None       # {"tiers": [...], "roles": [...]}
    description: str | None = None


@router.get("/feature-flags")
async def list_flags(_=Depends(require_permissions("feature_flags.manage")),
                     db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(FeatureFlag).order_by(FeatureFlag.key))).scalars().all()
    return {"flags": [
        {"key": f.key, "enabled": f.enabled, "targeting": f.targeting, "description": f.description}
        for f in rows
    ]}


@router.put("/feature-flags/{key}")
async def upsert_flag(key: str, body: FeatureFlagIn,
                      admin=Depends(require_permissions("feature_flags.manage")),
                      db: AsyncSession = Depends(get_db)):
    """Create or update a flag (idempotent by key). Audit-logged."""
    f = (await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))).scalar_one_or_none()
    created = f is None
    if f is None:
        f = FeatureFlag(key=key, enabled=False, targeting={})
        db.add(f)
    if body.enabled is not None:
        f.enabled = body.enabled
    if body.targeting is not None:
        f.targeting = body.targeting
    if body.description is not None:
        f.description = body.description
    await ev.admin(db, "feature_flag.upserted", user=admin, resource="feature_flag", resource_id=key,
                   payload={"created": created, "enabled": f.enabled})
    await db.commit()
    return {"key": f.key, "enabled": f.enabled, "targeting": f.targeting, "description": f.description}


@router.delete("/feature-flags/{key}")
async def delete_flag(key: str, admin=Depends(require_permissions("feature_flags.manage")),
                      db: AsyncSession = Depends(get_db)):
    f = (await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))).scalar_one_or_none()
    if not f:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Flag not found")
    await db.delete(f)
    await ev.admin(db, "feature_flag.deleted", level="warning", user=admin,
                   resource="feature_flag", resource_id=key)
    await db.commit()
    return {"deleted": key}


# ---------------- Plans (blueprint/20) — admin-managed pricing ----------------
@router.get("/plans")
async def list_plans(_=Depends(require_permissions("settings.appearance")),
                     db: AsyncSession = Depends(get_db)):
    from ..models.billing import Plan
    rows = (await db.execute(select(Plan).order_by(Plan.sort_order, Plan.price_inr))).scalars().all()
    return {"plans": [
        {"slug": p.slug, "name": p.name, "price_inr": float(p.price_inr), "interval": p.interval,
         "features": p.features or [], "trial_days": p.trial_days, "is_active": p.is_active,
         "is_featured": p.is_featured, "sort_order": p.sort_order} for p in rows
    ]}


@router.put("/plans/{slug}")
async def upsert_plan(slug: str, body: PlanIn, admin=Depends(require_permissions("settings.appearance")),
                      db: AsyncSession = Depends(get_db)):
    from ..models.billing import Plan
    p = (await db.execute(select(Plan).where(Plan.slug == slug))).scalar_one_or_none()
    created = p is None
    if p is None:
        p = Plan(slug=slug)
        db.add(p)
    p.name, p.price_inr, p.interval = body.name, body.price_inr, body.interval
    p.features, p.trial_days = body.features, body.trial_days
    p.is_active, p.is_featured, p.sort_order = body.is_active, body.is_featured, body.sort_order
    await ev.admin(db, "plan.upserted", user=admin, resource="plan", resource_id=slug,
                   payload={"created": created, "price": body.price_inr})
    await db.commit()
    return {"slug": slug, "ok": True}


@router.delete("/plans/{slug}")
async def delete_plan(slug: str, admin=Depends(require_permissions("settings.appearance")),
                      db: AsyncSession = Depends(get_db)):
    from ..models.billing import Plan
    p = (await db.execute(select(Plan).where(Plan.slug == slug))).scalar_one_or_none()
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found")
    await db.delete(p)
    await ev.admin(db, "plan.deleted", level="warning", user=admin, resource="plan", resource_id=slug)
    await db.commit()
    return {"deleted": slug}


@router.post("/rerun-pipeline")
async def rerun_pipeline(admin=Depends(require_permissions("picks.override")),
                         db: AsyncSession = Depends(get_db)):
    """Manually re-run the daily pipeline (idempotent upsert). Audit-logged."""
    from ..jobs.daily_pipeline import run as daily_run
    result = await daily_run()
    await ev.admin(db, "pipeline.rerun", user=admin, resource="ai_picks",
                   payload={"date": result.get("date"), "count": len(result.get("picks", []))})
    await db.commit()
    return {"ok": True, "date": result.get("date"), "regime": result.get("regime"),
            "picks": len(result.get("picks", []))}


@router.post("/recompute-analytics")
async def recompute_analytics(admin=Depends(require_permissions("picks.override")),
                              db: AsyncSession = Depends(get_db)):
    """Manually rebuild user_analytics from closed paper trades (nightly job on-demand)."""
    from ..jobs.recompute_analytics import run as analytics_run
    result = await analytics_run()
    await ev.admin(db, "analytics.recompute", user=admin, resource="user_analytics",
                   payload=result)
    await db.commit()
    return {"ok": True, **result}


@router.post("/run-seo-content")
async def run_seo_content(admin=Depends(require_permissions("content.manage")),
                          db: AsyncSession = Depends(get_db)):
    """Generate this week's SEO blog post from the latest picks (weekly job on-demand)."""
    from ..jobs.seo_content import run as seo_run
    result = await seo_run()
    await ev.admin(db, "content.seo_generated", user=admin, resource="cms_page", payload=result)
    await db.commit()
    return {"ok": True, **result}


@router.post("/run-retention")
async def run_retention(admin=Depends(require_permissions("picks.override")),
                        db: AsyncSession = Depends(get_db)):
    """Manually run the DPDP retention purge (stale sessions/login history/events)."""
    from ..jobs.retention import run as retention_run
    result = await retention_run()
    await ev.admin(db, "data.retention.purge", level="warning", user=admin,
                   resource="retention", payload=result)
    await db.commit()
    return {"ok": True, **result}


class RevalidateIn(BaseModel):
    paths: list[str] | None = None      # e.g. ["/en", "/en/stocks"]; defaults to locale homepages


@router.post("/revalidate")
async def admin_revalidate(body: RevalidateIn, admin=Depends(require_permissions("content.manage")),
                           db: AsyncSession = Depends(get_db)):
    """Force on-demand ISR revalidation of the given marketing paths (blueprint/08)."""
    from ..services.revalidate import LOCALES, revalidate
    paths = body.paths or [f"/{loc}" for loc in LOCALES]
    result = await revalidate(paths)
    await ev.admin(db, "content.revalidated", user=admin, resource="isr", payload={"paths": paths, **result})
    await db.commit()
    return {"ok": True, **result}


@router.get("/audit-log")
async def audit_log(limit: int = Query(100, ge=1, le=500),
                    _=Depends(require_permissions("events.read")), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(EventLog).where(EventLog.category.in_(["admin", "security"]))
        .order_by(desc(EventLog.created_at)).limit(limit)
    )).scalars().all()
    return {"events": [
        {"id": str(e.id), "type": e.event_type, "category": e.category, "level": e.level,
         "actor": str(e.actor_user_id) if e.actor_user_id else None,
         "resource": e.resource, "created_at": str(e.created_at)}
        for e in rows
    ]}
