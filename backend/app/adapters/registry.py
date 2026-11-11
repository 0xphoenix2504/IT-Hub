from app.adapters.base import AssetsAdapter, MonitorAdapter, SsoHandoff, TicketingAdapter
from app.adapters.unconfigured import (
    UnconfiguredAssets,
    UnconfiguredMonitor,
    UnconfiguredSso,
    UnconfiguredTicketing,
)


def ticketing() -> TicketingAdapter:
    # Replace this when the ticketing system has a read API.
    return UnconfiguredTicketing()


def assets() -> AssetsAdapter:
    return UnconfiguredAssets()


def monitor() -> MonitorAdapter:
    # The monitor product is not chosen. Keep this interface-only.
    return UnconfiguredMonitor()


def sso() -> SsoHandoff:
    # Deep links are separate. This handoff stays unconfigured until a real protocol exists.
    return UnconfiguredSso()
