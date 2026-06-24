#!/usr/bin/env python3
"""Export the live OpenAPI schema + a ready-to-import Postman collection.

Run: python3 scripts/export-openapi.py   (from repo root, uses backend deps)
Outputs into api-docs/:
  - openapi.json                      (import directly into Postman, Insomnia, etc.)
  - swingai.postman_collection.json   (folders by tag, {{base_url}} + {{token}} vars)
  - swingai.postman_environment.json  (base_url + token)

The schema is generated from the FastAPI app WITHOUT booting it (no DB needed).
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
OUT = os.path.join(ROOT, "api-docs")
os.makedirs(OUT, exist_ok=True)

from app.main import app  # noqa: E402

spec = app.openapi()
with open(os.path.join(OUT, "openapi.json"), "w") as f:
    json.dump(spec, f, indent=2)

# --- build a Postman v2.1 collection grouped by tag ---
AUTH = {"type": "bearer", "bearer": [{"key": "token", "value": "{{token}}", "type": "string"}]}
folders: dict[str, dict] = {}

for path, methods in sorted(spec.get("paths", {}).items()):
    for method, op in methods.items():
        if method not in ("get", "post", "put", "delete", "patch"):
            continue
        tag = (op.get("tags") or ["default"])[0]
        folder = folders.setdefault(tag, {"name": tag, "item": []})
        seg = [p for p in path.split("/") if p]
        url = {"raw": "{{base_url}}" + path, "host": ["{{base_url}}"], "path": seg}
        req = {"method": method.upper(), "header": [], "url": url}
        if op.get("requestBody"):
            req["header"].append({"key": "Content-Type", "value": "application/json"})
            req["body"] = {"mode": "raw", "raw": "{\n  \n}"}
        # mark likely-protected routes to use bearer auth
        if path.startswith("/api/admin") or path in ("/api/auth/me", "/api/analytics") \
                or path.startswith("/api/paper-trade"):
            req["auth"] = AUTH
        folder["item"].append({"name": op.get("summary") or f"{method.upper()} {path}",
                               "request": req})

collection = {
    "info": {
        "name": "SwingAI API",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        "description": "SwingAI platform API. Login via POST /api/auth/login, copy access_token "
                       "into the {{token}} environment variable. Swagger UI: {{base_url}}/docs",
    },
    "item": list(folders.values()),
    "variable": [{"key": "base_url", "value": "http://localhost:9000"}],
}
with open(os.path.join(OUT, "swingai.postman_collection.json"), "w") as f:
    json.dump(collection, f, indent=2)

env = {
    "name": "SwingAI Local",
    "values": [
        {"key": "base_url", "value": "http://localhost:9000", "enabled": True},
        {"key": "token", "value": "", "enabled": True},
    ],
}
with open(os.path.join(OUT, "swingai.postman_environment.json"), "w") as f:
    json.dump(env, f, indent=2)

n_paths = len(spec.get("paths", {}))
print(f"Wrote api-docs/openapi.json ({n_paths} paths), Postman collection + environment.")
