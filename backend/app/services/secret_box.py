"""Secrets vault — encrypt/decrypt integration credentials (blueprint/17,19).

Pattern adapted from OmniMark's secret_box: the DB stores ciphertext only; the
master key lives in env/KMS (settings.SECRET_VAULT_KEY), never in the DB. Secrets are
decrypted only in the backend at call time and never returned to the client.

Dev implementation uses Fernet (AES128-CBC + HMAC) via `cryptography` if available;
otherwise a clearly-labelled reversible dev fallback so the scaffold runs. PRODUCTION
must use the real KMS/Fernet path.
"""
from __future__ import annotations

import base64
import hashlib

from ..core.config import settings


def _fernet():
    try:
        from cryptography.fernet import Fernet
    except Exception:
        return None
    # derive a 32-byte urlsafe key from the configured master key
    digest = hashlib.sha256(settings.SECRET_VAULT_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt(plaintext: str) -> bytes:
    f = _fernet()
    if f is not None:
        return f.encrypt(plaintext.encode())
    # dev fallback (NOT secure — flagged). XOR+b64 so the scaffold runs without cryptography.
    key = hashlib.sha256(settings.SECRET_VAULT_KEY.encode()).digest()
    raw = plaintext.encode()
    xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(raw))
    return b"DEVFALLBACK:" + base64.b64encode(xored)


def decrypt(ciphertext: bytes) -> str:
    if ciphertext.startswith(b"DEVFALLBACK:"):
        key = hashlib.sha256(settings.SECRET_VAULT_KEY.encode()).digest()
        xored = base64.b64decode(ciphertext[len(b"DEVFALLBACK:"):])
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(xored)).decode()
    f = _fernet()
    if f is None:
        raise RuntimeError("cryptography not available to decrypt a Fernet secret")
    return f.decrypt(ciphertext).decode()


def mask(plaintext: str) -> str:
    """Masked hint for the admin UI — never reveals the secret."""
    if not plaintext:
        return ""
    tail = plaintext[-4:] if len(plaintext) >= 4 else ""
    return "•" * 8 + tail
