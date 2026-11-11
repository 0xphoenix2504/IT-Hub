from app.adapters import registry
from app.schemas import ConnectionOut
from app.services.dashboard import deep_links


def connection_status() -> list[ConnectionOut]:
    links = deep_links()
    ticketing_cfg = registry.ticketing().configured()
    assets_cfg = registry.assets().configured()
    monitor_cfg = registry.monitor().configured()
    sso_cfg = registry.sso().configured()

    return [
        ConnectionOut(
            key="ticketing_api",
            label="Ticketing read API",
            configured=ticketing_cfg,
            note="Connected to external ticketing system." if ticketing_cfg else "The ticketing system does not have a read API connected yet.",
        ),
        ConnectionOut(
            key="assets_api",
            label="Assets read API",
            configured=assets_cfg,
            note="Connected to external assets system." if assets_cfg else "The assets system does not have a read API connected yet.",
        ),
        ConnectionOut(
            key="monitor",
            label="Network monitor",
            configured=monitor_cfg,
            note="Connected to external network monitor." if monitor_cfg else "No monitor product is selected. The adapter interface is in place.",
        ),
        ConnectionOut(
            key="sso",
            label="Single sign-on handoff",
            configured=sso_cfg,
            note="Configured for SSO handoff." if sso_cfg else "The handoff interface is in place. No sign-in protocol is configured.",
        ),
        ConnectionOut(
            key="ticketing_link",
            label="Ticketing deep link",
            configured=links.ticketing is not None,
            note="Opens the ticketing system. It does not sign the user in.",
        ),
        ConnectionOut(
            key="assets_link",
            label="Assets deep link",
            configured=links.assets is not None,
            note="Opens the assets system. It does not sign the user in.",
        ),
    ]
