"""Loguru configuration for the application."""

import os

from loguru import logger as logger

from src.config.settings import get_settings


def configure_logging() -> None:
    """Configure Loguru with daily rotation and standard format."""
    os.makedirs("logs", exist_ok=True)
    settings = get_settings()
    logger.remove()
    logger.add(
        "logs/app.log",
        rotation="1 day",
        retention=f"{settings.job_retention_days} days",
        encoding="utf-8",
        level="INFO",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
        ),
    )
    logger.add(
        lambda msg: print(msg, end=""),
        level="INFO",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
        ),
    )
