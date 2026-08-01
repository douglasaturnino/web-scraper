"""Implementação do provedor Gupy."""

import asyncio
import math
import random
import re
import time
from collections.abc import Mapping
from typing import Any

from aiohttp import ClientError, ClientTimeout
from aiohttp import ClientSession as AiohttpClientSession
from loguru import logger

from src.config.settings import get_settings
from src.database.models.vacancy import Vacancy
from src.providers.base import BaseProvider


class GupyProvider(BaseProvider):
    """Provider for Gupy job listings."""

    def __init__(self) -> None:
        """Initialize provider with default settings."""
        self._base_url = "https://employability-portal.gupy.io/api/v1/jobs"
        self._headers = {
            "sec-ch-ua": '"Not/A)Brand";v="24", "Chromium";v="143", "Google Chrome";v="143"',
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://portal.gupy.io/",
            "sec-ch-ua-mobile": "?0",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "sec-ch-ua-platform": '"Linux"',
        }

    def search(
        self,
        keyword: str,
        state: str,
        municipality: str,
    ) -> list[Vacancy]:
        """Search for vacancies on Gupy.

        Args:
            keyword (str): Search keyword.
            state (str): State filter (ignored by Gupy).
            municipality (str): Municipality filter (ignored by Gupy).

        Returns:
            list[Vacancy]: Found vacancies.
        """
        logger.info("Starting Gupy search keyword={}", keyword)
        start = time.monotonic()
        result = asyncio.run(self._search_async(keyword))
        elapsed = time.monotonic() - start
        logger.info(
            "Gupy search completed in {:.2f}s | vacancies={}",
            elapsed,
            len(result),
        )
        return result

    async def _search_async(self, keyword: str) -> list[Vacancy]:
        """Async search implementation.

        Args:
            keyword (str): Search keyword.

        Returns:
            list[Vacancy]: Found vacancies.
        """
        limit = 10
        vacancies: list[Vacancy] = []

        async with AiohttpClientSession() as session:
            first_queries: dict[str, str | int] = {
                "jobName": keyword,
                "limit": limit,
                "offset": 0,
            }
            first_result = await self._fetch_api(session, first_queries)

            if not isinstance(first_result, dict) or "data" not in first_result:
                logger.warning(
                    "No data returned for Gupy search keyword={}",
                    keyword,
                )
                return []

            total_jobs = first_result["pagination"]["total"]
            pages = math.ceil(total_jobs / limit)
            logger.info(
                "Gupy search found {} jobs across {} pages",
                total_jobs,
                pages,
            )

            raw_jobs = list(first_result["data"])

            if pages > 1:
                semaphore = asyncio.Semaphore(get_settings().max_concurrent_requests)

                async def _fetch_page(
                    queries: dict[str, str | int],
                ) -> dict[str, Any] | None:
                    async with semaphore:
                        return await self._fetch_api(session, queries)

                tasks = [
                    _fetch_page(
                        {
                            "jobName": keyword,
                            "limit": limit,
                            "offset": limit * i,
                        }
                    )
                    for i in range(1, pages)
                ]
                results = await asyncio.gather(*tasks)
                for res in results:
                    if isinstance(res, dict) and "data" in res:
                        raw_jobs.extend(res["data"])

            for raw in raw_jobs:
                try:
                    vacancy = self.normalize(raw)
                    vacancies.append(vacancy)
                except Exception:
                    logger.exception(
                        "Error normalizing Gupy vacancy for keyword={}",
                        keyword,
                    )

        logger.info(
            "Gupy search completed for keyword={} | vacancies={}",
            keyword,
            len(vacancies),
        )
        return vacancies

    async def _fetch_api(
        self, session: AiohttpClientSession, queries: dict[str, str | int]
    ) -> dict[str, Any] | None:
        """Fetch Gupy API with retry logic.

        Args:
            session (AiohttpClientSession): aiohttp client session.
            queries (dict[str, str | int]): Query parameters.

        Returns:
            dict[str, Any] | None: API response or None on failure.
        """
        for attempt in range(1, get_settings().max_retries + 1):
            try:
                timeout = ClientTimeout(total=get_settings().request_timeout)
                async with session.get(
                    self._base_url,
                    headers=self._headers,
                    params=queries,
                    timeout=timeout,
                ) as resp:
                    status = resp.status
                    if status == 200:
                        data = await resp.json()
                        await asyncio.sleep(
                            random.uniform(  # noqa: S311
                                get_settings().min_delay,
                                get_settings().max_delay,
                            )
                        )
                        return dict(data)
                    logger.warning(
                        "Status {} for Gupy API (attempt {})",
                        status,
                        attempt,
                    )
            except TimeoutError:
                logger.warning("Timeout on attempt {} for Gupy API", attempt)
            except ClientError as exc:
                logger.error(
                    "aiohttp error on attempt {} for Gupy API: {}",
                    attempt,
                    exc,
                )
            except Exception as exc:
                logger.exception(
                    "Unexpected error on attempt {} for Gupy API: {}",
                    attempt,
                    exc,
                )

            await asyncio.sleep(
                random.uniform(  # noqa: S311
                    get_settings().min_delay,
                    get_settings().max_delay,
                )
                * attempt
            )

        logger.error(
            "Failed after {} attempts for Gupy API", get_settings().max_retries
        )
        return None

    def normalize(self, raw_data: Mapping[str, object]) -> Vacancy:
        """Normalize raw Gupy data into a Vacancy.

        Args:
            raw_data (Mapping[str, object]): Raw job data from Gupy.

        Returns:
            Vacancy: Normalized vacancy entity.
        """
        from datetime import UTC, datetime

        url = str(raw_data.get("url") or raw_data.get("jobUrl") or "")
        external_id = str(raw_data.get("external_id") or raw_data.get("id") or "")

        if not external_id and url:
            external_id = self._extract_external_id(self._clean_url(url))

        is_remote = bool(raw_data.get("isRemoteWork", False))

        if is_remote:
            state = "Remoto"
            municipality = "Remoto"
        else:
            state = str(raw_data.get("state") or "")
            city = str(raw_data.get("city") or "")
            municipality = city if city else "Brasil"

        pub_date = raw_data.get("publishedDate")
        if pub_date:
            try:
                publication_date = datetime.fromisoformat(
                    str(pub_date).replace("Z", "+00:00")
                )
            except ValueError, TypeError:
                publication_date = datetime.now(UTC)
        else:
            publication_date = datetime.now(UTC)

        return Vacancy(
            provider="gupy",
            external_id=external_id,
            company=str(
                raw_data.get("company") or raw_data.get("careerPageName") or ""
            ),
            title=str(raw_data.get("title") or raw_data.get("name") or ""),
            url=self._clean_url(url),
            publication_date=publication_date,
            state=state,
            municipality=municipality,
            description=str(raw_data.get("description") or ""),
        )

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
        """Extract the external ID from a Gupy job URL.

        Args:
            url (str): Clean Gupy job URL.

        Returns:
            str: External ID extracted from the URL.
        """
        path = url.rstrip("/")
        last_segment = path.split("/")[-1]
        match = re.search(r"(\d+)$", last_segment)
        if match:
            return match.group(1)
        return last_segment if last_segment else ""
