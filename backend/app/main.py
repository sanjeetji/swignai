"""FastAPI app — the SwingAI platform API (blueprint/07).

Boots with zero external infra in dev (async SQLite, no Redis). Production points
DATABASE_URL at Postgres (Supabase) and runs Alembic migrations instead of init_db.
"""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import JSONResponse

from . import brand
from .core.config import settings
from .core.db import init_db
from .core.observability import init_sentry
from .core.ratelimit import allow
from .routers import (admin, auth, billing, cms, health, me, metrics, notifications, paper,
                      picks, platform, referral, stocks)

# Initialise error tracking before the app is built (no-op without SENTRY_DSN).
init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # dev convenience: create tables + seed if empty. prod uses Alembic + seed script.
    await init_db()
    from .seed import seed_if_empty
    await seed_if_empty()
    if settings.ENABLE_SCHEDULER:
        from .jobs.scheduler import start_scheduler
        start_scheduler()
    yield
    if settings.ENABLE_SCHEDULER:
        from .jobs.scheduler import shutdown_scheduler
        shutdown_scheduler()


app = FastAPI(
    title=f"{brand.app_name()} API",
    version="0.1.0",
    description="Deterministic swing-trading platform API. Educational analysis, not advice.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


_RATE_LIMITED_PREFIXES = ("/api/auth", "/api/me/2fa")


@app.middleware("http")
async def correlation_and_ratelimit(request: Request, call_next):
    # request_id threads through event-log entries for tracing (blueprint/22)
    request.state.request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
    # per-IP rate limit on auth/sensitive paths (fails open on limiter error)
    if any(request.url.path.startswith(p) for p in _RATE_LIMITED_PREFIXES):
        ip = request.client.host if request.client else "unknown"
        try:
            if not allow(f"{ip}:{request.url.path}", settings.RATE_LIMIT_PER_MIN):
                return JSONResponse({"detail": "Too many requests"}, status_code=429)
        except Exception:
            pass
    response = await call_next(request)
    response.headers["x-request-id"] = request.state.request_id
    return response


for r in (health.router, platform.router, auth.router, me.router, picks.router, stocks.router,
          paper.router, cms.router, admin.router, metrics.router, notifications.router,
          referral.router, billing.router):
    app.include_router(r)


@app.get("/")
async def root():
    return {"service": brand.app_name(), "docs": "/docs", "health": "/api/health"}
