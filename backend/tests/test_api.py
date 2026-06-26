"""API integration tests (blueprint/11) — auth lifecycle, billing plans, free trial +
tier gating, and Razorpay signature logic. Runs against an isolated temp SQLite DB so it
needs no Postgres/network. The app lifespan seeds roles/plans on startup.
"""
import os
import pathlib
import tempfile

# Point at a throwaway SQLite DB BEFORE importing the app (settings read env at import).
_DB = pathlib.Path(tempfile.gettempdir()) / "swingai_test.db"
if _DB.exists():
    _DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_DB}"
os.environ["ENABLE_SCHEDULER"] = "false"
os.environ["LLM_PROVIDER"] = "template"   # no external LLM calls in tests

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:   # runs lifespan → init_db + seed
        yield c


def _register(client, email, pw="secret12"):
    r = client.post("/api/auth/register", json={"email": email, "password": pw, "name": "T"})
    assert r.status_code == 200, r.text
    return r.json()


def test_register_login_me(client):
    toks = _register(client, "a@example.com")
    assert toks["access_token"] and toks["refresh_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {toks['access_token']}"})
    assert me.status_code == 200 and me.json()["email"] == "a@example.com"


def test_refresh_and_logout(client):
    toks = _register(client, "b@example.com")
    nr = client.post("/api/auth/refresh", json={"refresh_token": toks["refresh_token"]})
    assert nr.status_code == 200
    acc = nr.json()["access_token"]
    h = {"Authorization": f"Bearer {acc}"}
    assert client.get("/api/auth/me", headers=h).status_code == 200
    client.post("/api/auth/logout", headers=h)
    assert client.get("/api/auth/me", headers=h).status_code == 401   # session revoked


def test_refresh_token_cannot_access(client):
    toks = _register(client, "d@example.com")
    h = {"Authorization": f"Bearer {toks['refresh_token']}"}   # using refresh as access
    assert client.get("/api/auth/me", headers=h).status_code == 401


def test_plans_seeded(client):
    plans = client.get("/api/billing/plans").json()["plans"]
    slugs = {p["id"] for p in plans}
    assert {"trial", "pro", "premium"} <= slugs
    trial = next(p for p in plans if p["id"] == "trial")
    assert trial["trial_days"] > 0 and trial["price_inr"] == 0


def test_trial_and_tier_gating(client):
    toks = _register(client, "c@example.com")
    h = {"Authorization": f"Bearer {toks['access_token']}"}
    # free user: equity curve is Pro+ → 402
    assert client.get("/api/analytics/equity", headers=h).status_code == 402
    # start trial → full access
    r = client.post("/api/billing/start-trial", headers=h)
    assert r.status_code == 200 and r.json()["tier"] == "trial"
    assert client.get("/api/analytics/equity", headers=h).status_code == 200
    # trial only once
    assert client.post("/api/billing/start-trial", headers=h).status_code == 400


def test_razorpay_signature():
    from app.services import razorpay
    sig = razorpay._sign("order_x|pay_y", "topsecret")
    assert razorpay.verify_payment("order_x", "pay_y", sig, "topsecret")
    assert not razorpay.verify_payment("order_x", "pay_y", "tampered", "topsecret")
