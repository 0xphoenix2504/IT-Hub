from app.adapters.base import AssetsAdapter, MonitorAdapter, SsoHandoff, TicketingAdapter
from app.schemas import empty_section


class UnconfiguredTicketing(TicketingAdapter):
    def configured(self) -> bool:
        return False

    def summary(self, scope: str):
        return empty_section()

    def top_problems(self, scope: str, limit: int = 5):
        return empty_section()


class UnconfiguredAssets(AssetsAdapter):
    def configured(self) -> bool:
        return False

    def summary(self):
        return empty_section()

    def devices(self, kind: str):
        return empty_section()


class UnconfiguredMonitor(MonitorAdapter):
    def configured(self) -> bool:
        return False

    def service_health(self, services):
        return empty_section()

    def devices(self, kind: str):
        return empty_section()


class UnconfiguredSso(SsoHandoff):
    def configured(self) -> bool:
        return False

    def start(self, username: str, target: str):
        return empty_section()
