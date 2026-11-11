from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import Principal, client_ip, require_manager
from app.core.audit import add_audit
from app.core.database import get_db
from app.core.roles import FIXED_EXECUTIVE_GROUP, GROUP_ROLES, clean_group_name
from app.core.security import clean_external_key, clean_label
from app.models import AuditLog, CriticalService, RoleMapping
from app.schemas import (
    AuditOut,
    ConnectionOut,
    MappingBody,
    MappingOut,
    ServiceBody,
    ServiceOut,
    UserBody,
    UserOut,
    UserPatch,
)
from app.services.accounts import create_user, list_users, update_user
from app.services.connections import connection_status

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/connections", response_model=list[ConnectionOut])
def connections(_: Principal = Depends(require_manager)) -> list[ConnectionOut]:
    return connection_status()


@router.get("/mappings", response_model=list[MappingOut])
def mappings(_: Principal = Depends(require_manager), db: Session = Depends(get_db)) -> list[MappingOut]:
    rows = db.query(RoleMapping).order_by(RoleMapping.ad_group).all()
    return [MappingOut(id=row.id, ad_group=row.ad_group, role=row.role) for row in rows]


@router.post("/mappings", response_model=MappingOut)
def add_mapping(
    body: MappingBody,
    request: Request,
    principal: Principal = Depends(require_manager),
    db: Session = Depends(get_db),
) -> MappingOut:
    group = clean_group_name(body.ad_group)
    if group is None:
        raise HTTPException(status_code=400, detail="Group name is not valid.")
    if group == FIXED_EXECUTIVE_GROUP:
        raise HTTPException(status_code=400, detail="The executives group is fixed and cannot be mapped here.")
    if body.role not in GROUP_ROLES:
        raise HTTPException(status_code=400, detail="Choose a valid role.")
    existing = db.query(RoleMapping).filter(func.lower(RoleMapping.ad_group) == group).one_or_none()
    if existing is not None:
        raise HTTPException(status_code=400, detail="That group is already mapped.")
    row = RoleMapping(ad_group=group, role=body.role)
    db.add(row)
    add_audit(db, principal.username, "mapping_created", f"{group} -> {body.role}", client_ip(request))
    db.commit()
    db.refresh(row)
    return MappingOut(id=row.id, ad_group=row.ad_group, role=row.role)


@router.delete("/mappings/{mapping_id}", status_code=204)
def delete_mapping(
    mapping_id: int,
    request: Request,
    principal: Principal = Depends(require_manager),
    db: Session = Depends(get_db),
) -> Response:
    row = db.get(RoleMapping, mapping_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Mapping not found.")
    detail = f"{row.ad_group} -> {row.role}"
    db.delete(row)
    add_audit(db, principal.username, "mapping_deleted", detail, client_ip(request))
    db.commit()
    return Response(status_code=204)


@router.get("/services", response_model=list[ServiceOut])
def services(_: Principal = Depends(require_manager), db: Session = Depends(get_db)) -> list[ServiceOut]:
    rows = db.query(CriticalService).order_by(CriticalService.sort_order, CriticalService.id).all()
    return [
        ServiceOut(id=row.id, name=row.name, external_key=row.external_key, sort_order=row.sort_order)
        for row in rows
    ]


@router.post("/services", response_model=ServiceOut)
def add_service(
    body: ServiceBody,
    request: Request,
    principal: Principal = Depends(require_manager),
    db: Session = Depends(get_db),
) -> ServiceOut:
    name = clean_label(body.name, 80)
    key = clean_external_key(body.external_key)
    if name is None or key is None:
        raise HTTPException(status_code=400, detail="Enter a service name and a key made of letters, numbers, and . _ : -.")
    duplicate_name = db.query(CriticalService).filter(func.lower(CriticalService.name) == name.lower()).one_or_none()
    duplicate_key = db.query(CriticalService).filter(func.lower(CriticalService.external_key) == key.lower()).one_or_none()
    if duplicate_name is not None or duplicate_key is not None:
        raise HTTPException(status_code=400, detail="That service is already listed.")
    current = db.query(func.max(CriticalService.sort_order)).scalar()
    row = CriticalService(name=name, external_key=key, sort_order=(current or 0) + 1)
    db.add(row)
    add_audit(db, principal.username, "service_created", name, client_ip(request))
    db.commit()
    db.refresh(row)
    return ServiceOut(id=row.id, name=row.name, external_key=row.external_key, sort_order=row.sort_order)


@router.delete("/services/{service_id}", status_code=204)
def delete_service(
    service_id: int,
    request: Request,
    principal: Principal = Depends(require_manager),
    db: Session = Depends(get_db),
) -> Response:
    row = db.get(CriticalService, service_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Service not found.")
    name = row.name
    db.delete(row)
    add_audit(db, principal.username, "service_deleted", name, client_ip(request))
    db.commit()
    return Response(status_code=204)


@router.get("/users", response_model=list[UserOut])
def users(_: Principal = Depends(require_manager), db: Session = Depends(get_db)) -> list[UserOut]:
    return list_users(db)


@router.post("/users", response_model=UserOut)
def post_user(
    body: UserBody,
    request: Request,
    principal: Principal = Depends(require_manager),
    db: Session = Depends(get_db),
) -> UserOut:
    return create_user(
        db,
        body.username,
        body.password,
        body.display_name,
        body.roles,
        principal.username,
        client_ip(request),
    )


@router.patch("/users/{user_id}", response_model=UserOut)
def patch_user(
    user_id: int,
    body: UserPatch,
    request: Request,
    principal: Principal = Depends(require_manager),
    db: Session = Depends(get_db),
) -> UserOut:
    return update_user(
        db,
        user_id,
        body.display_name,
        body.password,
        body.is_active,
        body.roles,
        principal.username,
        client_ip(request),
    )


@router.get("/audit", response_model=list[AuditOut])
def audit(_: Principal = Depends(require_manager), db: Session = Depends(get_db)) -> list[AuditOut]:
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(200).all()
    return [
        AuditOut(id=row.id, created_at=row.created_at, actor=row.actor, action=row.action, detail=row.detail, ip=row.ip)
        for row in rows
    ]
