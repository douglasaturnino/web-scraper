"""Implementação do provedor LinkedIn."""

import asyncio
import random
import re
import time
from collections.abc import Mapping
from urllib.parse import quote

from aiohttp import ClientError, ClientTimeout
from aiohttp import ClientSession as AiohttpClientSession
from bs4 import BeautifulSoup, Tag
from loguru import logger

from src.config.settings import get_settings
from src.database.models.vacancy import Vacancy
from src.providers.base import BaseProvider

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


class LinkedinProvider(BaseProvider):
    """Provider for LinkedIn job listings."""

    def __init__(self) -> None:
        """Initialize provider with default settings."""
        self._base_url = "https://www.linkedin.com/jobs/search"

    def search(
        self,
        keyword: str,
        state: str,
        municipality: str,
    ) -> list[Vacancy]:
        """Search for vacancies on LinkedIn.

        Args:
            keyword (str): Search keyword.
            state (str): State filter.
            municipality (str): Municipality filter.

        Returns:
            list[Vacancy]: Found vacancies.
        """
        logger.info(
            "Starting LinkedIn search keyword={} state={} municipality={}",
            keyword,
            state,
            municipality,
        )
        start = time.monotonic()
        result = asyncio.run(self._search_async(keyword, state, municipality))
        elapsed = time.monotonic() - start
        logger.info(
            "LinkedIn search completed in {:.2f}s | vacancies={}",
            elapsed,
            len(result),
        )
        return result

    async def _search_async(
        self,
        keyword: str,
        state: str,
        municipality: str,
    ) -> list[Vacancy]:
        """Async search implementation.

        Args:
            keyword (str): Search keyword.
            state (str): State filter.
            municipality (str): Municipality filter.

        Returns:
            list[Vacancy]: Found vacancies.
        """
        location = f"{state}, {municipality}" if municipality else state

        vacancies: list[Vacancy] = []
        start = 0

        async with AiohttpClientSession() as session:
            all_cards: list[Tag] = []
            for _page in range(3):
                url = self._build_search_url(keyword, location, start)
                html = await self._fetch_with_retry(session, url)
                if not html:
                    logger.warning(
                        "Failed to fetch search page for keyword={} location={}",
                        keyword,
                        location,
                    )
                    break

                soup = BeautifulSoup(html, "html.parser")
                job_cards = soup.find_all("div", {"class": "job-search-card"})

                if not job_cards:
                    break

                all_cards.extend(job_cards)
                start += 25

            semaphore = asyncio.Semaphore(get_settings().max_concurrent_requests)

            async def _process_card(card: Tag) -> Vacancy | None:
                try:
                    raw = self._parse_job_card(card)
                    url = str(raw.get("url") or "")
                    if url:
                        async with semaphore:
                            detail_html = await self._fetch_with_retry(session, url)
                        if detail_html:
                            raw = self._parse_detail_page(detail_html, raw)
                    return self.normalize(raw)
                except Exception:
                    logger.exception("Error parsing job card on LinkedIn search")
                    return None

            tasks = [_process_card(card) for card in all_cards]
            results = await asyncio.gather(*tasks)
            vacancies = [r for r in results if r is not None]

        logger.info(
            "LinkedIn search completed for keyword={} | vacancies={}",
            keyword,
            len(vacancies),
        )
        return vacancies

    def _build_search_url(self, keyword: str, location: str, start: int) -> str:
        """Build LinkedIn search URL.

        Args:
            keyword (str): Search keyword.
            location (str): Location string.
            start (int): Pagination offset.

        Returns:
            str: Full search URL.
        """
        encoded_keyword = quote(keyword)
        encoded_location = quote(location)
        return (
            f"{self._base_url}?f_TPR=r86400"
            f"&keywords={encoded_keyword}"
            f"&location={encoded_location}%2C%20Brazil"
            f"&start={start}"
        )

    async def _fetch_with_retry(
        self, session: AiohttpClientSession, url: str
    ) -> str | None:
        """Fetch URL with retry logic.

        Args:
            session (AiohttpClientSession): aiohttp client session.
            url (str): URL to fetch.

        Returns:
            str | None: HTML content or None on failure.
        """
        for attempt in range(1, get_settings().max_retries + 1):
            ua = random.choice(USER_AGENTS)  # noqa: S311
            headers = {
                "User-Agent": ua,
                "Accept-Language": "en-US,en;q=0.9",
            }
            try:
                timeout = ClientTimeout(total=get_settings().request_timeout)
                async with session.get(url, headers=headers, timeout=timeout) as resp:
                    status = resp.status
                    text: str = await resp.text(errors="ignore")
                    if status == 200:
                        await asyncio.sleep(
                            random.uniform(  # noqa: S311
                                get_settings().min_delay,
                                get_settings().max_delay,
                            )
                        )
                        return text
                    logger.warning(
                        "Status {} for {} (attempt {})",
                        status,
                        url,
                        attempt,
                    )
            except TimeoutError:
                logger.warning("Timeout on attempt {} for {}", attempt, url)
            except ClientError as exc:
                logger.error(
                    "aiohttp error on attempt {} for {}: {}",
                    attempt,
                    url,
                    exc,
                )
            except Exception as exc:
                logger.exception(
                    "Unexpected error on attempt {} for {}: {}",
                    attempt,
                    url,
                    exc,
                )

            await asyncio.sleep(
                random.uniform(  # noqa: S311
                    get_settings().min_delay,
                    get_settings().max_delay,
                )
                * attempt
            )

        logger.error("Failed after {} attempts: {}", get_settings().max_retries, url)
        return None

    def _parse_job_card(self, card: Tag) -> dict[str, object]:
        """Extract data from a LinkedIn job card element.

        Args:
            card (Tag): BeautifulSoup element representing a job card.

        Returns:
            dict[str, object]: Raw job data.
        """
        title = None
        company = None
        location_text = None
        href_link = None

        try:
            title_el = card.find("h3", {"class": "base-search-card__title"})
            if title_el:
                title = title_el.text.strip()
        except Exception:
            logger.exception("Error parsing job card title")

        try:
            company_el = card.find("a", {"class": "hidden-nested-link"})
            if company_el:
                company = company_el.text.strip()
        except Exception:
            logger.exception("Error parsing job card company")

        try:
            location_el = card.find("span", {"class": "job-search-card__location"})
            if location_el:
                location_text = location_el.text.strip()
        except Exception:
            logger.exception("Error parsing job card location")

        try:
            link_el = card.find("a", class_="base-card__full-link")
            if link_el and link_el.has_attr("href"):
                href_link = link_el["href"]
        except Exception:
            logger.exception("Error parsing job card link")

        return {
            "title": title,
            "company": company,
            "location": location_text,
            "url": href_link,
            "description": None,
        }

    def _parse_detail_page(
        self, html: str, raw: Mapping[str, object]
    ) -> dict[str, object]:
        """Extract description from a LinkedIn job detail page.

        Args:
            html (str): HTML content of the detail page.
            raw (Mapping[str, object]): Existing raw data to update.

        Returns:
            dict[str, object]: Updated raw job data.
        """
        mutable_raw = dict(raw)
        try:
            soup = BeautifulSoup(html, "html.parser")
            desc_el = soup.find("div", {"class": "show-more-less-html__markup"})
            if desc_el:
                mutable_raw["description"] = desc_el.get_text(strip=True)
        except Exception:
            logger.exception("Error parsing LinkedIn detail page")

        return mutable_raw

    def get_job(self, url: str) -> Vacancy | None:
        """Fetch a single vacancy by LinkedIn URL.

        Args:
            url (str): LinkedIn job URL.

        Returns:
            Vacancy | None: Found vacancy or None.
        """
        logger.info("Starting LinkedIn get_job url={}", url)
        start = time.monotonic()
        result = asyncio.run(self._get_job_async(url))
        elapsed = time.monotonic() - start
        logger.info("LinkedIn get_job completed in {:.2f}s", elapsed)
        return result

    async def _get_job_async(self, url: str) -> Vacancy | None:
        """Async get_job implementation.

        Args:
            url (str): LinkedIn job URL.

        Returns:
            Vacancy | None: Found vacancy or None.
        """
        clean_url = self._clean_url(url)
        external_id = self._extract_external_id(clean_url)

        async with AiohttpClientSession() as session:
            html = await self._fetch_with_retry(session, clean_url)
            if not html:
                logger.warning("Failed to fetch job detail page: {}", clean_url)
                return None

            raw: dict[str, object] = {
                "title": None,
                "company": None,
                "location": None,
                "url": clean_url,
                "external_id": external_id,
                "description": None,
            }

            try:
                soup = BeautifulSoup(html, "html.parser")

                title_el = soup.find("h1", {"class": "top-card__title"})
                if not title_el:
                    title_el = soup.find(
                        "h1", {"class": "jobs-unified-top-card__job-title"}
                    )
                if title_el:
                    raw["title"] = title_el.text.strip()

                company_el = soup.find("a", {"class": "hidden-nested-link"})
                if not company_el:
                    company_el = soup.find(
                        "span",
                        {"class": "top-card__company-name"},
                    )
                if company_el:
                    raw["company"] = company_el.text.strip()

                location_el = soup.find("span", {"class": "job-search-card__location"})
                if not location_el:
                    location_el = soup.find(
                        "span",
                        {"class": "top-card__flavor"},
                    )
                if location_el:
                    raw["location"] = location_el.text.strip()

                raw = self._parse_detail_page(html, raw)

            except Exception:
                logger.exception("Error parsing LinkedIn job detail page")

            return self.normalize(raw)

    @staticmethod
    def _clean_url(url: str) -> str:
        """Remove query parameters from a URL.

        Args:
            url (str): Raw URL.

        Returns:
            str: URL without query string.
        """
        if "?" in url:
            url = url.split("?")[0]
        return url.rstrip("/")

    @staticmethod
    def _extract_external_id(url: str) -> str:
        """Extract the external ID from a LinkedIn job URL.

        Args:
            url (str): Clean LinkedIn job URL.

        Returns:
            str: External ID extracted from the URL.
        """
        path = url.rstrip("/")
        last_segment = path.split("/")[-1]
        match = re.search(r"(\d+)$", last_segment)
        if match:
            return match.group(1)
        return last_segment

    def normalize(self, raw_data: Mapping[str, object]) -> Vacancy:
        """Normalize raw LinkedIn data into a Vacancy.

        Args:
            raw_data (Mapping[str, object]): Raw job data from LinkedIn.

        Returns:
            Vacancy: Normalized vacancy entity.
        """
        from datetime import UTC, datetime

        url = str(raw_data.get("url") or "")
        external_id = str(raw_data.get("external_id") or "")

        if not external_id and url:
            external_id = self._extract_external_id(self._clean_url(url))

        location = str(raw_data.get("location") or "")
        state, municipality = self._parse_location(location)

        return Vacancy(
            provider="linkedin",
            external_id=external_id,
            company=str(raw_data.get("company") or ""),
            title=str(raw_data.get("title") or ""),
            url=self._clean_url(url),
            publication_date=datetime.now(UTC),
            state=state,
            municipality=municipality,
            description=str(raw_data.get("description") or ""),
        )

    @staticmethod
    def _parse_location(
        location: str,
    ) -> tuple[str, str]:
        """Parse location string into state and municipality.

        Args:
            location (str): Location string from LinkedIn.

        Returns:
            tuple[str, str]: (state, municipality).
        """
        if not location:
            return ("", "")

        normalized = location.strip()
        if normalized.lower() == "remoto":
            return ("Remoto", "Remoto")

        parts = [p.strip() for p in normalized.split(",")]
        if len(parts) >= 3:
            return (parts[-2], parts[-3])
        if len(parts) == 2:
            return (parts[-1], parts[-2])
        if len(parts) == 1:
            return (parts[0], parts[0])
        return ("", "")
