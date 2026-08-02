"""Metrics endpoint."""

from fastapi import APIRouter
from loguru import logger

from src.config.metrics import get_metrics
from src.schemas.scraper import MetricsResponse

router = APIRouter()


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics_endpoint() -> dict[str, dict[str, dict[str, int]]]:
    """Return basic metrics about provider executions.

    Returns:
        dict[str, dict[str, dict[str, int]]]: Metrics per provider.
    """
    logger.info("Metrics requested")
    return get_metrics()
