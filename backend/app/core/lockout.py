import time

from app.core.config import get_settings

_attempts: dict[str, list[float]] = {}


def _prune(key: str, now: float, window: float) -> list[float]:
    kept = [stamp for stamp in _attempts.get(key, []) if now - stamp < window]
    if kept:
        _attempts[key] = kept
    else:
        _attempts.pop(key, None)
    return kept


def is_locked(username: str, ip: str) -> bool:
    settings = get_settings()
    window = settings.lockout_minutes * 60
    now = time.monotonic()
    user_key = f"u:{username.lower()}|{ip}"
    ip_key = f"ip:{ip}"
    user_hits = len(_prune(user_key, now, window))
    ip_hits = len(_prune(ip_key, now, window))
    return user_hits >= settings.max_attempts or ip_hits >= settings.max_attempts * 4


def record_failure(username: str, ip: str) -> None:
    now = time.monotonic()
    for key in (f"u:{username.lower()}|{ip}", f"ip:{ip}"):
        _attempts.setdefault(key, []).append(now)


def clear_username(username: str, ip: str) -> None:
    _attempts.pop(f"u:{username.lower()}|{ip}", None)


def clear_all() -> None:
    _attempts.clear()
