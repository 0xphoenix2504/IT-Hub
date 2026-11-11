from abc import ABC, abstractmethod

from app.models import CriticalService
from app.schemas import AssetStats, DeviceRecord, ProblemStat, Section, ServiceHealth, TicketStats


class TicketingAdapter(ABC):
    @abstractmethod
    def configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def summary(self, scope: str) -> Section[TicketStats]:
        raise NotImplementedError

    @abstractmethod
    def top_problems(self, scope: str, limit: int = 5) -> Section[list[ProblemStat]]:
        raise NotImplementedError


class AssetsAdapter(ABC):
    @abstractmethod
    def configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def summary(self) -> Section[AssetStats]:
        raise NotImplementedError

    @abstractmethod
    def devices(self, kind: str) -> Section[list[DeviceRecord]]:
        raise NotImplementedError


class MonitorAdapter(ABC):
    @abstractmethod
    def configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def service_health(self, services: list[CriticalService]) -> Section[list[ServiceHealth]]:
        raise NotImplementedError

    @abstractmethod
    def devices(self, kind: str) -> Section[list[DeviceRecord]]:
        raise NotImplementedError


class SsoHandoff(ABC):
    """A future protocol can subclass this. Nothing here signs a user into another system."""

    @abstractmethod
    def configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def start(self, username: str, target: str) -> Section[str]:
        raise NotImplementedError
