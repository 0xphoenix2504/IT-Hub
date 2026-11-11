import logging
from typing import Any

import httpx

from app.adapters.base import AssetsAdapter, MonitorAdapter, TicketingAdapter
from app.core.security import utcnow
from app.models import CriticalService
from app.schemas import (
    AssetStats,
    DeviceRecord,
    ProblemStat,
    Section,
    ServiceHealth,
    TicketStats,
    error_section,
)

log = logging.getLogger(__name__)

TIMEOUT_SECONDS = 5.0


def _build_headers(token: str) -> dict[str, str]:
    headers = {"Accept": "application/json", "User-Agent": "IT-Hub-Adapter/1.0"}
    if token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"
    return headers


class HttpTicketingAdapter(TicketingAdapter):
    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.strip().rstrip("/")
        self.token = token.strip()

    def configured(self) -> bool:
        return bool(self.base_url)

    def summary(self, scope: str) -> Section[TicketStats]:
        if not self.configured():
            return Section(status="not_configured", message="No data connected yet")
        url = f"{self.base_url}/api/stats/{scope}"
        try:
            with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
                res = client.get(url, headers=_build_headers(self.token))
                res.raise_for_status()
                payload = res.json()
                stats = TicketStats.model_validate(payload)
                return Section(status="ok", data=stats, last_updated=utcnow())
        except Exception as exc:
            log.warning("Ticketing API summary request failed for %s: %s", url, exc)
            return Section(status="error", message="Ticketing system is currently unreachable")

    def top_problems(self, scope: str, limit: int = 5) -> Section[list[ProblemStat]]:
        if not self.configured():
            return Section(status="not_configured", message="No data connected yet")
        url = f"{self.base_url}/api/problems/{scope}"
        try:
            with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
                res = client.get(url, params={"limit": limit}, headers=_build_headers(self.token))
                res.raise_for_status()
                payload = res.json()
                items = [ProblemStat.model_validate(item) for item in payload]
                return Section(status="ok", data=items, last_updated=utcnow())
        except Exception as exc:
            log.warning("Ticketing API top_problems request failed for %s: %s", url, exc)
            return Section(status="error", message="Ticketing system is currently unreachable")


class HttpAssetsAdapter(AssetsAdapter):
    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.strip().rstrip("/")
        self.token = token.strip()

    def configured(self) -> bool:
        return bool(self.base_url)

    def summary(self) -> Section[AssetStats]:
        if not self.configured():
            return Section(status="not_configured", message="No data connected yet")
        url = f"{self.base_url}/api/assets/summary"
        try:
            with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
                res = client.get(url, headers=_build_headers(self.token))
                res.raise_for_status()
                payload = res.json()
                stats = AssetStats.model_validate(payload)
                return Section(status="ok", data=stats, last_updated=utcnow())
        except Exception as exc:
            log.warning("Assets API summary request failed for %s: %s", url, exc)
            return Section(status="error", message="Assets system is currently unreachable")

    def devices(self, kind: str) -> Section[list[DeviceRecord]]:
        if not self.configured():
            return Section(status="not_configured", message="No data connected yet")
        url = f"{self.base_url}/api/assets/devices/{kind}"
        try:
            with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
                res = client.get(url, headers=_build_headers(self.token))
                res.raise_for_status()
                payload = res.json()
                items = [DeviceRecord.model_validate(item) for item in payload]
                return Section(status="ok", data=items, last_updated=utcnow())
        except Exception as exc:
            log.warning("Assets API devices request failed for %s: %s", url, exc)
            return Section(status="error", message="Assets system is currently unreachable")


class HttpMonitorAdapter(MonitorAdapter):
    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.strip().rstrip("/")
        self.token = token.strip()

    def configured(self) -> bool:
        return bool(self.base_url)

    def service_health(self, services: list[CriticalService]) -> Section[list[ServiceHealth]]:
        if not self.configured():
            return Section(status="not_configured", message="No data connected yet")
        if not services:
            return Section(status="ok", data=[], last_updated=utcnow())
        url = f"{self.base_url}/api/monitor/services"
        keys = [s.external_key for s in services]
        try:
            with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
                res = client.post(url, json={"keys": keys}, headers=_build_headers(self.token))
                res.raise_for_status()
                payload = res.json()
                items = [ServiceHealth.model_validate(item) for item in payload]
                return Section(status="ok", data=items, last_updated=utcnow())
        except Exception as exc:
            log.warning("Monitor API services request failed for %s: %s", url, exc)
            return Section(status="error", message="Network monitor is currently unreachable")

    def devices(self, kind: str) -> Section[list[DeviceRecord]]:
        if not self.configured():
            return Section(status="not_configured", message="No data connected yet")
        url = f"{self.base_url}/api/monitor/devices/{kind}"
        try:
            with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
                res = client.get(url, headers=_build_headers(self.token))
                res.raise_for_status()
                payload = res.json()
                items = [DeviceRecord.model_validate(item) for item in payload]
                return Section(status="ok", data=items, last_updated=utcnow())
        except Exception as exc:
            log.warning("Monitor API devices request failed for %s: %s", url, exc)
            return Section(status="error", message="Network monitor is currently unreachable")
