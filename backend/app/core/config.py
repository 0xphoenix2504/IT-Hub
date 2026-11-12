from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def as_int(value: str, default: int) -> int:
    text = value.strip()
    if not text:
        return default
    return int(text)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_PATH, extra="ignore")

    app_env: str = ""
    database_url: str = ""
    cors_origin: str = ""
    auth_provider: str = ""
    session_ttl_hours: str = ""
    cookie_secure: str = ""
    cookie_samesite: str = ""
    cookie_name: str = "it_hub_session"
    login_max_attempts: str = ""
    login_lockout_minutes: str = ""
    password_iterations: str = ""
    first_admin_username: str = ""
    first_admin_password: str = ""
    first_admin_display_name: str = ""
    ldaps_url: str = ""
    ldaps_base_dn: str = ""
    ldaps_user_dn_template: str = ""
    ldaps_user_filter: str = ""
    ldaps_bind_dn: str = ""
    ldaps_bind_password: str = ""
    ticketing_app_base_url: str = ""
    assets_app_base_url: str = ""
    ticketing_api_url: str = ""
    ticketing_api_token: str = ""
    assets_api_url: str = ""
    assets_api_token: str = ""
    monitor_api_url: str = ""
    monitor_api_token: str = ""
    stats_cache_seconds: str = ""
    trust_proxy: str = ""

    @property
    def environment(self) -> str:
        value = self.app_env.strip().lower()
        return value or "development"

    @property
    def provider(self) -> str:
        value = self.auth_provider.strip().lower()
        return value or "local"

    @property
    def ttl_seconds(self) -> int:
        return as_int(self.session_ttl_hours, 8) * 3600

    @property
    def proxy_trusted(self) -> bool:
        return self.trust_proxy.strip().lower() in {"1", "true", "yes"}

    @property
    def secure_cookie(self) -> bool:
        if self.samesite == "none":
            return True
        raw = self.cookie_secure.strip().lower()
        if not raw:
            return self.environment == "production"
        return raw in {"1", "true", "yes"}

    @property
    def samesite(self) -> str:
        value = self.cookie_samesite.strip().lower() or "lax"
        if value not in {"lax", "strict", "none"}:
            return "lax"
        return value

    @property
    def max_attempts(self) -> int:
        return as_int(self.login_max_attempts, 5)

    @property
    def lockout_minutes(self) -> int:
        return as_int(self.login_lockout_minutes, 15)

    @property
    def iterations(self) -> int:
        return as_int(self.password_iterations, 600_000)

    @property
    def cache_seconds(self) -> int:
        return as_int(self.stats_cache_seconds, 60)

    @property
    def origin(self) -> str:
        return self.cors_origin.strip().rstrip("/")

    @property
    def origins(self) -> list[str]:
        raw = self.cors_origin.strip()
        if not raw:
            return []
        return [item.strip().rstrip("/") for item in raw.split(",") if item.strip()]

    @property
    def user_filter(self) -> str:
        value = self.ldaps_user_filter.strip()
        return value or "(sAMAccountName={username})"


@lru_cache
def get_settings() -> Settings:
    return Settings()
