# 06 — Database Schema

> 🧭 **Status:** 📝 Spec · **Tier:** 🏆 Best-in-class (design) → **Target: 🏆 Best-in-class** · **Phase 1** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** PostgreSQL (via Supabase) is the system of record for users, AI picks, paper trades, analytics, the public track record, and (later) subscriptions. This doc defines the core tables for Phase 1, plus the columns/tables that later phases add. Migrations via Alembic. Auth users come from Supabase Auth; our `users` table extends them.

---

## 1. Conventions

- **Primary keys:** UUID (`id`).
- **Timestamps:** `created_at`, `updated_at` (UTC in DB; render IST in app).
- **Money:** integer paise or `numeric(14,2)` INR — be consistent; avoid floats for money.
- **Enums:** Postgres enums or check-constrained text.
- **Idempotency:** daily-generated rows use unique constraints so cron re-runs upsert, not duplicate.
- **Auth link:** `users.id` = Supabase `auth.users.id` (1:1).

---

## 2. Core tables (Phase 1)

### `users` (extends Supabase auth)
```
id                UUID PK   -- = auth.users.id
email             text
name              text
phone             text
created_at        timestamptz
capital_amount    numeric(14,2)        -- virtual capital, default 100000
risk_appetite     text                 -- low / moderate / high
risk_pct          numeric(4,2)         -- per-trade risk %, default 1.00
preferred_sectors text[]               -- optional
subscription_tier text                 -- free / pro / premium (default free)
subscription_expiry timestamptz
is_admin          boolean default false
```

### `ai_picks` — one row per stock per day (the signal record)
```
id                  UUID PK
stock_symbol        text
sector              text
date_generated      date
score               numeric(5,2)
score_breakdown     jsonb        -- {rs:22, trend:18, setup:16, volume:11, momentum:9, rr:7}
regime              text         -- bull / neutral / bear
-- trade plan
entry_price         numeric(12,2)
stop_loss           numeric(12,2)
target_1            numeric(12,2)
target_2            numeric(12,2)
rr_ratio            numeric(5,2)
position_size_suggested numeric(14,2)
confidence          numeric(5,2)
-- indicators snapshot (for SEO page + audit)
rsi                 numeric(6,2)
macd                numeric(8,4)
ema20               numeric(12,2)
ema50               numeric(12,2)
ema200              numeric(12,2)
atr_pct             numeric(6,3)
volume_ratio        numeric(6,2)
rel_strength        numeric(6,2)
pattern             text
-- narration
explanation_hinglish text
-- outcome (resolved by nightly job)
actual_result       text         -- hit_target / hit_stoploss / scratch / still_open
actual_return_pct   numeric(7,3)
actual_r_multiple   numeric(6,3)
closed_at           timestamptz
created_at          timestamptz
UNIQUE (stock_symbol, date_generated)   -- idempotent upsert
```

### `paper_trades` — user virtual trades
```
id                  UUID PK
user_id             UUID FK -> users
ai_pick_id          UUID FK -> ai_picks (nullable; user may trade off-pick)
stock_symbol        text
entry_price         numeric(12,2)
entry_date          timestamptz
quantity            integer
position_size_inr   numeric(14,2)
stop_loss_set       numeric(12,2)
target_set          numeric(12,2)
sl_moved_to_breakeven boolean default false
exit_price          numeric(12,2)
exit_date           timestamptz
pnl_inr             numeric(14,2)
pnl_percent         numeric(7,3)
r_multiple          numeric(6,3)
status              text   -- open / closed_profit / closed_loss / scratch
-- journal (Layer 2 — process)
entry_reason        text
exit_reason         text
created_at          timestamptz
```

### `user_analytics` — recomputed nightly (personal expectancy dashboard)
```
user_id             UUID PK FK -> users
total_trades        integer
winning_trades      integer
win_rate_pct        numeric(5,2)     -- wins / (wins+losses+scratches)
expectancy_r        numeric(6,3)     -- THE headline metric
profit_factor       numeric(6,2)
total_pnl_inr       numeric(14,2)
avg_holding_days    numeric(5,1)
best_sector         text
rr_achieved_avg     numeric(5,2)
discipline_score    numeric(5,2)     -- followed-the-plan score (see §4)
last_updated        timestamptz
```

### `regime_log` — daily market state (public record)
```
date                date PK
nifty_close         numeric(12,2)
nifty_ema20         numeric(12,2)
regime              text       -- bull / neutral / bear
picks_generated     integer
created_at          timestamptz
```

### `backtest_runs` — cached results for the public `/backtest` tool
```
id                  UUID PK
params              jsonb       -- strategy params + date range
date_range          daterange
expectancy_r        numeric(6,3)
win_rate            numeric(5,2)
profit_factor       numeric(6,2)
max_drawdown        numeric(6,2)
trade_log           jsonb       -- full auditable log
computed_at         timestamptz
```

---

## 3. Tables added in later phases

### Phase 2 — alerts & referrals
```
alerts            -- id, user_id, paper_trade_id, type(target/sl), channel(whatsapp/sms), sent_at, status
referrals         -- id, referrer_user_id, referred_user_id, status, reward_status, created_at
```

### Phase 3 — subscriptions & payments (Razorpay)
```
subscriptions     -- id, user_id, plan(pro/premium), status, started_at, current_period_end,
                  --   razorpay_subscription_id
payments          -- id, user_id, amount_inr, status, razorpay_payment_id, created_at
```

### Phase 2/3 — content (SEO)
```
blog_posts        -- id, slug, title, body_md, sector, generated_by, published_at, meta(jsonb)
stock_meta        -- symbol PK, name, sector, isin, last_analysis_at  (for /stocks/[symbol] SEO)
```

---

## 2b. Platform-control tables (admin, RBAC, theming, i18n, sessions, secrets — docs 14–20)

> Phase 1 foundational. All admin/personalization/security features read from these — **no hardcoded settings, strings, colors, or secrets.**

### RBAC (doc 19)
```
roles             -- id, name (super_admin/admin/support/user), description, is_system
permissions       -- id, key (e.g. users.block, integrations.manage), description
role_permissions  -- role_id, permission_id
user_roles        -- user_id, role_id, granted_by, granted_at
```

### Personalization — theming & i18n (docs 14–16)
```
platform_settings -- singleton/keyed: default_theme_mode(light/dark/system),
                  --   default_preset, default_font, default_locale,
                  --   locked_axes(jsonb: which of mode/preset/font/locale are admin-forced),
                  --   enabled_presets[], enabled_fonts[], enabled_locales[],
                  --   maintenance_mode(bool), maintenance_message, new_user_defaults(jsonb), updated_by
theme_presets     -- id, name, tokens_light(jsonb), tokens_dark(jsonb), is_enabled, sort_order
feature_flags     -- id, key, enabled(bool), targeting(jsonb: tier/role/cohort), updated_by, updated_at
user_preferences  -- user_id PK, theme_mode, theme_preset, font, locale  (NULL = inherit default)
```

### Integrations / secrets vault (doc 17)
```
integrations      -- id, category(llm/data/payments/alerts/infra), provider(gemini/angelone/razorpay…),
                  --   enabled(bool), role(primary/fallback), config(jsonb: non-secret, e.g. default model),
                  --   secret_ciphertext(bytea), secret_meta(jsonb: masked hint, key id),
                  --   last_tested_at, last_status, updated_by, updated_at
                  --   (secret stored ENCRYPTED; master key in env/KMS, never in DB — doc 17/19)
```

### Sessions, devices, blocks, audit (doc 18)
```
user_sessions     -- id, user_id, supabase_session_ref, ip, geo(jsonb: city/region/country/isp),
                  --   device, browser, os, created_at, last_active_at, expires_at, revoked_at, is_active
login_history     -- id, user_id, ip, geo(jsonb), device, success(bool), reason, created_at
user_blocks       -- id, user_id, blocked_by, reason, created_at, lifted_by, lifted_at, is_active
event_logs        -- UNIFIED event stream (doc 22) — APPEND-ONLY:
                  --   event_type(dotted), category(security/admin/integration/system/product/data/billing),
                  --   level(debug/info/warning/error/critical), actor_user_id(null=SYSTEM), actor_role, source,
                  --   resource, resource_id, before(jsonb), after(jsonb), payload(jsonb),
                  --   request_id(correlation), session_id, ip, location, user_agent, device,
                  --   hash_prev(optional tamper-evidence), created_at
                  --   (the "audit_logs" view = category in (admin,security); secrets' VALUES never stored)
data_subject_requests -- DPDP/GDPR (doc 22): requested_email, request_type, status, regulation,
                  --   requester_ip, verified_at, due_at(statutory deadline)
notifications     -- id, user_id, type, channel(inapp/email/whatsapp/sms), payload(jsonb),
                  --   locale, read_at, sent_at, status
```

### Business metrics snapshot (doc 20)
```
platform_metrics  -- date, mrr, arr, arpu, ltv, active_dau, active_wau, active_mau,
                  --   signups, paid_conversions, churn_rate, new_mrr, churned_mrr, computed_at
                  -- (pre-computed nightly so admin dashboards load instantly)
```

### Marketing CMS (doc 21) — dynamic, seeded, versioned
```
cms_pages          -- slug, title, type(landing/feature/pricing/about/custom), status(draft/published),
                   --   locale, seo_meta_id, published_version_id, nav_visible, sort_order, updated_by
cms_sections       -- page_id, block_type(hero/features/testimonials/stats/faq/cta/pricing/richtext/media),
                   --   sort_order, content(jsonb typed per block_type), is_enabled, locale
content_categories -- slug, name, description, parent_id, sort_order, seo_meta_id   (dynamic)
content_items      -- category_id, slug, title, body(jsonb), media, status, seo_meta_id, locale
testimonials       -- author_name, role, company, avatar_media_id, quote, rating, is_featured, sort_order, locale
stats_metrics      -- key, label, value, suffix, source, is_live(bool→real backend number), sort_order, locale
faqs               -- category, question, answer, sort_order, locale
navigation_menus   -- location(header/footer), items(jsonb), locale
media_assets       -- url, type, alt_text, width, height, uploaded_by
seo_meta           -- owner_type/owner_id, title, description, canonical, og(jsonb), twitter(jsonb),
                   --   json_ld(jsonb), robots, keywords, hreflang(jsonb)
content_versions   -- owner_type/owner_id, snapshot(jsonb), version_no, created_by, created_at, note
                   --   (draft/publish history + rollback for ANY editable content)
```
All marketing content is **DB-driven, locale-aware, seeded on first boot, and editable by Super Admin** — rendered server-side (ISR) for SEO. See doc 21.

### Future (doc 13)
```
news_sentiment    -- symbol, date, sentiment_score, source, headline   (sentiment AI)
watchlists        -- user-defined symbol lists
leaderboard_stats -- anonymized paper-trading rankings (community)
fno_strategies    -- risk-defined option strategy records (Phase 4)
```

---

## 4. Key derived logic (where it lives)

- **`win_rate_pct` MUST be `wins / (wins + losses + scratches)`** — scratches in the denominator, no massaging (doc 00 non-negotiable #2). Enforced in the nightly `recompute_analytics` job (doc 07) and verified by tests (doc 11).
- **`discipline_score`** — measures *did the user follow the plan*: used the suggested stop? sized within risk? didn't exit a winner before T1 without reason? This is the Layer-2 retention metric (doc 00) and feeds the post-trade review.
- **`expectancy_r`** is the headline everywhere it's shown — never win rate alone.

---

## 5. Indexing & integrity (essentials)

- `ai_picks (date_generated)`, `ai_picks (stock_symbol, date_generated)` unique.
- `paper_trades (user_id, status)` for open-position lookups.
- `regime_log (date)` for the public record timeline.
- FK constraints with sensible `on delete` (e.g. user deletion cascades their paper trades/analytics per data-retention policy).
- Supabase **Row Level Security**: users can read/write only their own `paper_trades`/`user_analytics`; `ai_picks`/`regime_log`/`backtest_runs` are world-readable (public SEO/track-record); `admin` bypass for the admin panel.

---

*Next: [`07-backend-api-cron.md`](./07-backend-api-cron.md) — the FastAPI endpoints, cron jobs, and error handling that operate on this schema.*
