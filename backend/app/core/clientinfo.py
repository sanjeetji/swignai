"""Client introspection — IP, geo (city/region/country/ISP), device/browser/OS (blueprint/18).

Geo via ip-api.com (free, no key) gated behind GEOIP_ENABLED; private/loopback IPs and
any lookup error degrade gracefully to {} (never block a login on geo). Results cached in
Redis. UA parsing is a lightweight heuristic — no heavy dependency.
"""
from __future__ import annotations

import ipaddress
import json

from fastapi import Request

from .config import settings
from .redis import cache_get, cache_set


def client_ip(req: Request) -> str | None:
    """Real client IP — honor the first hop of X-Forwarded-For (set by our proxy/CDN)."""
    xff = req.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return req.client.host if req.client else None


def _is_public(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_global
    except ValueError:
        return False


def parse_user_agent(ua: str | None) -> dict:
    """Heuristic UA → {device, browser, os}. Good enough for a sessions list label."""
    ua = ua or ""
    u = ua.lower()
    if "windows" in u:
        os_ = "Windows"
    elif "iphone" in u or "ipad" in u or " ios" in u:
        os_ = "iOS"
    elif "mac os" in u or "macintosh" in u:
        os_ = "macOS"
    elif "android" in u:
        os_ = "Android"
    elif "linux" in u:
        os_ = "Linux"
    else:
        os_ = None
    # order matters: Edge/Opera UAs also contain "chrome"/"safari"
    if "edg/" in u or "edge" in u:
        br = "Edge"
    elif "opr/" in u or "opera" in u:
        br = "Opera"
    elif "chrome" in u and "chromium" not in u:
        br = "Chrome"
    elif "firefox" in u:
        br = "Firefox"
    elif "safari" in u:
        br = "Safari"
    else:
        br = None
    if "ipad" in u or "tablet" in u:
        dev = "Tablet"
    elif "mobile" in u or "iphone" in u or "android" in u:
        dev = "Mobile"
    elif ua:
        dev = "Desktop"
    else:
        dev = None
    return {"device": dev, "browser": br, "os": os_}


async def geo_lookup(ip: str | None) -> dict:
    """IP → {city, region, country, isp}. Cached 7d; {} for private/loopback or when disabled."""
    if not ip or not settings.GEOIP_ENABLED or not _is_public(ip):
        return {}
    cache_key = f"geo:{ip}"
    cached = await cache_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except (ValueError, TypeError):
            return {}
    geo: dict = {}
    try:
        import requests
        r = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,country,regionName,city,isp"}, timeout=4,
        )
        d = r.json()
        if d.get("status") == "success":
            geo = {"city": d.get("city"), "region": d.get("regionName"),
                   "country": d.get("country"), "isp": d.get("isp")}
    except Exception:
        geo = {}
    if geo:
        await cache_set(cache_key, json.dumps(geo), ttl=60 * 60 * 24 * 7)
    return geo


async def build_client_context(req: Request) -> dict:
    """Everything we record about the client: {ip, geo, device, browser, os}."""
    ip = client_ip(req)
    ctx = {"ip": ip, "geo": await geo_lookup(ip)}
    ctx.update(parse_user_agent(req.headers.get("user-agent")))
    return ctx
