import httpx
import pytest

from app.adapters import registry
from app.adapters.http_adapters import (
    HttpAssetsAdapter,
    HttpMonitorAdapter,
    HttpTicketingAdapter,
)
from app.core.config import get_settings
from app.models import CriticalService


def test_http_ticketing_adapter_unconfigured():
    adapter = HttpTicketingAdapter(base_url="")
    assert adapter.configured() is False
    summary = adapter.summary("all")
    assert summary.status == "not_configured"
    assert summary.data is None
    problems = adapter.top_problems("all")
    assert problems.status == "not_configured"
    assert problems.data is None


def test_http_ticketing_adapter_success(monkeypatch):
    def fake_handler(request: httpx.Request) -> httpx.Response:
        if "/api/stats/all" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "open_now": 12,
                    "closed_this_month": 45,
                    "closed_last_month": 40,
                    "avg_resolution_hours": 3.5,
                    "avg_resolution_hours_last_month": 4.0,
                },
            )
        if "/api/problems/all" in str(request.url):
            return httpx.Response(
                200,
                json=[
                    {"label": "VPN Connection", "count": 15},
                    {"label": "Password Reset", "count": 10},
                ],
            )
        return httpx.Response(404)

    orig_client = httpx.Client
    transport = httpx.MockTransport(fake_handler)
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: orig_client(transport=transport))

    adapter = HttpTicketingAdapter(base_url="https://tickets.internal", token="secret")
    assert adapter.configured() is True
    summary = adapter.summary("all")
    assert summary.status == "ok"
    assert summary.data is not None
    assert summary.data.open_now == 12
    assert summary.data.closed_this_month == 45

    problems = adapter.top_problems("all")
    assert problems.status == "ok"
    assert len(problems.data or []) == 2
    assert problems.data[0].label == "VPN Connection"


def test_http_ticketing_adapter_error(monkeypatch):
    def fake_handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Error")

    orig_client = httpx.Client
    transport = httpx.MockTransport(fake_handler)
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: orig_client(transport=transport))

    adapter = HttpTicketingAdapter(base_url="https://tickets.internal")
    summary = adapter.summary("all")
    assert summary.status == "error"
    assert summary.data is None


def test_http_assets_adapter_success(monkeypatch):
    def fake_handler(request: httpx.Request) -> httpx.Response:
        if "/api/assets/summary" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "total_devices": 150,
                    "total_servers": 25,
                    "nearing_end_of_life": 8,
                },
            )
        if "/api/assets/devices/server" in str(request.url):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "srv-01",
                        "name": "DB Primary",
                        "kind": "server",
                        "status": "up",
                        "ip": "192.168.1.10",
                        "hostname": "db1.local",
                    }
                ],
            )
        return httpx.Response(404)

    orig_client = httpx.Client
    transport = httpx.MockTransport(fake_handler)
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: orig_client(transport=transport))

    adapter = HttpAssetsAdapter(base_url="https://assets.internal")
    assert adapter.configured() is True
    summary = adapter.summary()
    assert summary.status == "ok"
    assert summary.data is not None
    assert summary.data.total_devices == 150

    devices = adapter.devices("server")
    assert devices.status == "ok"
    assert len(devices.data or []) == 1
    assert devices.data[0].name == "DB Primary"


def test_http_monitor_adapter_success(monkeypatch):
    def fake_handler(request: httpx.Request) -> httpx.Response:
        if "/api/monitor/services" in str(request.url):
            return httpx.Response(
                200,
                json=[
                    {
                        "name": "Active Directory",
                        "state": "up",
                        "availability_30d": 99.9,
                    }
                ],
            )
        return httpx.Response(404)

    orig_client = httpx.Client
    transport = httpx.MockTransport(fake_handler)
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: orig_client(transport=transport))

    adapter = HttpMonitorAdapter(base_url="https://monitor.internal")
    assert adapter.configured() is True
    services = [CriticalService(id=1, name="Active Directory", external_key="ad", sort_order=1)]
    health = adapter.service_health(services)
    assert health.status == "ok"
    assert len(health.data or []) == 1
    assert health.data[0].name == "Active Directory"
    assert health.data[0].state == "up"


def test_registry_picks_http_when_env_configured(monkeypatch):
    monkeypatch.setenv("TICKETING_API_URL", "https://tickets.company")
    monkeypatch.setenv("ASSETS_API_URL", "https://assets.company")
    monkeypatch.setenv("MONITOR_API_URL", "https://monitor.company")
    get_settings.cache_clear()

    assert isinstance(registry.ticketing(), HttpTicketingAdapter)
    assert registry.ticketing().configured() is True
    assert isinstance(registry.assets(), HttpAssetsAdapter)
    assert registry.assets().configured() is True
    assert isinstance(registry.monitor(), HttpMonitorAdapter)
    assert registry.monitor().configured() is True

    get_settings.cache_clear()
