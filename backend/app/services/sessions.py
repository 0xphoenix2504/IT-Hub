from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.ldaps import LdapsAuth
from app.auth.local import LocalAuth
from app.core.audit import add_audit
from app.core.config import get_settings
from app.core.lockout import clear_username, is_locked, record_failure
from app.core.roles import sort_roles
from app.core.security import as_utc, hash_token, new_session_token, utcnow
from app.models import SessionToken, User
from datetime import timedelta


class LoginDenied(Exception):
    def __init__(self, status: int, detail: str):
        self.status = status
        self.detail = detail


def authenticate_credentials(db: Session, username: str, password: str):
    settings = get_settings()
    if settings.provider == "ldaps":
        return LdapsAuth().authenticate(db, username, password)
    if settings.provider == "local":
        return LocalAuth().authenticate(db, username, password)
    raise LoginDenied(503, "Sign-in is unavailable right now.")


def start_session(db: Session, username: str, password: str, ip: str) -> str:
    from app.text import INVALID_LOGIN, LOCKED, UNAVAILABLE

    if len(password) > 128:
        record_failure(username or "unknown", ip)
        add_audit(db, username or "unknown", "login_failure", "rejected", ip)
        db.commit()
        raise LoginDenied(401, INVALID_LOGIN)
    if is_locked(username, ip):
        raise LoginDenied(429, LOCKED)
    result = authenticate_credentials(db, username, password)
    if not result.ok:
        record_failure(username, ip)
        action = "login_denied_no_role" if result.reason == "no_role" else "login_failure"
        if result.reason == "unavailable":
            add_audit(db, username or "unknown", "login_failure", "directory unavailable", ip)
            db.commit()
            raise LoginDenied(503, UNAVAILABLE)
        add_audit(db, result.username or username or "unknown", action, result.reason, ip)
        db.commit()
        raise LoginDenied(401, INVALID_LOGIN)
    user = db.query(User).filter(func.lower(User.username) == result.username.lower()).one_or_none()
    if user is None or not user.is_active:
        record_failure(username, ip)
        add_audit(db, username, "login_failure", "missing account", ip)
        db.commit()
        raise LoginDenied(401, INVALID_LOGIN)
    clear_username(username, ip)
    db.query(SessionToken).filter(SessionToken.user_id == user.id).delete()
    token = new_session_token()
    settings = get_settings()
    now = utcnow()
    user.last_login_at = now
    db.add(
        SessionToken(
            user_id=user.id,
            token_hash=hash_token(token),
            auth_provider=settings.provider,
            roles_json=sort_roles(result.roles or []),
            expires_at=now + timedelta(seconds=settings.ttl_seconds),
            created_at=now,
            ip=ip[:64],
        )
    )
    add_audit(db, user.username, "login_success", "", ip)
    db.commit()
    return token


def user_from_token(db: Session, token: str):
    if not token:
        return None
    row = db.query(SessionToken).filter(SessionToken.token_hash == hash_token(token)).one_or_none()
    if row is None:
        return None
    if as_utc(row.expires_at) <= utcnow() or row.auth_provider != get_settings().provider:
        db.delete(row)
        db.commit()
        return None
    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        return None
    if user.provider == "local":
        roles = sort_roles([item.role for item in user.roles])
    else:
        roles = sort_roles(list(row.roles_json or []))
    if not roles:
        return None
    return user, roles


def end_session(db: Session, token: str, ip: str) -> None:
    if not token:
        return
    row = db.query(SessionToken).filter(SessionToken.token_hash == hash_token(token)).one_or_none()
    if row is None:
        return
    user = db.get(User, row.user_id)
    actor = user.username if user is not None else "unknown"
    db.delete(row)
    add_audit(db, actor, "logout", "", ip)
    db.commit()
