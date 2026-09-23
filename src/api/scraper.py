"""Scraper endpoints for manual execution and URL-based collection."""

import uuid

from fastapi import APIRouter, HTTPException
from loguru import logger

from src.database.models.job_search import JobSearch
from src.database.models.job_search_provider import JobSearchProvider
from src.database.session import SessionLocal
from src.providers.factory import ProviderFactory
from src.providers.gupy import GupyProvider
from src.providers.linkedin import LinkedinProvider
from src.queue.manual_queue import ManualQueue
from src.repositories.job_search_provider_repository import (
    JobSearchProviderRepository,
)
from src.repositories.search_repository import SearchRepository
from src.repositories.vacancy_repository import VacancyRepository
from src.schemas.scraper import (
    CreateSearchRequest,
    CreateSearchResponse,
    SchedulerRunResponse,
    SearchByProviderRequest,
    SearchByProviderResponse,
    SearchByUrlRequest,
    SearchByUrlResponse,
)
from src.services.scraper_service import ScraperService
from src.services.search_service import SearchService
from src.services.vacancy_service import VacancyService

router = APIRouter()


def _build_scraper_service() -> tuple[ScraperService, ProviderFactory]:
    """Build a ScraperService and ProviderFactory with fresh database session.

    Returns:
        tuple[ScraperService, ProviderFactory]: Configured service and factory.
    """
    session = SessionLocal()
    try:
        search_repo = SearchRepository(session)
        provider_repo = JobSearchProviderRepository(session)
        vacancy_repo = VacancyRepository(session)
        search_service = SearchService(search_repo, provider_repo)
        vacancy_service = VacancyService(vacancy_repo)
        provider_factory = ProviderFactory()
        provider_factory.register("linkedin", LinkedinProvider())
        provider_factory.register("gupy", GupyProvider())
        return ScraperService(
            search_service, vacancy_service, provider_factory
        ), provider_factory
    except Exception:
        session.close()
        raise


@router.post("/scraper/run", response_model=SchedulerRunResponse)
def run_scheduler() -> SchedulerRunResponse:
    """Execute all eligible searches and persist results.

    Returns:
        SchedulerRunResponse: Execution metrics with searches and vacancies count.
    """
    logger.info("Manual scheduler execution requested")
    scraper_service, _ = _build_scraper_service()
    metrics = scraper_service.run_scheduler()
    return SchedulerRunResponse(**metrics)


@router.post("/scraper/search", response_model=SearchByProviderResponse)
def search_by_provider(
    request: SearchByProviderRequest,
) -> SearchByProviderResponse:
    """Execute a manual search on a specific provider.

    Args:
        request (SearchByProviderRequest): Search parameters.

    Returns:
        SearchByProviderResponse: Result with provider name and vacancies found.
    """
    logger.info(
        "Manual search requested provider={} keyword={}",
        request.provider,
        request.keyword,
    )
    scraper_service, _ = _build_scraper_service()
    search = JobSearch(
        keyword=request.keyword,
        state=request.state,
        municipality=request.municipality,
        active=True,
    )
    saved = scraper_service.execute_search(search, request.provider)
    return SearchByProviderResponse(
        provider=request.provider,
        vacancies_found=len(saved),
    )


@router.post("/scraper/url", response_model=SearchByUrlResponse)
def search_by_url(request: SearchByUrlRequest) -> SearchByUrlResponse:
    """Fetch a single vacancy by URL and persist it.

    Args:
        request (SearchByUrlRequest): URL request body.

    Returns:
        SearchByUrlResponse: The persisted vacancy details.

    Raises:
        HTTPException: If the provider is not supported or the vacancy
            cannot be fetched.
    """
    logger.info("Manual URL search requested: {}", request.url)
    scraper_service, provider_factory = _build_scraper_service()

    queue = ManualQueue(scraper_service, provider_factory)
    queue.enqueue(str(request.url))
    vacancies = queue.process_all()

    if not vacancies:
        raise HTTPException(
            status_code=400,
            detail="Provider não suportado ou vaga não encontrada",
        )

    vacancy = vacancies[0]
    return SearchByUrlResponse(
        id=str(vacancy.id),
        provider=vacancy.provider,
        title=vacancy.title,
        company=vacancy.company,
        url=vacancy.url,
        state=vacancy.state,
        municipality=vacancy.municipality,
    )


@router.post("/scraper/search/create", response_model=CreateSearchResponse)
def create_search(
    request: CreateSearchRequest,
) -> CreateSearchResponse:
    """Create a new shared search and associate it with a provider.

    Args:
        request (CreateSearchRequest): Search parameters.

    Returns:
        CreateSearchResponse: The created search details.
    """
    logger.info(
        "Creating search provider={} keyword={}",
        request.provider,
        request.keyword,
    )
    # The id is generated explicitly (client-side) so the provider
    # association can reference it before either object is written to the
    # database — SQLAlchemy column defaults only apply at flush time.
    search = JobSearch(
        id=uuid.uuid4(),
        keyword=request.keyword,
        state=request.state,
        municipality=request.municipality,
        active=request.active,
    )
    search_provider = JobSearchProvider(
        search_id=search.id,
        provider=request.provider,
        active=request.active,
    )

    session = SessionLocal()
    try:
        search_repo = SearchRepository(session)
        provider_repo = JobSearchProviderRepository(session)
        search_repo.add(search)
        provider_repo.add(search_provider)
        # Single transaction: both INSERTs are flushed together, so the
        # search and its provider association either both persist or both
        # roll back (no orphaned searches on failure).
        session.commit()

        return CreateSearchResponse(
            id=str(search.id),
            provider=request.provider,
            keyword=request.keyword,
            state=request.state,
            municipality=request.municipality,
            active=request.active,
        )
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
