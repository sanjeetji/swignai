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
| `scripts/swingai.sh start` | Start everything: DB + Redis (Docker) → backend → frontend. Prints all URLs. |
| `scripts/swingai.sh stop` | Stop frontend + backend + DB containers. **Data preserved** (volumes kept). |
| `scripts/swingai.sh restart` | `stop` then `start`. |
| `scripts/swingai.sh status` | Show containers, backend/frontend processes, and a ● / ○ port table. |
| `scripts/swingai.sh fresh` | **DESTRUCTIVE** — drop the DB volume, then start fresh (re-seeds). |
| `scripts/swingai.sh logs` | Tail backend + frontend logs together. |
| `scripts/swingai.sh test` | Run the backend test suite. |

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
| `scripts/backend.sh start` | Create venv + install deps (first run), then run uvicorn on :9000 (background). |
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
| `scripts/frontend.sh start` | `npm install` (first run), then `npm run dev` (both apps, background). |
| `scripts/frontend.sh stop` | Stop the dev servers + free ports 9001/9002. |
| `scripts/frontend.sh restart` | `stop` then `start`. |
| `scripts/frontend.sh install` | Install JS deps only (no run). |
| `scripts/frontend.sh status` | Is the frontend process alive? |
| `scripts/frontend.sh logs` | Tail `logs/frontend.log`. |

---

## 📜 `logs.sh` — tail logs

| Command | What it does |
|---|---|
| `scripts/logs.sh all` | Tail backend + frontend together (default). |
| `scripts/logs.sh backend` | Tail `logs/backend.log`. |
| `scripts/logs.sh frontend` | Tail `logs/frontend.log`. |
| `scripts/logs.sh db` | Follow Postgres container logs. |
| `scripts/logs.sh redis` | Follow Redis container logs. |

---

## 🧰 Utility scripts (not services)

| Script | Use |
|---|---|
| `python3 scripts/export-openapi.py` | Regenerate `api-docs/` (OpenAPI schema + Postman collection + env). |
| `scripts/rename-brand.sh OLD NEW [--apply]` | Rename the whole platform (e.g. `SwingAI → SwingWise`). See [`brand/BRAND.md`](../brand/BRAND.md). |

---

## Typical day

```bash
colima start                 # docker runtime
scripts/swingai.sh start     # bring up the whole platform
scripts/swingai.sh status    # check ports
scripts/logs.sh all          # watch logs
# ... work ...
scripts/swingai.sh stop      # done
```

**Runtime artifacts** (git-ignored): PIDs in `.run/`, logs in `logs/`.
