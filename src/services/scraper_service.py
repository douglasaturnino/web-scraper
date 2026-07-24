"""Scraper service to orchestrate collection flow."""

from loguru import logger

from src.database.models.job_search import JobSearch
from src.database.models.vacancy import Vacancy
from src.providers.base import BaseProvider
from src.services.search_service import SearchService
from src.services.vacancy_service import VacancyService


class ScraperService:
    """Service responsible for orchestrating the collection flow."""

    def __init__(
        self,
        search_service: SearchService,
        vacancy_service: VacancyService,
        providers: dict[str, BaseProvider],
    ) -> None:
        """Initialize service with dependencies.

        Args:
            search_service (SearchService): Search business rules.
            vacancy_service (VacancyService): Vacancy business rules.
            providers (dict[str, BaseProvider]): Available providers.
        """
        self._search_service = search_service
        self._vacancy_service = vacancy_service
        self._providers = providers

    def execute_search(self, search: JobSearch, provider_name: str) -> list[Vacancy]:
        """Execute a single search on a provider and persist results.

        Args:
            search (JobSearch): Job search to execute.
            provider_name (str): Provider name.

        Returns:
            list[Vacancy]: Persisted vacancies.
        """
        provider = self._providers.get(provider_name)
        if provider is None:
            logger.warning(
                "Provider {} not found for search {}",
                provider_name,
                search.id,
            )
            return []

        logger.info(
            "Executing search {} on provider {}",
            search.id,
            provider_name,
        )

        try:
            vacancies = provider.search(
                keyword=search.keyword,
                state=search.state,
                municipality=search.municipality,
                remote=search.remote,
            )
        except Exception:
            logger.exception(
                "Error executing search {} on provider {}",
                search.id,
                provider_name,
            )
            return []

        saved, _ = self._vacancy_service.save_vacancies(vacancies)
        logger.info(
            "Search {} completed on provider {} - saved: {}",
            search.id,
            provider_name,
            len(saved),
        )
        return saved

    def execute_by_url(self, url: str, provider_name: str) -> Vacancy | None:
        """Execute a manual single vacancy collection by URL.

        Args:
            url (str): Vacancy URL.
            provider_name (str): Provider name.

        Returns:
            Vacancy | None: Persisted vacancy or None.
        """
        provider = self._providers.get(provider_name)
        if provider is None:
            logger.warning(
                "Provider {} not found for manual URL",
                provider_name,
            )
            return None

        try:
            vacancy = provider.get_job(url)
        except Exception:
            logger.exception(
                "Error fetching vacancy by URL on provider {}",
                provider_name,
            )
            return None

        if vacancy is None:
            return None

        saved, _ = self._vacancy_service.save_vacancies([vacancy])
        return saved[0] if saved else None

    def run_scheduler(self) -> dict[str, int]:
        """Execute all eligible searches and persist results.

        Returns:
            dict[str, int]: Execution metrics.
        """
        searches = self._search_service.get_elegible_searches()
        metrics: dict[str, int] = {"searches": 0, "vacancies": 0}

        if not searches:
            logger.info("No active searches found")
            return metrics

        logger.info("Starting scheduler with {} searches", len(searches))

        for search in searches:
            if not self._search_service.is_search_elegible(search):
                logger.info("Search {} is not eligible, skipping", search.id)
                continue

            metrics["searches"] += 1
            providers = self._search_service.get_providers_for_search(search.id)

            for provider_assoc in providers:
                if not provider_assoc.active:
                    continue

                saved = self.execute_search(search, provider_assoc.provider)
                metrics["vacancies"] += len(saved)

        logger.info(
            "Scheduler finished - searches: {} | vacancies: {}",
            metrics["searches"],
            metrics["vacancies"],
        )
        return metrics
