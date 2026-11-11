from collections.abc import Callable
from datetime import timedelta

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import utcnow
from app.models import StatsCache
from app.schemas import Section


def cached_section(db: Session, key: str, model: type[BaseModel], producer: Callable[[], Section]) -> Section:
    ttl = get_settings().cache_seconds
    if ttl <= 0:
        return producer()
    now = utcnow()
    row = db.get(StatsCache, key)
    if row is not None and row.expires_at is not None:
        expires = row.expires_at
        if expires.tzinfo is None:
            from datetime import timezone

            expires = expires.replace(tzinfo=timezone.utc)
        if expires > now:
            try:
                return model.model_validate(row.payload)
            except ValidationError:
                db.delete(row)
                db.commit()
    section = producer()
    if section.status == "ok":
        db.merge(
            StatsCache(
                cache_key=key,
                payload=section.model_dump(mode="json"),
                expires_at=now + timedelta(seconds=ttl),
            )
        )
        db.commit()
    return section
