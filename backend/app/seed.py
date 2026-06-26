"""Idempotent seed — roles, permissions, theme presets, settings, super admin, marketing.

Everything the platform needs to work on first boot, editable thereafter by the
Super Admin (blueprint/16,19,21). Seeds only when tables are empty (won't clobber edits).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select

from .core.db import SessionLocal
from .core.security import hash_password
from .models.billing import Plan
from .models.cms import CmsPage, CmsSection, StatMetric, Testimonial
from .models.platform import FeatureFlag, Integration, PlatformSetting, ThemePreset
from .models.user import Permission, Role, RolePermission, User, UserRole

PERMISSIONS = [
    "users.read", "users.block", "users.impersonate", "roles.manage",
    "integrations.manage", "settings.appearance", "feature_flags.manage",
    "content.manage", "events.read", "analytics.view", "picks.override",
]

ROLE_PERMS = {
    "super_admin": PERMISSIONS,                          # everything
    "admin": ["users.read", "users.block", "content.manage", "events.read",
              "analytics.view", "settings.appearance"],
    "support": ["users.read", "events.read"],
    "user": [],
}

PRESETS = [
    ("default", "Default Blue",
     {"primary": "#2563eb", "background": "#ffffff", "foreground": "#0f172a"},
     {"primary": "#3b82f6", "background": "#0b1120", "foreground": "#e2e8f0"}),
    ("emerald", "Emerald",
     {"primary": "#059669", "background": "#ffffff", "foreground": "#0f172a"},
     {"primary": "#10b981", "background": "#0b1120", "foreground": "#e2e8f0"}),
    ("violet", "Violet",
     {"primary": "#7c3aed", "background": "#ffffff", "foreground": "#0f172a"},
     {"primary": "#8b5cf6", "background": "#0b1120", "foreground": "#e2e8f0"}),
    ("amber", "Amber",
     {"primary": "#d97706", "background": "#ffffff", "foreground": "#0f172a"},
     {"primary": "#f59e0b", "background": "#0b1120", "foreground": "#e2e8f0"}),
]


async def _empty(db, model) -> bool:
    return (await db.execute(select(func.count()).select_from(model))).scalar_one() == 0


async def seed_if_empty() -> None:
    async with SessionLocal() as db:
        # --- permissions + roles ---
        if await _empty(db, Permission):
            perms = {key: Permission(key=key, description=key) for key in PERMISSIONS}
            for p in perms.values():
                db.add(p)
            await db.flush()
            for rname, keys in ROLE_PERMS.items():
                role = Role(name=rname, description=f"{rname} role")
                db.add(role)
                await db.flush()
                for k in keys:
                    db.add(RolePermission(role_id=role.id, permission_id=perms[k].id))
            await db.flush()

        # --- super admin user (dev) ---
        if await _empty(db, User):
            admin = User(email="admin@swingai.in", name="Platform Owner",
                         password_hash=hash_password("admin12345"), is_email_verified=True)
            db.add(admin)
            await db.flush()
            sa = (await db.execute(select(Role).where(Role.name == "super_admin"))).scalar_one()
            db.add(UserRole(user_id=admin.id, role_id=sa.id))

        # --- platform settings + theme presets ---
        if await _empty(db, PlatformSetting):
            db.add(PlatformSetting(
                default_theme_mode="system", default_preset="default", default_font="inter",
                default_locale="en", enabled_presets=[p[0] for p in PRESETS],
                enabled_fonts=["inter", "manrope", "jakarta"], enabled_locales=["en", "hi"],
            ))
        if await _empty(db, ThemePreset):
            for i, (name, label, light, dark) in enumerate(PRESETS):
                db.add(ThemePreset(name=name, label=label, tokens_light=light, tokens_dark=dark,
                                   sort_order=i))

        # --- subscription plans (admin-editable; shown on marketing + dashboard) ---
        if await _empty(db, Plan):
            db.add(Plan(slug="pro", name="Pro", price_inr=499, sort_order=1, is_featured=False,
                        features=["Daily picks + full scanner", "Paper trading + journal",
                                  "Personal analytics & alerts"]))
            db.add(Plan(slug="premium", name="Premium", price_inr=999, sort_order=2, is_featured=True,
                        features=["Everything in Pro", "Priority data refresh",
                                  "Early access to new features"]))

        # --- feature flags (admin-togglable; on by default for core Layers) ---
        if await _empty(db, FeatureFlag):
            for key, desc in [
                ("daily_picks", "Show the daily screener picks (Layer 3)"),
                ("paper_trading", "Paper-trade engine + portfolio (Layer 1/2)"),
                ("trade_journal", "Trade journal + post-trade review (Layer 2)"),
                ("ai_explanations", "Hinglish LLM explanations on picks (Layer 3)"),
            ]:
                db.add(FeatureFlag(key=key, enabled=True, targeting={}, description=desc))

        # --- integration slots (admin pastes keys in the Integrations tab; vault overrides .env) ---
        # Idempotent per-provider: add any missing slot without touching configured ones.
        slots = [
            ("llm", "groq"), ("llm", "openrouter"), ("llm", "together"),
            ("llm", "openai"), ("llm", "gemini"),
            ("payments", "razorpay"),
            ("data", "angelone"),
        ]
        have = set((await db.execute(select(Integration.provider))).scalars().all())
        for category, provider in slots:
            if provider not in have:
                db.add(Integration(category=category, provider=provider, enabled=False, role="primary", config={}))

        # --- marketing content (seed, then admin-editable) ---
        if await _empty(db, CmsPage):
            home = CmsPage(slug="home", title="SwingAI — Disciplined Swing Trading",
                           type="landing", status="published", locale="en", nav_visible=True,
                           seo={"title": "SwingAI — Disciplined swing trading, proven honestly",
                                "description": "AI-assisted NSE swing-trade analysis with enforced risk "
                                               "management and a transparent track record. Educational, not advice."})
            db.add(home)
            await db.flush()
            blocks = [
                ("hero", {"heading": "Trade swings with discipline, not guesswork.",
                          "subheading": "Risk-managed NSE setups, a transparent track record, and paper "
                                        "trading to prove it — before you risk real money.",
                          "cta": {"label": "Start free", "href": "/signup"}}),
                ("stats", {"source": "stats_metrics"}),
                ("features", {"items": [
                    {"title": "Enforced risk engine", "body": "Position sizing, stops and portfolio heat — automatic."},
                    {"title": "Honest track record", "body": "Every pick, net of costs, in R-multiples. Scratches counted."},
                    {"title": "Hinglish explanations", "body": "Plain-language reasoning for every setup."},
                ]}),
                ("testimonials", {"source": "testimonials"}),
                ("cta", {"heading": "Prove it on paper first.", "cta": {"label": "Create account", "href": "/signup"}}),
            ]
            for i, (bt, content) in enumerate(blocks):
                db.add(CmsSection(page_id=home.id, block_type=bt, sort_order=i, content=content))

        if await _empty(db, StatMetric):
            for i, (k, label, val, suf, live) in enumerate([
                ("regime", "Market regime gate", "Bull/Bear", "", True),
                ("rr", "Minimum reward:risk", "1:2", "", False),
                ("risk", "Risk per trade", "1", "%", False),
            ]):
                db.add(StatMetric(key=k, label=label, value=val, suffix=suf, is_live=live, sort_order=i))

        if await _empty(db, Testimonial):
            db.add(Testimonial(author_name="Beta tester", role="Swing trader", company="",
                               quote="The risk engine stopped me oversizing. First time I followed a plan.",
                               rating=5, is_featured=True, sort_order=0))

        await db.commit()
