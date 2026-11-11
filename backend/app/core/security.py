import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from urllib.parse import urlsplit

from app.core.config import get_settings

MIN_PASSWORD_LENGTH = 10


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def hash_password(password: str) -> str:
    rounds = get_settings().iterations
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, rounds)
    return f"pbkdf2_sha256${rounds}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, rounds, salt_hex, digest_hex = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(rounds))
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


_dummy_hash: str | None = None


def dummy_password_hash() -> str:
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hash_password("not-a-real-password")
    return _dummy_hash


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def public_url(url: str) -> str | None:
    raw = url.strip()
    if not raw:
        return None
    parts = urlsplit(raw)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        return None
    if parts.username or parts.password:
        host = parts.hostname
        if parts.port:
            host = f"{host}:{parts.port}"
        return f"{parts.scheme}://{host}"
    return raw


def clean_label(value: str, limit: int) -> str | None:
    text = " ".join(value.split())
    if not text or len(text) > limit:
        return None
    if any(ord(char) < 32 for char in text):
        return None
    return text


def clean_external_key(value: str) -> str | None:
    text = value.strip()
    if not text or len(text) > 128:
        return None
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-")
    if any(char not in allowed for char in text):
        return None
    return text


def clean_username(value: str) -> str | None:
    name = value.strip()
    if not name or len(name) > 128:
        return None
    if any(ord(char) < 32 or char in "{}()*\\" for char in name):
        return None
    return name
