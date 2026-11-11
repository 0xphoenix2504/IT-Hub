import logging

from ldap3 import BASE, SUBTREE, Connection, Server
from ldap3.core.exceptions import LDAPException
from ldap3.utils.conv import escape_filter_chars
from sqlalchemy.orm import Session

from app.auth.base import AuthResult
from app.core.config import get_settings
from app.core.roles import FIXED_EXECUTIVE_GROUP, sort_roles
from app.core.security import utcnow
from app.models import RoleMapping, User, UserRole

log = logging.getLogger(__name__)


def group_names_from_dns(values) -> set[str]:
    names: set[str] = set()
    for dn in values or []:
        text = str(dn)
        for part in text.split(","):
            rdn = part.strip()
            if rdn.lower().startswith("cn="):
                names.add(rdn[3:].strip().lower())
                break
    return names


def roles_for_groups(db: Session, names: set[str]) -> list[str]:
    roles: set[str] = set()
    if FIXED_EXECUTIVE_GROUP in names:
        roles.add("executive")
    for mapping in db.query(RoleMapping).all():
        if mapping.ad_group.lower() in names:
            roles.add(mapping.role)
    return sort_roles(roles)


def _display_name(entry, username: str) -> str:
    value = None
    if entry is not None and "displayName" in entry:
        raw = entry["displayName"].value
        if isinstance(raw, list):
            value = raw[0] if raw else None
        else:
            value = raw
    text = str(value).strip() if value else ""
    return text or username


class LdapsAuth:
    provider_name = "ldaps"

    def configured(self) -> bool:
        settings = get_settings()
        url_ok = settings.ldaps_url.strip().lower().startswith("ldaps://")
        base_ok = bool(settings.ldaps_base_dn.strip())
        can_find = bool(settings.ldaps_user_dn_template.strip()) or (
            bool(settings.ldaps_bind_dn.strip()) and bool(settings.ldaps_bind_password)
        )
        return url_ok and base_ok and can_find and "{username}" in settings.user_filter

    def authenticate(self, db: Session, username: str, password: str) -> AuthResult:
        if not password:
            return AuthResult(ok=False, reason="invalid")
        if not self.configured():
            log.error("LDAPS settings are incomplete")
            return AuthResult(ok=False, reason="unavailable")
        try:
            names, display = self._bind_and_groups(username, password)
        except LDAPException:
            log.exception("LDAPS sign-in failed")
            return AuthResult(ok=False, reason="invalid")
        except OSError:
            log.exception("LDAPS connection failed")
            return AuthResult(ok=False, reason="unavailable")
        roles = roles_for_groups(db, names)
        if not roles:
            return AuthResult(ok=False, reason="no_role", username=username, display_name=display)
        self._remember(db, username, display, roles)
        return AuthResult(ok=True, username=username, display_name=display, roles=roles, provider="ldaps")

    def _server(self) -> Server:
        settings = get_settings()
        return Server(settings.ldaps_url.strip(), use_ssl=True, connect_timeout=5, get_info=None)

    def _search(self, conn: Connection, username: str):
        settings = get_settings()
        query = settings.user_filter.replace("{username}", escape_filter_chars(username))
        conn.search(
            settings.ldaps_base_dn.strip(),
            query,
            search_scope=SUBTREE,
            attributes=["memberOf", "displayName"],
            size_limit=2,
        )
        if len(conn.entries) != 1:
            return None
        entry = conn.entries[0]
        member = entry.entry_attributes_as_dict.get("memberOf", [])
        return entry.entry_dn, group_names_from_dns(member), _display_name(entry, username)

    def _bind_and_groups(self, username: str, password: str):
        settings = get_settings()
        server = self._server()
        if settings.ldaps_bind_dn.strip() and settings.ldaps_bind_password:
            service = Connection(
                server,
                user=settings.ldaps_bind_dn.strip(),
                password=settings.ldaps_bind_password,
                auto_bind=True,
                receive_timeout=5,
            )
            try:
                found = self._search(service, username)
            finally:
                service.unbind()
            if found is None:
                raise LDAPException("directory user was not found")
            user_dn, names, display = found
            user_conn = Connection(server, user=user_dn, password=password, auto_bind=True, receive_timeout=5)
            user_conn.unbind()
            return names, display

        bind_name = settings.ldaps_user_dn_template.replace("{username}", username)
        conn = Connection(server, user=bind_name, password=password, auto_bind=True, receive_timeout=5)
        try:
            found = self._search(conn, username)
            if found is None:
                conn.search(bind_name, "(objectClass=*)", search_scope=BASE, attributes=["memberOf", "displayName"])
                if len(conn.entries) != 1:
                    raise LDAPException("directory groups could not be read")
                entry = conn.entries[0]
                member = entry.entry_attributes_as_dict.get("memberOf", [])
                return group_names_from_dns(member), _display_name(entry, username)
            _dn, names, display = found
            return names, display
        finally:
            conn.unbind()

    def _remember(self, db: Session, username: str, display: str, roles: list[str]) -> None:
        from sqlalchemy import func

        user = db.query(User).filter(func.lower(User.username) == username.lower()).one_or_none()
        now = utcnow()
        if user is None:
            user = User(
                username=username,
                display_name=display,
                password_hash=None,
                provider="ldaps",
                is_active=True,
                created_at=now,
            )
            db.add(user)
            db.flush()
        user.display_name = display
        user.provider = "ldaps"
        user.password_hash = None
        user.is_active = True
        db.query(UserRole).filter(UserRole.user_id == user.id).delete()
        for role in roles:
            db.add(UserRole(user_id=user.id, role=role))
        db.flush()
