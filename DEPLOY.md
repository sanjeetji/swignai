# Deploying SwingAI

The platform is a Turbo monorepo: a **FastAPI** backend + **two Next.js** apps (marketing, dashboard).
Recommended: **backend on Render** (Postgres + Redis included), **frontends on Vercel**.
CI (`.github/workflows/ci.yml`) runs backend tests + frontend typecheck on every push.

---

## 1. Backend → Render (one click via blueprint)

1. Push this repo to GitHub.
2. Render → **New → Blueprint** → pick the repo. It reads `render.yaml` and creates:
   the API (Docker, from `backend/Dockerfile`), a Postgres DB, and Redis. `DATABASE_URL`,
   `REDIS_URL`, `JWT_SECRET`, `SECRET_VAULT_KEY` are wired/generated automatically.
3. In the API service → **Environment**, fill the `sync:false` secrets:
   `ANGELONE_*`, `GROQ_API_KEY` (or other LLM keys), `RAZORPAY_KEY_ID/SECRET/WEBHOOK_SECRET`,
   `SENTRY_DSN` (optional), and `CORS_ORIGINS` = your Vercel URLs (comma-separated).
4. Deploy. Tables + factory seed (roles, theme presets, plans incl. Free Trial, integration slots)
   are created automatically on first boot via the app lifespan.

> `ENABLE_SCHEDULER=true` runs the daily cron jobs inside the web process (fine for one instance).
> For scale, split them into a separate Render **worker** running the same image.

**Railway / Fly** work too — point them at `backend/Dockerfile`, set the same env vars, and attach
managed Postgres + Redis.

### Create the first super admin (no demo admin is seeded)
Open the API service **Shell** in Render (or run locally against the prod `DATABASE_URL`) and run:
```bash
python -m app.admin_setup --email you@domain.com --name "Your Name" --password "a-strong-password"
# or interactively:
python -m app.admin_setup
```
Locally during development this is just: `scripts/swingai.sh create-admin` (or `fresh` to wipe + bootstrap).

---

## 2. Frontends → Vercel (two projects)

Create **two** Vercel projects from the same repo (monorepo root):

| Project | Root directory | Env vars |
|---|---|---|
| marketing | `apps/marketing` | `NEXT_PUBLIC_API_BASE` = API URL · `NEXT_PUBLIC_DASHBOARD_URL` = dashboard URL · `NEXT_PUBLIC_SITE_URL` = this site's URL · `REVALIDATE_TOKEN` |
| dashboard | `apps/dashboard` | `NEXT_PUBLIC_API_BASE` = API URL · `NEXT_PUBLIC_DASHBOARD_URL` = this site's URL |

Build command `npm run build`, install `npm install` (Vercel auto-detects Turbo/Next).
After deploy, set the backend's `CORS_ORIGINS` to both Vercel URLs and the API's
`REVALIDATE_URL` to `https://<marketing-url>/api/revalidate` (matching `REVALIDATE_TOKEN`).

---

## 3. Razorpay webhook
Razorpay dashboard → **Settings → Webhooks** → add `https://<api-url>/api/billing/webhook`,
set a secret, and put the same value in `RAZORPAY_WEBHOOK_SECRET`. Use **test** keys until live KYC.

---

## 4. Database alternative — Supabase
Prefer Supabase Postgres? Create a project, take its `postgresql+asyncpg://…` connection string,
and set it as `DATABASE_URL` on the API (skip the Render database in `render.yaml`).

---

## Checklist before public launch
- [ ] Replace placeholder legal contacts in `/privacy` and `/terms`; get a **SEBI + DPDP lawyer** sign-off.
- [ ] Set strong `JWT_SECRET` / `SECRET_VAULT_KEY` (Render generates these).
- [ ] Switch Razorpay to **live** keys after KYC.
- [ ] Point a custom domain at the Vercel apps; update `CORS_ORIGINS` + `NEXT_PUBLIC_*`.
- [ ] Schedule `scripts/backup.sh` (or Render/Supabase managed backups).
