from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.audit import add_audit
from app.core.config import get_settings
from app.core.roles import ALL_ROLES, IT_MANAGER, sort_roles
from app.core.security import MIN_PASSWORD_LENGTH, clean_username, hash_password, utcnow
from app.models import User, UserRole
from app.schemas import UserOut


def to_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        provider=user.provider,
        is_active=user.is_active,
        roles=sort_roles([item.role for item in user.roles]),
    )


def list_users(db: Session) -> list[UserOut]:
    users = db.query(User).order_by(User.username).all()
    return [to_user_out(user) for user in users]


def _require_local_provider() -> None:
    if get_settings().provider != "local":
        raise HTTPException(status_code=400, detail="Accounts are managed in Active Directory.")


def _validate_roles(roles: list[str]) -> list[str]:
    cleaned = sort_roles(roles)
    if not cleaned or any(role not in ALL_ROLES for role in roles):
        raise HTTPException(status_code=400, detail="Choose at least one valid role.")
    return cleaned


def _manager_count(db: Session, ignore_user_id: int | None = None) -> int:
    query = (
        db.query(User)
        .join(UserRole)
        .filter(User.is_active.is_(True), User.provider == "local", UserRole.role == IT_MANAGER)
    )
    if ignore_user_id is not None:
        query = query.filter(User.id != ignore_user_id)
    return query.count()


def create_user(
    db: Session,
    username: str,
    password: str,
    display_name: str,
    roles: list[str],
    actor: str,
    ip: str | None,
) -> UserOut:
    _require_local_provider()
    cleaned_name = clean_username(username)
    if cleaned_name is None:
        raise HTTPException(status_code=400, detail="Username is not valid.")
    if len(password) < MIN_PASSWORD_LENGTH or len(password) > 128:
        raise HTTPException(status_code=400, detail="Password must be 10 to 128 characters.")
    assigned = _validate_roles(roles)
    existing = db.query(User).filter(func.lower(User.username) == cleaned_name.lower()).one_or_none()
    if existing is not None:
        raise HTTPException(status_code=400, detail="That username is already in use.")
    display = display_name.strip()[:128] or cleaned_name
    user = User(
        username=cleaned_name,
        display_name=display,
        password_hash=hash_password(password),
        provider="local",
        is_active=True,
        created_at=utcnow(),
    )
    db.add(user)
    db.flush()
    for role in assigned:
        db.add(UserRole(user_id=user.id, role=role))
    add_audit(db, actor, "user_created", cleaned_name, ip)
    db.commit()
    db.refresh(user)
    return to_user_out(user)


def update_user(
    db: Session,
    user_id: int,
    display_name: str | None,
    password: str | None,
    is_active: bool | None,
    roles: list[str] | None,
    actor: str,
    ip: str | None,
) -> UserOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Account not found.")
    if user.provider != "local":
        raise HTTPException(status_code=400, detail="This account is managed in Active Directory.")
    current_roles = [item.role for item in user.roles]
    next_roles = _validate_roles(roles) if roles is not None else sort_roles(current_roles)
    next_active = user.is_active if is_active is None else is_active
    removing_manager = IT_MANAGER in current_roles and (IT_MANAGER not in next_roles or not next_active)
    if removing_manager and user.is_active and _manager_count(db, ignore_user_id=user.id) == 0:
        raise HTTPException(status_code=400, detail="The last IT Manager cannot be removed.")
    if password is not None:
        if len(password) < MIN_PASSWORD_LENGTH or len(password) > 128:
            raise HTTPException(status_code=400, detail="Password must be 10 to 128 characters.")
        user.password_hash = hash_password(password)
    if display_name is not None and display_name.strip():
        user.display_name = display_name.strip()[:128]
    user.is_active = next_active
    if roles is not None:
        db.query(UserRole).filter(UserRole.user_id == user.id).delete()
        for role in next_roles:
            db.add(UserRole(user_id=user.id, role=role))
    changed = []
    if display_name is not None and display_name.strip():
        changed.append("display name")
    if password is not None:
        changed.append("password")
    if is_active is not None:
        changed.append("active")
    if roles is not None:
        changed.append("roles")
    add_audit(db, actor, "user_updated", f"{user.username}: {', '.join(changed) or 'saved'}", ip)
    db.commit()
    db.refresh(user)
    return to_user_out(user)
