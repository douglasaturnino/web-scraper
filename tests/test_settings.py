"""Configuration tests."""

import pytest

from src.config.settings import Settings


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify default configuration values."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    settings = Settings()
    assert settings.max_concurrent_requests == 4
    assert settings.min_delay == 3.0
    assert settings.max_delay == 7.0
    assert settings.max_retries == 3
    assert settings.request_timeout == 20
    assert settings.job_retention_days == 90
    assert settings.scheduler_hours == ["12:00", "15:00", "18:00"]


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify settings loaded from environment variables."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("MAX_CONCURRENT_REQUESTS", "8")
    monkeypatch.setenv("MIN_DELAY", "1.0")
    monkeypatch.setenv("MAX_DELAY", "5.0")
    monkeypatch.setenv("MAX_RETRIES", "5")
    monkeypatch.setenv("REQUEST_TIMEOUT", "30")
    monkeypatch.setenv("JOB_RETENTION_DAYS", "60")
    monkeypatch.setenv("SCHEDULER_HOURS", '["09:00", "18:00"]')
    settings = Settings()
    assert settings.database_url == "postgresql://test:test@localhost:5432/test"
    assert settings.max_concurrent_requests == 8
    assert settings.min_delay == 1.0
    assert settings.max_delay == 5.0
    assert settings.max_retries == 5
    assert settings.request_timeout == 30
    assert settings.job_retention_days == 60
    assert settings.scheduler_hours == ["09:00", "18:00"]
