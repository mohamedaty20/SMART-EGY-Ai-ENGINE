"""
services/auth_service.py — Password hashing + session tokens.
"""
import os
import hmac
import time
import json
import base64
import hashlib

SECRET = os.environ.get("SESSION_SECRET", "change-me-in-render-env").encode()


def hash_password(password, salt=None):
    """Return (salt_hex, hash_hex)."""
    if salt is None:
        salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(),
                             bytes.fromhex(salt), 100_000)
    return salt, dk.hex()


def verify_password(password, salt_hex, hash_hex):
    if not salt_hex or not hash_hex:
        return False
    _, computed = hash_password(password, salt_hex)
    return hmac.compare_digest(computed, hash_hex)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def make_session(user_id, days=30):
    payload = {"uid": int(user_id), "exp": int(time.time()) + days * 86400}
    body = _b64(json.dumps(payload).encode())
    sig = hmac.new(SECRET, body.encode(), hashlib.sha256).digest()
    return body + "." + _b64(sig)


def read_session(token):
    if not token or "." not in token:
        return None
    body, sig = token.split(".", 1)
    expected = hmac.new(SECRET, body.encode(), hashlib.sha256).digest()
    try:
        if not hmac.compare_digest(_unb64(sig), expected):
            return None
        payload = json.loads(_unb64(body).decode())
        if payload.get("exp", 0) < time.time():
            return None
        return int(payload["uid"])
    except Exception:
        return None
