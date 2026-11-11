from datetime import datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict

from app.text import EMPTY_MESSAGE, ERROR_MESSAGE

T = TypeVar("T")


class Section(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "not_configured", "error"]
    message: str | None = None
    last_updated: datetime | None = None
    data: T | None = None


class ServiceHealth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    state: Literal["up", "degraded", "down"]
    availability_30d: float


class TicketStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    open_now: int
    closed_this_month: int
    closed_last_month: int
    avg_resolution_hours: float
    avg_resolution_hours_last_month: float | None = None


class AssetStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_devices: int
    total_servers: int
    nearing_end_of_life: int


class ProblemStat(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    count: int


class DeviceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    kind: Literal["server", "network", "endpoint"]
    status: Literal["up", "degraded", "down", "unknown"]
    ip: str | None = None
    hostname: str | None = None


class DeepLinks(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticketing: str | None = None
    assets: str | None = None


class ExecutiveDashboard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    service_health: Section[list[ServiceHealth]]
    tickets: Section[TicketStats]
    assets: Section[AssetStats]
    top_problems: Section[list[ProblemStat]]


class TechnicalDashboard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    tickets: Section[TicketStats]
    problems: Section[list[ProblemStat]]
    devices: Section[list[DeviceRecord]]
    links: DeepLinks


class Me(BaseModel):
    username: str
    display_name: str
    roles: list[str]
    auth_provider: str


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    provider: str
    is_active: bool
    roles: list[str]


class MappingOut(BaseModel):
    id: int
    ad_group: str
    role: str


class ServiceOut(BaseModel):
    id: int
    name: str
    external_key: str
    sort_order: int


class AuditOut(BaseModel):
    id: int
    created_at: datetime
    actor: str
    action: str
    detail: str
    ip: str | None


class ConnectionOut(BaseModel):
    key: str
    label: str
    configured: bool
    note: str


class LoginBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    password: str


class MappingBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ad_group: str
    role: str


class ServiceBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    external_key: str


class UserBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    password: str
    display_name: str = ""
    roles: list[str]


class UserPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = None
    password: str | None = None
    is_active: bool | None = None
    roles: list[str] | None = None


def empty_section() -> Section[Any]:
    return Section(status="not_configured", message=EMPTY_MESSAGE)


def error_section() -> Section[Any]:
    return Section(status="error", message=ERROR_MESSAGE)
