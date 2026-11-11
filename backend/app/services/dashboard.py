import hashlib

from sqlalchemy.orm import Session

from app.adapters import registry
from app.core.config import get_settings
from app.core.security import public_url, utcnow
from app.models import CriticalService
from app.schemas import (
    DeepLinks,
    DeviceRecord,
    ExecutiveDashboard,
    Section,
    ServiceHealth,
    TechnicalDashboard,
    empty_section,
    error_section,
)
from app.services.cache import cached_section


def merge_device_lists(assets: list[DeviceRecord], monitors: list[DeviceRecord]) -> list[DeviceRecord]:
    merged = {item.id: item for item in assets}
    order = [item.id for item in assets]
    for item in monitors:
        current = merged.get(item.id)
        if current is None:
            merged[item.id] = item
            order.append(item.id)
            continue
        merged[item.id] = current.model_copy(
            update={
                "status": item.status,
                "hostname": item.hostname or current.hostname,
                "ip": item.ip or current.ip,
                "name": current.name or item.name,
            }
        )
    return [merged[key] for key in order]


def merge_device_results(
    assets: Section[list[DeviceRecord]],
    monitor: Section[list[DeviceRecord]],
) -> Section[list[DeviceRecord]]:
    parts = [assets, monitor]
    ok_parts = [part for part in parts if part.status == "ok" and part.data is not None]
    errors = [part for part in parts if part.status == "error"]
    if not ok_parts and errors:
        return error_section()
    if not ok_parts:
        return empty_section()
    if len(ok_parts) == 1:
        devices = list(ok_parts[0].data or [])
    else:
        devices = merge_device_lists(list(assets.data or []), list(monitor.data or []))
    times = [part.last_updated for part in ok_parts if part.last_updated is not None]
    return Section(
        status="ok",
        message="Some sources could not be loaded." if errors else None,
        last_updated=max(times) if times else utcnow(),
        data=devices,
    )


def deep_links() -> DeepLinks:
    settings = get_settings()
    return DeepLinks(
        ticketing=public_url(settings.ticketing_app_base_url),
        assets=public_url(settings.assets_app_base_url),
    )


def _health_key(services: list[CriticalService]) -> str:
    identity = ",".join(f"{item.id}:{item.external_key}" for item in services)
    digest = hashlib.sha256(identity.encode()).hexdigest()[:16]
    return f"health:{digest}"


def service_health(db: Session) -> Section[list[ServiceHealth]]:
    services = db.query(CriticalService).order_by(CriticalService.sort_order, CriticalService.id).all()
    source = registry.monitor()
    if not services or not source.configured():
        return empty_section()
    model = Section[list[ServiceHealth]]
    return cached_section(db, _health_key(services), model, lambda: source.service_health(services))


def ticket_summary(db: Session, scope: str) -> Section:
    source = registry.ticketing()
    if not source.configured():
        return empty_section()
    from app.schemas import TicketStats

    return cached_section(db, f"tickets:{scope}", Section[TicketStats], lambda: source.summary(scope))


def problems(db: Session, scope: str) -> Section:
    source = registry.ticketing()
    if not source.configured():
        return empty_section()
    from app.schemas import ProblemStat

    return cached_section(
        db,
        f"problems:{scope}",
        Section[list[ProblemStat]],
        lambda: source.top_problems(scope, 5),
    )


def devices_for(db: Session, kind: str) -> Section[list[DeviceRecord]]:
    asset_source = registry.assets()
    monitor_source = registry.monitor()
    if not asset_source.configured() and not monitor_source.configured():
        return empty_section()

    def produce() -> Section[list[DeviceRecord]]:
        assets = asset_source.devices(kind) if asset_source.configured() else empty_section()
        monitor = monitor_source.devices(kind) if monitor_source.configured() else empty_section()
        return merge_device_results(assets, monitor)

    return cached_section(db, f"devices:{kind}", Section[list[DeviceRecord]], produce)


def build_executive(db: Session) -> ExecutiveDashboard:
    return ExecutiveDashboard(
        generated_at=utcnow(),
        service_health=service_health(db),
        tickets=ticket_summary(db, "all"),
        assets=_assets(db),
        top_problems=problems(db, "all"),
    )


def _assets(db: Session) -> Section:
    source = registry.assets()
    if not source.configured():
        return empty_section()
    from app.schemas import AssetStats

    return cached_section(db, "assets:summary", Section[AssetStats], source.summary)


def build_technical(db: Session, ticket_scope: str, device_kind: str) -> TechnicalDashboard:
    return TechnicalDashboard(
        generated_at=utcnow(),
        tickets=ticket_summary(db, ticket_scope),
        problems=problems(db, ticket_scope),
        devices=devices_for(db, device_kind),
        links=deep_links(),
    )
