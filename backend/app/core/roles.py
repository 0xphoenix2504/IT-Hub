EXECUTIVE = "executive"
IT_MANAGER = "it_manager"
SYSTEM_ADMIN = "system_admin"
NETWORK_ADMIN = "network_admin"
HELPDESK = "helpdesk"

ALL_ROLES = (IT_MANAGER, SYSTEM_ADMIN, NETWORK_ADMIN, HELPDESK, EXECUTIVE)
GROUP_ROLES = (IT_MANAGER, SYSTEM_ADMIN, NETWORK_ADMIN, HELPDESK)
FIXED_EXECUTIVE_GROUP = "executives"

ROLE_LABELS = {
    IT_MANAGER: "IT Manager",
    SYSTEM_ADMIN: "System Admin",
    NETWORK_ADMIN: "Network Admin",
    HELPDESK: "Helpdesk",
    EXECUTIVE: "Executive",
}


def sort_roles(roles: list[str] | set[str]) -> list[str]:
    order = {role: index for index, role in enumerate(ALL_ROLES)}
    return sorted(set(roles), key=lambda role: order.get(role, 99))


def clean_group_name(value: str) -> str | None:
    name = value.strip().lower()
    if not name or len(name) > 128:
        return None
    if any(ord(char) < 32 or char in ",=+" for char in name):
        return None
    return name
