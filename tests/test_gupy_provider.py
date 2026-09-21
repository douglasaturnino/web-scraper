"""Gupy provider tests."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientError

from src.providers.gupy import GupyProvider


def _provider() -> GupyProvider:
    return GupyProvider()


def test_normalize_minimal_data() -> None:
    """Verify normalize works with minimal raw data."""
    provider = _provider()
    raw = {
        "name": "Python Developer",
        "careerPageName": "Acme Corp",
        "state": "SP",
        "city": "São Paulo",
        "jobUrl": "https://jobs.gupy.io/acme/job/123456",
        "description": "Develop Python applications.",
        "publishedDate": "2026-07-29T02:03:26.208Z",
    }
    vacancy = provider.normalize(raw)

    assert vacancy.provider == "gupy"
    assert vacancy.external_id == "123456"
    assert vacancy.company == "Acme Corp"
    assert vacancy.title == "Python Developer"
    assert vacancy.url == "https://jobs.gupy.io/acme/job/123456"
    assert vacancy.state == "SP"
    assert vacancy.municipality == "São Paulo"
    assert vacancy.description == "Develop Python applications."
    assert vacancy.publication_date is not None


def test_normalize_remote_work() -> None:
    """Verify normalize handles remote work."""
    provider = _provider()
    raw = {
        "name": "Remote Developer",
        "careerPageName": "Remote Corp",
        "isRemoteWork": True,
        "jobUrl": "https://jobs.gupy.io/remote/job/999",
        "description": "Work remotely.",
        "publishedDate": "2026-07-29T02:03:26.208Z",
    }
    vacancy = provider.normalize(raw)

    assert vacancy.state == "Remoto"
    assert vacancy.municipality == "Remoto"


def test_normalize_empty_city_defaults_to_brasil() -> None:
    """Verify normalize defaults municipality to Brasil when city is empty."""
    provider = _provider()
    raw = {
        "name": "Developer",
        "careerPageName": "Some Corp",
        "state": "RJ",
        "city": "",
        "jobUrl": "https://jobs.gupy.io/some/job/111",
        "description": "Code.",
        "publishedDate": "2026-07-29T02:03:26.208Z",
    }
    vacancy = provider.normalize(raw)

    assert vacancy.state == "RJ"
    assert vacancy.municipality == "Brasil"


def test_normalize_none_city_defaults_to_brasil() -> None:
    """Verify normalize defaults municipality to Brasil when city is None."""
    provider = _provider()
    raw = {
        "name": "Developer",
        "careerPageName": "Some Corp",
        "state": "RJ",
        "city": None,
        "jobUrl": "https://jobs.gupy.io/some/job/111",
        "description": "Code.",
        "publishedDate": "2026-07-29T02:03:26.208Z",
    }
    vacancy = provider.normalize(raw)

    assert vacancy.municipality == "Brasil"


def test_normalize_parses_published_date() -> None:
    """Verify normalize parses publishedDate correctly."""
    provider = _provider()
    raw = {
        "name": "Developer",
        "careerPageName": "Some Corp",
        "state": "SP",
        "city": "São Paulo",
        "jobUrl": "https://jobs.gupy.io/some/job/111",
        "description": "Code.",
        "publishedDate": "2026-07-29T02:03:26.208Z",
    }
    vacancy = provider.normalize(raw)

    assert vacancy.publication_date is not None
    assert vacancy.publication_date.year == 2026
    assert vacancy.publication_date.month == 7
    assert vacancy.publication_date.day == 29


def test_normalize_invalid_published_date_uses_now() -> None:
    """Verify normalize uses current time for invalid publishedDate."""
    provider = _provider()
    raw = {
        "name": "Developer",
        "careerPageName": "Some Corp",
        "state": "SP",
        "city": "São Paulo",
        "jobUrl": "https://jobs.gupy.io/some/job/111",
        "description": "Code.",
        "publishedDate": "invalid-date",
    }
    vacancy = provider.normalize(raw)

    assert vacancy.publication_date is not None
    assert vacancy.publication_date.year == 2026


def test_normalize_missing_published_date_uses_now() -> None:
    """Verify normalize uses current time when publishedDate is missing."""
    provider = _provider()
    raw = {
        "name": "Developer",
        "careerPageName": "Some Corp",
        "state": "SP",
        "city": "São Paulo",
        "jobUrl": "https://jobs.gupy.io/some/job/111",
        "description": "Code.",
    }
    vacancy = provider.normalize(raw)

    assert vacancy.publication_date is not None
    assert vacancy.publication_date.year == 2026


def test_normalize_uses_name_as_title_fallback() -> None:
    """Verify normalize uses name when title is missing."""
    provider = _provider()
    raw = {
        "name": "Data Scientist",
        "careerPageName": "Tech Corp",
        "state": "RJ",
        "city": "Rio de Janeiro",
        "jobUrl": "https://jobs.gupy.io/tech/job/222",
        "description": "Analyze data.",
        "publishedDate": "2026-07-29T02:03:26.208Z",
    }
    vacancy = provider.normalize(raw)

    assert vacancy.title == "Data Scientist"


def test_normalize_uses_career_page_name_as_company_fallback() -> None:
    """Verify normalize uses careerPageName when company is missing."""
    provider = _provider()
    raw = {
        "name": "Developer",
        "careerPageName": "Acme",
        "state": "SP",
        "city": "São Paulo",
        "jobUrl": "https://jobs.gupy.io/acme/job/333",
        "description": "Code.",
        "publishedDate": "2026-07-29T02:03:26.208Z",
    }
    vacancy = provider.normalize(raw)

    assert vacancy.company == "Acme"


def test_normalize_no_external_id_in_url() -> None:
    """Verify normalize handles URL with no numeric ID."""
    provider = _provider()
    raw = {
        "name": "Designer",
        "careerPageName": "Design Co",
        "state": "SP",
        "city": "São Paulo",
        "jobUrl": "https://jobs.gupy.io/design/job/some-job-title",
        "description": "Design things.",
        "publishedDate": "2026-07-29T02:03:26.208Z",
    }
    vacancy = provider.normalize(raw)

    assert vacancy.external_id == "some-job-title"


def test_normalize_with_none_values() -> None:
    """Verify normalize handles None values in raw data."""
    provider = _provider()
    raw = {
        "name": None,
        "careerPageName": None,
        "state": None,
        "city": None,
        "jobUrl": None,
        "description": None,
    }
    vacancy = provider.normalize(raw)

    assert vacancy.provider == "gupy"
    assert vacancy.title == ""
    assert vacancy.company == ""
    assert vacancy.url == ""
    assert vacancy.description == ""
    assert vacancy.state == ""
    assert vacancy.municipality == "Brasil"


def test_clean_url_removes_query_params() -> None:
    """Verify _clean_url strips query parameters."""
    url = "https://jobs.gupy.io/acme/job/123?position=3&pageNum=0"
    assert GupyProvider._clean_url(url) == "https://jobs.gupy.io/acme/job/123"


def test_clean_url_no_query_params() -> None:
    """Verify _clean_url leaves clean URLs unchanged."""
    url = "https://jobs.gupy.io/acme/job/123"
    assert GupyProvider._clean_url(url) == url


def test_clean_url_trailing_slash() -> None:
    """Verify _clean_url strips trailing slash."""
    url = "https://jobs.gupy.io/acme/job/123/"
    assert GupyProvider._clean_url(url) == "https://jobs.gupy.io/acme/job/123"


def test_extract_external_id_from_url() -> None:
    """Verify external ID extraction from Gupy URL."""
    url = "https://jobs.gupy.io/acme/job/123456"
    assert GupyProvider._extract_external_id(url) == "123456"


def test_extract_external_id_from_hybrid_slug() -> None:
    """Verify external ID extraction from URL with text prefix."""
    url = "https://jobs.gupy.io/acme/job/python-developer-123456"
    assert GupyProvider._extract_external_id(url) == "123456"


def test_extract_external_id_fallback() -> None:
    """Verify external ID fallback when no digits found."""
    url = "https://jobs.gupy.io/acme/job/some-job-title"
    assert GupyProvider._extract_external_id(url) == "some-job-title"


def test_extract_external_id_empty_url() -> None:
    """Verify external ID extraction from empty URL."""
    assert GupyProvider._extract_external_id("") == ""


def test_search_returns_list() -> None:
    """Verify search returns a list when network fails."""
    provider = _provider()
    with patch.object(provider, "_search_async", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = []
        result = provider.search("Python", "SP", "São Paulo")
    assert isinstance(result, list)


def test_search_async_with_mocked_api_response() -> None:
    """Verify _search_async parses jobs from API response."""
    provider = _provider()
    api_response = {
        "data": [
            {
                "id": "1",
                "name": "Python Dev",
                "careerPageName": "Tech Corp",
                "state": "SP",
                "city": "São Paulo",
                "jobUrl": "https://jobs.gupy.io/tech/job/1",
                "description": "Python role.",
                "publishedDate": "2026-07-29T02:03:26.208Z",
            },
            {
                "id": "2",
                "name": "Data Scientist",
                "careerPageName": "Data Corp",
                "state": "RJ",
                "city": "Rio de Janeiro",
                "jobUrl": "https://jobs.gupy.io/data/job/2",
                "description": "Data role.",
                "publishedDate": "2026-07-29T02:03:26.208Z",
            },
        ],
        "pagination": {"total": 2},
    }

    async def mock_fetch(*args: object, **kwargs: object) -> dict[str, object]:
        return api_response

    with patch.object(provider, "_fetch_api", side_effect=mock_fetch):
        vacancies = asyncio.run(provider._search_async("Python"))

    assert len(vacancies) == 2
    assert vacancies[0].title == "Python Dev"
    assert vacancies[0].company == "Tech Corp"
    assert vacancies[0].external_id == "1"
    assert vacancies[1].title == "Data Scientist"


def test_search_async_with_no_results() -> None:
    """Verify _search_async returns empty list when no data."""
    provider = _provider()

    async def mock_fetch(*args: object, **kwargs: object) -> dict[str, object] | None:
        return None

    with patch.object(provider, "_fetch_api", side_effect=mock_fetch):
        vacancies = asyncio.run(provider._search_async("Python"))

    assert vacancies == []


def test_search_async_with_empty_data() -> None:
    """Verify _search_async returns empty list when data is empty."""
    provider = _provider()
    api_response = {"data": [], "pagination": {"total": 0}}

    async def mock_fetch(*args: object, **kwargs: object) -> dict[str, object]:
        return api_response

    with patch.object(provider, "_fetch_api", side_effect=mock_fetch):
        vacancies = asyncio.run(provider._search_async("Python"))

    assert vacancies == []


def test_search_async_handles_normalize_error() -> None:
    """Verify _search_async continues when normalize raises."""
    provider = _provider()
    api_response = {
        "data": [
            {
                "id": "1",
                "name": "Python Dev",
                "careerPageName": "Tech Corp",
                "state": "SP",
                "city": "São Paulo",
                "jobUrl": "https://jobs.gupy.io/tech/job/1",
                "description": "Python role.",
                "publishedDate": "2026-07-29T02:03:26.208Z",
            },
        ],
        "pagination": {"total": 1},
    }

    async def mock_fetch(*args: object, **kwargs: object) -> dict[str, object]:
        return api_response

    with (
        patch.object(provider, "_fetch_api", side_effect=mock_fetch),
        patch.object(provider, "normalize", side_effect=RuntimeError("boom")),
    ):
        vacancies = asyncio.run(provider._search_async("Python"))

    assert vacancies == []


def test_fetch_api_handles_timeout() -> None:
    """Verify _fetch_api retries on TimeoutError."""
    provider = _provider()

    mock_settings = MagicMock()
    mock_settings.max_retries = 2
    mock_settings.request_timeout = 1
    mock_settings.min_delay = 0
    mock_settings.max_delay = 0

    mock_response = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={"data": [], "pagination": {"total": 0}}
    )

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.get = MagicMock(side_effect=[TimeoutError(), mock_response])

    with (
        patch("src.providers.gupy.get_settings", return_value=mock_settings),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        result = asyncio.run(provider._fetch_api(mock_session, {"jobName": "Python"}))

    assert result is not None
    assert result["pagination"]["total"] == 0
    assert mock_session.get.call_count == 2


def test_fetch_api_handles_client_error() -> None:
    """Verify _fetch_api retries on ClientError."""
    provider = _provider()

    mock_settings = MagicMock()
    mock_settings.max_retries = 2
    mock_settings.request_timeout = 1
    mock_settings.min_delay = 0
    mock_settings.max_delay = 0

    mock_response = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={"data": [], "pagination": {"total": 0}}
    )

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.get = MagicMock(side_effect=[ClientError("boom"), mock_response])

    with (
        patch("src.providers.gupy.get_settings", return_value=mock_settings),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        result = asyncio.run(provider._fetch_api(mock_session, {"jobName": "Python"}))

    assert result is not None


def test_fetch_api_returns_none_after_max_attempts() -> None:
    """Verify _fetch_api returns None after exhausting retries."""
    provider = _provider()

    mock_settings = MagicMock()
    mock_settings.max_retries = 2
    mock_settings.request_timeout = 1
    mock_settings.min_delay = 0
    mock_settings.max_delay = 0

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.get = MagicMock(side_effect=ClientError("boom"))

    with (
        patch("src.providers.gupy.get_settings", return_value=mock_settings),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        result = asyncio.run(provider._fetch_api(mock_session, {"jobName": "Python"}))

    assert result is None
    assert mock_session.get.call_count == 2


def test_provider_implements_base_provider() -> None:
    """Verify GupyProvider implements BaseProvider protocol."""
    from src.providers.base import BaseProvider

    provider = _provider()
    assert isinstance(provider, BaseProvider)
