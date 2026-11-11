from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.roles import IT_MANAGER
from app.models import User
from app.services.sessions import user_from_token
from app.text import NO_ACCESS, SIGN_IN_REQUIRED


@dataclass
class Principal:
    user: User
    roles: list[str]

    @property
    def username(self) -> str:
        return self.user.username


def client_ip(request: Request) -> str:
    if get_settings().proxy_trusted:
        forwarded = request.headers.get("x-forwarded-for", "")
        first = forwarded.split(",")[0].strip()
        if first:
            return first[:64]
    if request.client is None:
        return "unknown"
    return request.client.host[:64]


def get_principal(request: Request, db: Session = Depends(get_db)) -> Principal:
    token = request.cookies.get(get_settings().cookie_name, "")
    found = user_from_token(db, token)
    if found is None:
        raise HTTPException(status_code=401, detail=SIGN_IN_REQUIRED)
    user, roles = found
    return Principal(user=user, roles=roles)


def require_roles(*allowed: str):
    def dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if IT_MANAGER in principal.roles or any(role in principal.roles for role in allowed):
            return principal
        raise HTTPException(status_code=403, detail=NO_ACCESS)
    return dependency


def require_manager(principal: Principal = Depends(get_principal)) -> Principal:
    if IT_MANAGER not in principal.roles:
        raise HTTPException(status_code=403, detail=NO_ACCESS)
    return principal
