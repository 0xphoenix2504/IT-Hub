from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import Principal, client_ip, require_roles
from app.core.audit import add_audit
from app.core.database import get_db
from app.core.roles import EXECUTIVE, HELPDESK, NETWORK_ADMIN, SYSTEM_ADMIN
from app.schemas import ExecutiveDashboard, TechnicalDashboard
from app.services.dashboard import build_executive, build_technical
from app.services.report import render_pdf, report_lines

router = APIRouter(prefix="/api", tags=["dashboards"])


@router.get("/dashboard/executive", response_model=ExecutiveDashboard)
def executive_dashboard(
    _: Principal = Depends(require_roles(EXECUTIVE)),
    db: Session = Depends(get_db),
) -> ExecutiveDashboard:
    return build_executive(db)


@router.get("/dashboard/servers", response_model=TechnicalDashboard)
def servers_dashboard(
    _: Principal = Depends(require_roles(SYSTEM_ADMIN)),
    db: Session = Depends(get_db),
) -> TechnicalDashboard:
    return build_technical(db, "servers", "server")


@router.get("/dashboard/network", response_model=TechnicalDashboard)
def network_dashboard(
    _: Principal = Depends(require_roles(NETWORK_ADMIN)),
    db: Session = Depends(get_db),
) -> TechnicalDashboard:
    return build_technical(db, "network", "network")


@router.get("/dashboard/helpdesk", response_model=TechnicalDashboard)
def helpdesk_dashboard(
    _: Principal = Depends(require_roles(HELPDESK)),
    db: Session = Depends(get_db),
) -> TechnicalDashboard:
    return build_technical(db, "endpoints", "endpoint")


@router.get("/reports/executive.pdf")
def executive_report(
    request: Request,
    principal: Principal = Depends(require_roles(EXECUTIVE)),
    db: Session = Depends(get_db),
) -> Response:
    board = build_executive(db)
    payload = render_pdf(report_lines(board))
    add_audit(db, principal.username, "report_exported", "executive monthly", client_ip(request))
    db.commit()
    return Response(
        content=payload,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="it-hub-monthly-report.pdf"'},
    )
