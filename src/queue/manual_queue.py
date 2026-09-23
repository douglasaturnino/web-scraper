"""Manual URL queue for processing individual vacancy URLs."""

import collections.abc
from collections import deque
from typing import ClassVar
from urllib.parse import urlparse

from loguru import logger

from src.database.models.vacancy import Vacancy
from src.providers.factory import ProviderFactory
from src.services.scraper_service import ScraperService


class ManualQueue:
    """Queue for manual URL-based vacancy collection."""

    PROVIDER_DOMAIN_MAP: ClassVar[dict[str, str]] = {
        "linkedin.com": "linkedin",
        "gupy.io": "gupy",
        "portal.gupy.io": "gupy",
        "employability-portal.gupy.io": "gupy",
    }

    def __init__(
        self,
        scraper_service: ScraperService,
        provider_factory: ProviderFactory,
    ) -> None:
        """Initialize queue with dependencies.

        Args:
            scraper_service (ScraperService): Service for persisting vacancies.
            provider_factory (ProviderFactory): Factory for provider retrieval.
        """
        self._queue: collections.deque[str] = deque()
        self._scraper_service = scraper_service
        self._provider_factory = provider_factory

    def enqueue(self, url: str) -> None:
        """Add a URL to the processing queue.

        Args:
            url (str): Vacancy URL to process.
        """
        self._queue.append(url)
        logger.info("URL enqueued: {}", url)

    def enqueue_batch(self, urls: list[str]) -> None:
        """Add multiple URLs to the processing queue.

        Args:
            urls (list[str]): List of vacancy URLs to process.
        """
        for url in urls:
            self.enqueue(url)

    def _resolve_provider(self, url: str) -> str | None:
        """Determine the provider from a URL's domain.

        Args:
            url (str): Vacancy URL.

        Returns:
            str | None: Provider name or None if domain is unsupported.
        """
        domain = urlparse(url).netloc
        if domain in self.PROVIDER_DOMAIN_MAP:
            return self.PROVIDER_DOMAIN_MAP[domain]
        for suffix, provider in self.PROVIDER_DOMAIN_MAP.items():
            if domain.endswith("." + suffix) or domain == suffix:
                return provider
        return None

    def process_next(self) -> Vacancy | None:
        """Process the next URL in the queue.

        Returns:
            Vacancy | None: The persisted vacancy, or None if the URL
            could not be processed (unsupported provider, fetch failure,
            or duplicate).
        """
        if not self._queue:
            return None

        url = self._queue.popleft()
        provider_name = self._resolve_provider(url)

        if provider_name is None:
            logger.warning("Unsupported provider domain for URL: {}", url)
            return None

        try:
            provider = self._provider_factory.get(provider_name)
        except ValueError:
            logger.warning(
                "Provider '{}' not registered for URL {}",
                provider_name,
                url,
            )
            return None

        vacancy = provider.get_job(url)
        if vacancy is None:
            logger.warning("Failed to fetch vacancy from URL: {}", url)
            return None

        saved, _ = self._scraper_service._vacancy_service.save_vacancies([vacancy])
        if saved:
            logger.info("Vacancy persisted from URL: {}", url)
            return saved[0]
        else:
            logger.info("Vacancy ignored as duplicate from URL: {}", url)
            return None

    def process_all(self) -> list[Vacancy]:
        """Process all URLs in the queue.

        Returns:
            list[Vacancy]: List of persisted vacancies.
        """
        vacancies: list[Vacancy] = []
        while True:
            vacancy = self.process_next()
            if vacancy is None:
                break
            vacancies.append(vacancy)
        return vacancies

    @property
    def size(self) -> int:
        """Return the current queue size.

        Returns:
            int: Number of URLs waiting in the queue.
        """
        return len(self._queue)
