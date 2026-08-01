"""Scheduler module for orchestrating job searches."""

from src.services.scraper_service import ScraperService


class Scheduler:
    """Orchestrates the execution of active job searches."""

    def __init__(self, scraper_service: ScraperService) -> None:
        """Initialize scheduler with scraper service.

        Args:
            scraper_service (ScraperService): Scraper service instance.
        """
        self._scraper_service = scraper_service

    def run(self) -> dict[str, int]:
        """Execute all eligible searches and persist results.

        Returns:
            dict[str, int]: Execution metrics.
        """
        return self._scraper_service.run_scheduler()
