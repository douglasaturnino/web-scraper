"""Schemas package."""

from src.schemas.scraper import (
    CreateSearchRequest,
    CreateSearchResponse,
    HealthCheckResponse,
    MetricsResponse,
    SchedulerRunResponse,
    SearchByProviderRequest,
    SearchByProviderResponse,
    SearchByUrlRequest,
    SearchByUrlResponse,
)

__all__ = [
    "CreateSearchRequest",
    "CreateSearchResponse",
    "HealthCheckResponse",
    "MetricsResponse",
    "SchedulerRunResponse",
    "SearchByProviderRequest",
    "SearchByProviderResponse",
    "SearchByUrlRequest",
    "SearchByUrlResponse",
]
