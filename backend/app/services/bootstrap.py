import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.roles import IT_MANAGER
from app.core.security import MIN_PASSWORD_LENGTH, hash_password, utcnow
from app.models import User, UserRole

log = logging.getLogger(__name__)


def bootstrap_first_admin(db: Session) -> None:
    settings = get_settings()
    if settings.provider != "local":
        return
    username = settings.first_admin_username.strip()
    password = settings.first_admin_password
    if not username or not password:
        log.info("First admin is not configured.")
        return
    if len(password) < MIN_PASSWORD_LENGTH:
        log.error("FIRST_ADMIN_PASSWORD must be at least 10 characters. Admin was not created.")
        return
    existing = db.query(User).filter(func.lower(User.username) == username.lower()).one_or_none()
    if existing is not None:
        return
    display = settings.first_admin_display_name.strip() or username
    user = User(
        username=username,
        display_name=display[:128],
        password_hash=hash_password(password),
        provider="local",
        is_active=True,
        created_at=utcnow(),
    )
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role=IT_MANAGER))
    db.commit()
    log.info("Created the first admin account for %s", username)
