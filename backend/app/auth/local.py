from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.base import AuthResult, local_result
from app.models import User


class LocalAuth:
    provider_name = "local"

    def authenticate(self, db: Session, username: str, password: str) -> AuthResult:
        user = (
            db.query(User)
            .filter(func.lower(User.username) == username.lower(), User.provider == "local")
            .one_or_none()
        )
        return local_result(user, password)
