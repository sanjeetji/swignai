# API Docs — Swagger & Postman

Interactive and importable documentation for the SwingAI backend API.

## Live interactive docs (Swagger / ReDoc)

With the backend running (`scripts/backend.sh start`):

| Tool | URL |
|---|---|
| **Swagger UI** (try-it-out) | http://localhost:9000/docs |
| **ReDoc** (clean reference) | http://localhost:9000/redoc |
| **Raw OpenAPI schema** | http://localhost:9000/openapi.json |

## Files in this folder (regenerate with `python3 scripts/export-openapi.py`)

| File | Use |
|---|---|
| `openapi.json` | OpenAPI 3 schema. **Import directly into Postman/Insomnia** (Import → File). |
| `swingai.postman_collection.json` | Ready-made Postman collection — requests grouped by tag, with `{{base_url}}` + `{{token}}`. |
| `swingai.postman_environment.json` | Postman environment (`base_url=http://localhost:9000`, empty `token`). |

## Quick start in Postman

1. **Import** `swingai.postman_collection.json` **and** `swingai.postman_environment.json`.
2. Select the **SwingAI Local** environment (top-right).
3. Run **auth → `POST /api/auth/login`** with body:
   ```json
   { "email": "admin@swingai.in", "password": "admin12345" }
   ```
4. Copy `access_token` from the response into the environment's **`token`** variable.
5. Protected routes (admin, paper-trade, analytics, /auth/me) now send `Authorization: Bearer {{token}}` automatically.

## Endpoint groups (folders)

- **health / platform** — health, brand, public appearance (theme presets, locales)
- **auth** — register, login, me
- **picks** — `GET /api/daily-picks` (deterministic quant engine output)
- **paper** — buy / close / portfolio (server-side risk guards)
- **metrics** — `GET /api/track-record`, `GET /api/analytics` (honest, R-multiples)
- **cms** — public page/testimonials/stats + admin pages
- **admin** — users + block/unblock, appearance, integrations vault (+test), event logs + audit, metrics

> Keep this folder current: re-run `python3 scripts/export-openapi.py` after adding/changing endpoints.
