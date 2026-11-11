from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.roles import sort_roles
from app.core.security import clean_username, dummy_password_hash, verify_password
from app.models import User


@dataclass
class AuthResult:
    ok: bool
    reason: str = ""
    username: str = ""
    display_name: str = ""
    roles: list[str] | None = None
    provider: str = ""


class AuthProvider:
    def authenticate(self, db: Session, username: str, password: str) -> AuthResult:
        raise NotImplementedError


def local_result(user: User | None, password: str) -> AuthResult:
    if user is None or not user.password_hash:
        verify_password(password, dummy_password_hash())
        return AuthResult(ok=False, reason="invalid")
    if not verify_password(password, user.password_hash):
        return AuthResult(ok=False, reason="invalid")
    if not user.is_active:
        return AuthResult(ok=False, reason="inactive")
    roles = sort_roles([item.role for item in user.roles])
    if not roles:
        return AuthResult(ok=False, reason="no_role")
    return AuthResult(
        ok=True,
        username=user.username,
        display_name=user.display_name,
        roles=roles,
        provider="local",
    )


def checked_username(value: str) -> str | None:
    return clean_username(value)
