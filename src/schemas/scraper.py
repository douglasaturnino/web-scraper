"""Pydantic schemas for scraper API requests and responses."""

from pydantic import BaseModel, HttpUrl


class SearchByProviderRequest(BaseModel):
    """Request body for POST /scraper/search."""

    provider: str
    keyword: str
    state: str
    municipality: str


class SearchByUrlRequest(BaseModel):
    """Request body for POST /scraper/url."""

    url: HttpUrl


class CreateSearchRequest(BaseModel):
    """Request body for POST /scraper/search/create."""

    provider: str
    keyword: str
    state: str
    municipality: str
    active: bool = True


class CreateSearchResponse(BaseModel):
    """Response for POST /scraper/search/create."""

    id: str
    provider: str
    keyword: str
    state: str
    municipality: str
    active: bool


class SchedulerRunResponse(BaseModel):
    """Response for POST /scraper/run."""

    searches: int
    vacancies: int


class SearchByProviderResponse(BaseModel):
    """Response for POST /scraper/search."""

    provider: str
    vacancies_found: int


class SearchByUrlResponse(BaseModel):
    """Response for POST /scraper/url."""

    id: str
    provider: str
    title: str
    company: str
    url: str
    state: str
    municipality: str


class HealthCheckResponse(BaseModel):
    """Response for GET /health."""

    status: str


class MetricsResponse(BaseModel):
    """Response for GET /metrics."""

    providers: dict[str, dict[str, int]]
