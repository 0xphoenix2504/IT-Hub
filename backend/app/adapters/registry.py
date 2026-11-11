from app.adapters.base import AssetsAdapter, MonitorAdapter, SsoHandoff, TicketingAdapter
from app.adapters.http_adapters import (
    HttpAssetsAdapter,
    HttpMonitorAdapter,
    HttpTicketingAdapter,
)
from app.adapters.unconfigured import (
    UnconfiguredAssets,
    UnconfiguredMonitor,
    UnconfiguredSso,
    UnconfiguredTicketing,
)
from app.core.config import get_settings


def ticketing() -> TicketingAdapter:
    settings = get_settings()
    if settings.ticketing_api_url.strip():
        return HttpTicketingAdapter(settings.ticketing_api_url, settings.ticketing_api_token)
    return UnconfiguredTicketing()


def assets() -> AssetsAdapter:
    settings = get_settings()
    if settings.assets_api_url.strip():
        return HttpAssetsAdapter(settings.assets_api_url, settings.assets_api_token)
    return UnconfiguredAssets()


def monitor() -> MonitorAdapter:
    settings = get_settings()
    if settings.monitor_api_url.strip():
        return HttpMonitorAdapter(settings.monitor_api_url, settings.monitor_api_token)
    return UnconfiguredMonitor()


def sso() -> SsoHandoff:
    # Deep links are separate. This handoff stays unconfigured until a real protocol exists.
    return UnconfiguredSso()
