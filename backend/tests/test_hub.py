import pytest
from pydantic import ValidationError

from app.adapters import registry
from app.auth.ldaps import group_names_from_dns, roles_for_groups
from app.core.lockout import clear_all
from app.core.security import hash_password, public_url, utcnow
from app.models import RoleMapping, User, UserRole
from app.schemas import DeviceRecord, Section, ServiceHealth
from app.services.dashboard import build_executive, merge_device_lists
from app.services.report import render_pdf, report_lines

ADMIN = {"username": "admin", "password": "correct-horse-1"}
FORBIDDEN_KEYS = {"ip", "hostname", "interface", "log", "logs"}


def keys(value):
    found = set()
    if isinstance(value, dict):
        found.update(value.keys())
        for item in value.values():
            found |= keys(item)
    elif isinstance(value, list):
        for item in value:
            found |= keys(item)
    return found


def login(client, body=None):
    return client.post("/api/auth/login", json=body or ADMIN)


def test_adapters_are_unconfigured():
    assert registry.ticketing().configured() is False
    assert registry.assets().configured() is False
    assert registry.monitor().configured() is False
    assert registry.sso().configured() is False
    assert registry.sso().start("someone", "ticketing").status == "not_configured"


def test_executive_model_rejects_technical_fields():
    with pytest.raises(ValidationError):
        ServiceHealth.model_validate(
            {"name": "Mail", "state": "up", "availability_30d": 99.0, "ip": "10.0.0.8", "hostname": "mail"}
        )


def test_public_url_strips_credentials():
    assert public_url("https://user:secret@tickets.example/app") == "https://tickets.example"
    assert public_url("") is None
    assert public_url("not a url") is None


def test_group_mapping_unions_roles_and_keeps_executives_fixed(db):
    db.add(RoleMapping(ad_group="svc-admins", role="system_admin"))
    db.commit()
    names = group_names_from_dns(
        ["CN=Executives,OU=Groups,DC=example,DC=com", "CN=svc-admins,OU=Groups,DC=example,DC=com"]
    )
    assert roles_for_groups(db, names) == ["system_admin", "executive"]
    assert roles_for_groups(db, {"interns"}) == []


def test_merge_keeps_asset_name_and_monitor_status():
    assets = [DeviceRecord(id="a1", name="Mail server", kind="server", status="unknown", ip=None, hostname=None)]
    monitors = [DeviceRecord(id="a1", name="mail", kind="server", status="up", ip="10.1.1.8", hostname="mail.example")]
    merged = merge_device_lists(assets, monitors)
    assert merged[0].name == "Mail server"
    assert merged[0].status == "up"
    assert merged[0].ip == "10.1.1.8"


def test_login_cookie_and_empty_executive_dashboard(client):
    assert client.get("/api/dashboard/executive").status_code == 401

    response = login(client)
    assert response.status_code == 200
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    body = response.json()
    assert body["roles"] == ["it_manager"]
    assert "password" not in body

    board = client.get("/api/dashboard/executive")
    assert board.status_code == 200
    payload = board.json()
    assert payload["tickets"]["status"] == "not_configured"
    assert payload["tickets"]["data"] is None
    assert payload["service_health"]["message"] == "No data connected yet"
    assert keys(payload).isdisjoint(FORBIDDEN_KEYS)


def test_report_has_no_invented_numbers(db):
    text = "\n".join(report_lines(build_executive(db)))
    assert text.count("No data connected yet") >= 4
    assert "$" not in text
    assert render_pdf(report_lines(build_executive(db))).startswith(b"%PDF")


def test_role_boundaries_and_settings(client):
    assert login(client).status_code == 200
    created = client.post(
        "/api/settings/users",
        json={
            "username": "desk",
            "password": "helpdesk-pass-1",
            "display_name": "Desk",
            "roles": ["helpdesk"],
        },
    )
    assert created.status_code == 200
    assert "password_hash" not in created.json()

    assert client.post("/api/settings/services", json={"name": "Email", "external_key": "mail"}).status_code == 200
    assert client.post("/api/settings/mappings", json={"ad_group": "Executives", "role": "it_manager"}).status_code == 400
    assert client.post("/api/settings/mappings", json={"ad_group": "Service Admins", "role": "system_admin"}).status_code == 200
    assert client.get("/api/dashboard/executive").json()["service_health"]["status"] == "not_configured"

    report = client.get("/api/reports/executive.pdf")
    assert report.status_code == 200
    assert report.content.startswith(b"%PDF")
    assert "helpdesk-pass-1" not in str(client.get("/api/settings/audit").json())

    client.post("/api/auth/logout")
    client.cookies.clear()
    assert login(client, {"username": "desk", "password": "helpdesk-pass-1"}).status_code == 200
    helpdesk = client.get("/api/dashboard/helpdesk")
    assert helpdesk.status_code == 200
    assert helpdesk.json()["devices"]["status"] == "not_configured"
    assert helpdesk.json()["devices"]["data"] is None
    assert client.get("/api/dashboard/servers").status_code == 403
    assert client.get("/api/dashboard/network").status_code == 403
    assert client.get("/api/dashboard/executive").status_code == 403
    assert client.get("/api/settings/users").status_code == 403


def test_lockout_and_missing_role(client, db):
    for _ in range(3):
        failed = login(client, {"username": "admin", "password": "wrong-password-1"})
        assert failed.status_code == 401
        assert failed.json()["detail"] == "Invalid username or password."
    assert login(client).status_code == 429

    db.add(
        User(
            username="norole",
            display_name="No Role",
            password_hash=hash_password("correct-horse-1"),
            provider="local",
            is_active=True,
            created_at=utcnow(),
        )
    )
    db.commit()
    clear_all()
    denied = login(client, {"username": "norole", "password": "correct-horse-1"})
    assert denied.status_code == 401
    assert "role" not in denied.json()["detail"].lower()


def test_last_manager_cannot_be_removed(client, db):
    assert login(client).status_code == 200
    admin = db.query(User).filter(User.username == "admin").one()
    assert client.patch(f"/api/settings/users/{admin.id}", json={"is_active": False}).status_code == 400
    assert db.query(UserRole).filter(UserRole.user_id == admin.id).count() == 1


def test_empty_section_has_no_placeholder_values():
    section = Section[list[DeviceRecord]](status="not_configured", message="No data connected yet")
    assert section.data is None
