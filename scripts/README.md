# Scripts — Command Reference

Every control script for the SwingAI platform, with each sub-command and what it does.
All scripts source [`_common.sh`](./_common.sh) (the single source of truth for ports/paths).

**Ports (9000 series — clear of OmniMark's 3000/8000):**
| Service | Port |
|---|---|
| API (FastAPI) | **9000** → http://localhost:9000/docs |
| Dashboard (Next.js) | **9001** → http://localhost:9001 |
| Marketing (Next.js) | **9002** → http://localhost:9002 |
| Postgres (Docker) | **5434** |
| Redis (Docker) | **6380** |

Override any port inline, e.g. `BACKEND_PORT=9100 scripts/backend.sh start`.

> **Colima auto-start:** the `start` actions check the Docker daemon first and, if it's down,
> automatically run `colima start` and wait until it's ready before continuing — so you don't
> need to run `colima start` by hand. (No-op when Docker is already running. Requires Colima
> installed; otherwise you'll get a clear message to start Docker manually.)

---

## 🎛️ `swingai.sh` — master control (use this 90% of the time)

| Command | What it does |
|---|---|
| `scripts/swingai.sh start` | Start everything: DB + Redis (Docker) → backend → frontend (background). Ends with a **health report** + URLs. |
| `scripts/swingai.sh start --logs` | Same, but then **stays attached and streams logs** so you see crashes live. `Ctrl-C` stops watching; services keep running. (`-w` / `--watch` also work.) |
| `scripts/swingai.sh dev` | Alias for `start --logs`. |
| `scripts/swingai.sh stop` | Stop frontend + backend + DB containers. **Data preserved** (volumes kept). |
| `scripts/swingai.sh restart [--logs]` | `stop` then `start` (optionally attach to logs). |
| `scripts/swingai.sh status` / `health` | **Health probe**: ● / ○ for every port, the API `/api/health` response, and recent error lines from the logs. Safe to run anytime. |
| `scripts/swingai.sh fresh [--logs]` | **DESTRUCTIVE** — drop the DB volume, start fresh, create the first super admin (asks `y/n` first). Market data auto-fetches on first dashboard open. |
| `scripts/swingai.sh create-admin` | Create / promote a super admin (interactive, or `--email/--name/--password`). |
| `scripts/swingai.sh pipeline` | (Re)run the daily screener now to refresh market data / picks. |
| `scripts/swingai.sh logs [N]` | Tail backend + frontend (live follow; or pass `N` for the last N lines then exit). |
| `scripts/swingai.sh test` | Run the backend test suite. |

> **Crash visibility:** `start`/`fresh` launch services in the background and return — so a later
> crash won't show in your terminal. Use **`status`** (anytime) for a health snapshot, **`logs`** to
> tail, or **`start --logs` / `dev`** to watch live from the moment of launch. If a service fails to
> come up *during* start, the script now automatically prints the last ~30 lines of its log so you
> see the cause immediately.

---

## 🗄️ `db.sh` — database + Redis (Docker)

| Command | What it does |
|---|---|
| `scripts/db.sh start` | Start Postgres (:5434) + Redis (:6380), wait until healthy. |
| `scripts/db.sh stop` | Stop both containers (volumes/data kept). |
| `scripts/db.sh status` | `docker compose ps` for db + redis. |
| `scripts/db.sh wait` | Block until Postgres accepts connections. |
| `scripts/db.sh psql` | Open a `psql` shell inside the DB container. |
| `scripts/db.sh redis-cli` | Open a `redis-cli` shell inside the Redis container. |
| `scripts/db.sh reset` | **DESTRUCTIVE** — `docker compose down -v` (removes volumes). Confirms first. |

---

## 🐍 `backend.sh` — FastAPI API

| Command | What it does |
|---|---|
| `scripts/backend.sh start` | Create venv + install deps (first run), then run uvicorn on :9000 (background). If it fails to bind the port, it prints the last ~30 log lines so you see the crash. |
| `scripts/backend.sh stop` | Stop the uvicorn process. |
| `scripts/backend.sh restart` | `stop` then `start`. |
| `scripts/backend.sh status` | Is the backend process alive? |
| `scripts/backend.sh seed` | Create tables + seed (roles, theme presets, super admin, marketing). |
| `scripts/backend.sh test` | Run `pytest` in the backend venv. |
| `scripts/backend.sh logs` | Tail `logs/backend.log`. |

> Uses `DATABASE_URL` / `REDIS_URL` from `_common.sh` (points at the Docker Postgres/Redis).

---

## ⚛️ `frontend.sh` — Turborepo (marketing + dashboard)

| Command | What it does |
|---|---|
| `scripts/frontend.sh start` | `npm install` (first run), clears stale `.next`, then `npm run dev` (both apps, background). If an app fails to come up, it prints the last ~30 log lines. |
| `scripts/frontend.sh stop` | Stop the dev servers + free ports 9001/9002. |
| `scripts/frontend.sh restart` | `stop` then `start`. |
| `scripts/frontend.sh install` | Install JS deps only (no run). |
| `scripts/frontend.sh status` | Is the frontend process alive? |
| `scripts/frontend.sh logs` | Tail `logs/frontend.log`. |

---

## 📜 `logs.sh` — view logs

Pass an optional **line count** as a 2nd argument to get a **snapshot** (prints the last N lines
and exits — the prompt returns immediately) instead of a live follow.

| Command | What it does |
|---|---|
| `scripts/logs.sh all` | **Live follow** backend + frontend together (default). `Ctrl-C` to stop. |
| `scripts/logs.sh all 50` | Snapshot: last 50 lines of each, then exit. |
| `scripts/logs.sh backend [N]` | Follow `logs/backend.log` (or last N lines then exit). |
| `scripts/logs.sh frontend [N]` | Follow `logs/frontend.log` (or last N lines then exit). |
| `scripts/logs.sh db [N]` | Follow Postgres container logs (or last N then exit). |
| `scripts/logs.sh redis [N]` | Follow Redis container logs (or last N then exit). |

> **Follow vs snapshot:** a live follow (`tail -f`) *stays attached on purpose* — that's how you
> watch logs in real time; press `Ctrl-C` to return to the prompt. Add a number when you just want
> a quick peek without blocking.

---

## 🧰 Utility scripts (not services)

| Script | Use |
|---|---|
| `python3 scripts/export-openapi.py` | Regenerate `api-docs/` (OpenAPI schema + Postman collection + env). |
| `scripts/rename-brand.sh OLD NEW [--apply]` | Rename the whole platform (e.g. `SwingAI → SwingWise`). See [`brand/BRAND.md`](../brand/BRAND.md). |

---

## Typical day

```bash
scripts/swingai.sh start --logs   # bring up everything AND watch logs live (see crashes)
#   (Colima/Docker auto-starts if needed; Ctrl-C stops watching, services keep running)

# or, if you prefer the prompt back:
scripts/swingai.sh start          # background; ends with a health report
scripts/swingai.sh status         # health snapshot anytime (ports + /health + recent errors)
scripts/logs.sh all 80            # quick peek at the last 80 log lines (no blocking)
scripts/logs.sh all               # live follow when you want to watch

scripts/swingai.sh stop           # done (data preserved)
```

**First run / reset:**
```bash
scripts/swingai.sh fresh          # wipes DB → starts → asks to create the first super admin
#   then open the dashboard — it auto-fetches today's market data with a progress bar
scripts/swingai.sh pipeline       # (optional) force a market-data refresh from the CLI
```

**Did something crash?**
```bash
scripts/swingai.sh status         # is anything ○ DOWN? shows recent error lines too
scripts/logs.sh backend 100       # last 100 backend lines
scripts/swingai.sh restart        # bounce everything
```

**Runtime artifacts** (git-ignored): PIDs in `.run/`, logs in `logs/`.
