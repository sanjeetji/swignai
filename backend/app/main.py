"""FastAPI app — the SwingAI platform API (blueprint/07).

Boots with zero external infra in dev (async SQLite, no Redis). Production points
DATABASE_URL at Postgres (Supabase) and runs Alembic migrations instead of init_db.
"""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from . import brand
from .core.config import settings
from .core.db import init_db
from .routers import admin, auth, cms, health, metrics, paper, picks, platform


@asynccontextmanager
async def lifespan(app: FastAPI):
    # dev convenience: create tables + seed if empty. prod uses Alembic + seed script.
    await init_db()
    from .seed import seed_if_empty
    await seed_if_empty()
    yield


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


@app.middleware("http")
async def correlation_id(request: Request, call_next):
    # request_id threads through event-log entries for tracing (blueprint/22)
    request.state.request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
    response = await call_next(request)
    response.headers["x-request-id"] = request.state.request_id
    return response


for r in (health.router, platform.router, auth.router, picks.router, paper.router,
          cms.router, admin.router, metrics.router):
    app.include_router(r)


@app.get("/")
async def root():
    return {"service": brand.app_name(), "docs": "/docs", "health": "/api/health"}
