"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application configuration.

    All values are loaded from environment variables or ``.env`` file.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = ""

    max_concurrent_requests: int = 4
    min_delay: float = 3.0
    max_delay: float = 7.0
    max_retries: int = 3
    request_timeout: int = 20
    job_retention_days: int = 90
    scheduler_hours: list[str] = ["12:00", "15:00", "18:00"]


def get_settings() -> Settings:
    """Return application settings instance."""
    return Settings()
