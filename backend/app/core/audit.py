from sqlalchemy.orm import Session

from app.core.security import utcnow
from app.models import AuditLog


def add_audit(db: Session, actor: str, action: str, detail: str, ip: str | None) -> None:
    db.add(
        AuditLog(
            created_at=utcnow(),
            actor=actor[:128] or "unknown",
            action=action[:64],
            detail=detail[:500],
            ip=(ip or None),
        )
    )
