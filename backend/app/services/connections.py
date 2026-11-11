from app.adapters import registry
from app.schemas import ConnectionOut
from app.services.dashboard import deep_links


def connection_status() -> list[ConnectionOut]:
    links = deep_links()
    return [
        ConnectionOut(
            key="ticketing_api",
            label="Ticketing read API",
            configured=registry.ticketing().configured(),
            note="The ticketing system does not have a read API connected yet.",
        ),
        ConnectionOut(
            key="assets_api",
            label="Assets read API",
            configured=registry.assets().configured(),
            note="The assets system does not have a read API connected yet.",
        ),
        ConnectionOut(
            key="monitor",
            label="Network monitor",
            configured=registry.monitor().configured(),
            note="No monitor product is selected. The adapter interface is in place.",
        ),
        ConnectionOut(
            key="sso",
            label="Single sign-on handoff",
            configured=registry.sso().configured(),
            note="The handoff interface is in place. No sign-in protocol is configured.",
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
