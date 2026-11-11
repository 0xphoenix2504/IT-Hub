from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import Principal, client_ip, get_principal
from app.core.audit import add_audit
from app.core.config import get_settings
from app.core.database import get_db
from app.core.lockout import record_failure
from app.core.security import clean_username
from app.schemas import LoginBody, Me
from app.services.sessions import LoginDenied, end_session, start_session
from app.text import INVALID_LOGIN

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _me(principal: Principal) -> Me:
    return Me(
        username=principal.user.username,
        display_name=principal.user.display_name,
        roles=principal.roles,
        auth_provider=principal.user.provider,
    )


def _write_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        secure=settings.secure_cookie,
        samesite=settings.samesite,
        max_age=settings.ttl_seconds,
        path="/",
    )


def _clear_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.cookie_name,
        path="/",
        httponly=True,
        secure=settings.secure_cookie,
        samesite=settings.samesite,
    )


@router.post("/login", response_model=Me)
def login(body: LoginBody, request: Request, response: Response, db: Session = Depends(get_db)) -> Me:
    username = clean_username(body.username)
    ip = client_ip(request)
    if username is None or not body.password:
        record_failure((body.username or "unknown")[:128], ip)
        add_audit(db, (body.username or "unknown")[:128], "login_failure", "rejected", ip)
        db.commit()
        raise HTTPException(status_code=401, detail=INVALID_LOGIN)
    try:
        token = start_session(db, username, body.password, ip)
    except LoginDenied as exc:
        raise HTTPException(status_code=exc.status, detail=exc.detail) from exc
    principal_row = user_from_request_token(db, token)
    _write_cookie(response, token)
    return principal_row


def user_from_request_token(db: Session, token: str) -> Me:
    from app.services.sessions import user_from_token

    found = user_from_token(db, token)
    if found is None:
        raise HTTPException(status_code=401, detail=INVALID_LOGIN)
    user, roles = found
    return Me(username=user.username, display_name=user.display_name, roles=roles, auth_provider=user.provider)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> None:
    token = request.cookies.get(get_settings().cookie_name, "")
    end_session(db, token, client_ip(request))
    _clear_cookie(response)


@router.get("/me", response_model=Me)
def me(principal: Principal = Depends(get_principal)) -> Me:
    return _me(principal)
