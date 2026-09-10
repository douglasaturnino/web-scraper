"""Logger configuration tests."""

import pytest
from loguru import logger as logger

from src.config.logger import configure_logging


def test_configure_logging_adds_sinks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify configure_logging adds file and console sinks."""
    calls: list[int] = []

    def mock_add(*args: object, **kwargs: object) -> int:
        calls.append(1)
        return 0

    monkeypatch.setattr(logger, "add", mock_add)
    configure_logging()
    assert sum(calls) == 2


def test_logger_is_importable_from_config_module() -> None:
    """Verify global logger is accessible from config module."""
    from loguru import logger as loguru_logger

    from src.config.logger import logger as config_logger

    assert config_logger is loguru_logger
