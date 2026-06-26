"""Idempotent seed — roles, permissions, theme presets, settings, super admin, marketing.

Everything the platform needs to work on first boot, editable thereafter by the
Super Admin (blueprint/16,19,21). Seeds only when tables are empty (won't clobber edits).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select

from .core.db import SessionLocal
from .models.billing import Plan
from .models.cms import CmsPage, CmsSection, Faq, StatMetric, Testimonial
from .models.platform import FeatureFlag, Integration, PlatformSetting, ThemePreset
from .models.user import Permission, Role, RolePermission

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

        # NOTE: no demo super-admin is seeded. Create the first one interactively:
        #   scripts/swingai.sh fresh   (or)   scripts/swingai.sh create-admin

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

        # --- subscription plans (factory defaults; fully admin-editable afterwards) ---
        if await _empty(db, Plan):
            db.add(Plan(slug="trial", name="Free Trial", price_inr=0, trial_days=30, sort_order=0,
                        is_featured=False,
                        features=["Full access for 30 days", "No card required",
                                  "Daily picks + scanner + paper trading"]))
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
            ("data", "angelone"), ("data", "dhan"),
            ("alerts", "smtp"), ("alerts", "twilio"),
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
                    {"title": "Enforced risk engine", "body": "Position sizing, stops and portfolio heat — automatic, not optional."},
                    {"title": "NSE scanner", "body": "Rank the universe by a deterministic quant score, relative strength and volume."},
                    {"title": "Honest track record", "body": "Every pick, net of costs, in R-multiples. Scratches counted, nothing hidden."},
                    {"title": "Paper trading + journal", "body": "Place trades at real prices, log your reasons, review your discipline."},
                    {"title": "Hinglish explanations", "body": "Plain-language reasoning for every setup — analysis, never a buy/sell command."},
                    {"title": "Personal analytics", "body": "Your expectancy, win rate, profit factor and equity curve over time."},
                ]}),
                ("testimonials", {"source": "testimonials"}),
                ("faq", {"source": "faqs"}),
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
            for i, (author, role, quote) in enumerate([
                ("Rahul M.", "Swing trader",
                 "The risk engine stopped me oversizing. First time I actually followed a plan instead of my gut."),
                ("Priya S.", "Part-time trader",
                 "The journal review showed me I was exiting winners early. Fixing that changed my expectancy."),
                ("Anand K.", "Beta tester",
                 "Honest track record in R-multiples, not vanity win-rate. That's why I trust the picks as analysis."),
            ]):
                db.add(Testimonial(author_name=author, role=role, company="", quote=quote,
                                   rating=5, is_featured=(i == 0), sort_order=i))

        if await _empty(db, Faq):
            for i, (q, a) in enumerate([
                ("Is this investment advice?",
                 "No. SwingAI provides deterministic technical analysis and educational tools — not advice, "
                 "recommendations, or solicitations. We're not a SEBI-registered Research Analyst or Adviser."),
                ("Are the picks AI or a black box?",
                 "Neither. The score is fixed mathematics — EMA/RSI/MACD/ATR/ADX, relative strength and volume "
                 "through a weighted formula. The only AI is the optional Hinglish explanation text."),
                ("Do you execute real trades?",
                 "No. Trading on SwingAI is paper (simulated) with real prices, so you can prove a process before "
                 "risking real money. We never handle your funds."),
                ("Is the data real?",
                 "Yes — live NSE prices via Angel One SmartAPI. The track record is net of costs, in R-multiples, "
                 "counting wins, losses and scratches."),
                ("How much does it cost?",
                 "Start free, no card. A free trial unlocks everything for a limited time; paid plans are shown on "
                 "the Pricing page and are fully managed by us."),
            ]):
                db.add(Faq(question=q, answer=a, sort_order=i, locale="en"))

        await db.commit()
