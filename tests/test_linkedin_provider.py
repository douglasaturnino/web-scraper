"""LinkedIn provider tests."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientError
from bs4 import BeautifulSoup, Tag

from src.providers.linkedin import LinkedinProvider


def _provider() -> LinkedinProvider:
    return LinkedinProvider()


def test_normalize_minimal_data() -> None:
    """Verify normalize works with minimal raw data."""
    provider = _provider()
    raw = {
        "title": "Python Developer",
        "company": "Acme Corp",
        "location": "São Paulo, SP",
        "url": "https://br.linkedin.com/jobs/view/123456789",
        "description": "Develop Python applications.",
    }
    vacancy = provider.normalize(raw)

    assert vacancy.provider == "linkedin"
    assert vacancy.external_id == "123456789"
    assert vacancy.company == "Acme Corp"
    assert vacancy.title == "Python Developer"
    assert vacancy.url == "https://br.linkedin.com/jobs/view/123456789"
    assert vacancy.state == "SP"
    assert vacancy.municipality == "São Paulo"
    assert vacancy.description == "Develop Python applications."
    assert vacancy.publication_date is not None


def test_normalize_with_query_params_in_url() -> None:
    """Verify URL cleaning removes query parameters."""
    provider = _provider()
    raw = {
        "title": "Data Scientist",
        "company": "Tech Corp",
        "location": "Rio de Janeiro, RJ",
        "url": (
            "https://br.linkedin.com/jobs/view/"
            "data-scientist-987654321"
            "?position=3&pageNum=0"
        ),
        "description": "Analyze data.",
    }
    vacancy = provider.normalize(raw)

    assert vacancy.url == ("https://br.linkedin.com/jobs/view/data-scientist-987654321")
    assert vacancy.external_id == "987654321"


def test_normalize_remote_location() -> None:
    """Verify normalize handles remote location."""
    provider = _provider()
    raw = {
        "title": "Remote Developer",
        "company": "Remote Corp",
        "location": "Remoto",
        "url": "https://www.linkedin.com/jobs/view/555555555",
        "description": "Work remotely.",
    }
    vacancy = provider.normalize(raw)

    assert vacancy.state == "Remoto"
    assert vacancy.municipality == "Remoto"


def test_normalize_empty_location() -> None:
    """Verify normalize handles empty location."""
    provider = _provider()
    raw = {
        "title": "Developer",
        "company": "Some Corp",
        "location": "",
        "url": "https://www.linkedin.com/jobs/view/111111111",
        "description": "Code.",
    }
    vacancy = provider.normalize(raw)

    assert vacancy.state == ""
    assert vacancy.municipality == ""


def test_normalize_single_location_part() -> None:
    """Verify normalize handles location with only one part."""
    provider = _provider()
    raw = {
        "title": "Designer",
        "company": "Design Co",
        "location": "Brazil",
        "url": "https://www.linkedin.com/jobs/view/222222222",
        "description": "Design things.",
    }
    vacancy = provider.normalize(raw)

    assert vacancy.state == "Brazil"
    assert vacancy.municipality == "Brazil"


def test_normalize_no_external_id_in_url() -> None:
    """Verify normalize handles URL with no numeric ID."""
    provider = _provider()
    raw = {
        "title": "Designer",
        "company": "Design Co",
        "location": "Brazil",
        "url": "https://www.linkedin.com/jobs/view/no-digits-here",
        "description": "Design things.",
    }
    vacancy = provider.normalize(raw)

    assert vacancy.external_id == "no-digits-here"


def test_normalize_with_none_values() -> None:
    """Verify normalize handles None values in raw data."""
    provider = _provider()
    raw = {
        "title": None,
        "company": None,
        "location": None,
        "url": None,
        "description": None,
    }
    vacancy = provider.normalize(raw)

    assert vacancy.provider == "linkedin"
    assert vacancy.title == ""
    assert vacancy.company == ""
    assert vacancy.url == ""
    assert vacancy.description == ""


def test_clean_url_removes_query_params() -> None:
    """Verify _clean_url strips query parameters."""
    url = "https://br.linkedin.com/jobs/view/some-job-4442862289?position=3&pageNum=0"
    assert LinkedinProvider._clean_url(url) == (
        "https://br.linkedin.com/jobs/view/some-job-4442862289"
    )


def test_clean_url_no_query_params() -> None:
    """Verify _clean_url leaves clean URLs unchanged."""
    url = "https://br.linkedin.com/jobs/view/4442862289"
    assert LinkedinProvider._clean_url(url) == url


def test_clean_url_trailing_slash() -> None:
    """Verify _clean_url strips trailing slash."""
    url = "https://br.linkedin.com/jobs/view/4442862289/"
    assert LinkedinProvider._clean_url(url) == (
        "https://br.linkedin.com/jobs/view/4442862289"
    )


def test_extract_external_id_from_url() -> None:
    """Verify external ID extraction from LinkedIn URL."""
    url = "https://br.linkedin.com/jobs/view/4442862289"
    assert LinkedinProvider._extract_external_id(url) == "4442862289"


def test_extract_external_id_from_hybrid_slug() -> None:
    """Verify external ID extraction from URL with text prefix."""
    url = (
        "https://br.linkedin.com/jobs/view/"
        "fbs-associate-analytics-engineer-remote-at-capgemini-4442862289"
    )
    assert LinkedinProvider._extract_external_id(url) == "4442862289"


def test_extract_external_id_fallback() -> None:
    """Verify external ID fallback when no digits found."""
    url = "https://br.linkedin.com/jobs/view/some-job-title"
    assert LinkedinProvider._extract_external_id(url) == "some-job-title"


def test_parse_location_two_parts() -> None:
    """Verify location parsing with state and municipality."""
    state, municipality = LinkedinProvider._parse_location("Rio de Janeiro, RJ")
    assert state == "RJ"
    assert municipality == "Rio de Janeiro"


def test_parse_location_single_part() -> None:
    """Verify location parsing with single part."""
    state, municipality = LinkedinProvider._parse_location("Brazil")
    assert state == "Brazil"
    assert municipality == "Brazil"


def test_parse_location_empty() -> None:
    """Verify location parsing with empty string."""
    state, municipality = LinkedinProvider._parse_location("")
    assert state == ""
    assert municipality == ""


def test_parse_location_three_parts() -> None:
    """Verify location parsing with three comma-separated parts."""
    state, municipality = LinkedinProvider._parse_location(
        "São Paulo, São Paulo, Brazil"
    )
    assert state == "São Paulo"
    assert municipality == "São Paulo"


def test_build_search_url() -> None:
    """Verify _build_search_url constructs correct URL."""
    provider = _provider()
    url = provider._build_search_url("Python", "SP, São Paulo", 0)
    assert "keywords=Python" in url
    assert "location=SP%2C%20S%C3%A3o%20Paulo" in url
    assert "start=0" in url
    assert "f_TPR=r86400" in url


def test_build_search_url_with_remote() -> None:
    """Verify _build_search_url handles remote location."""
    provider = _provider()
    url = provider._build_search_url("Python", "Remoto", 25)
    assert "location=Remoto" in url
    assert "start=25" in url


def test_parse_job_card_with_all_fields() -> None:
    """Verify _parse_job_card extracts all fields."""
    html = """
    <div class="job-search-card">
        <h3 class="base-search-card__title">Python Developer</h3>
        <a class="hidden-nested-link">Acme Corp</a>
        <span class="job-search-card__location">São Paulo, SP</span>
        <a class="base-card__full-link" href="https://br.linkedin.com/jobs/view/123"></a>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", {"class": "job-search-card"})
    assert card is not None
    provider = _provider()
    result = provider._parse_job_card(card)

    assert result["title"] == "Python Developer"
    assert result["company"] == "Acme Corp"
    assert result["location"] == "São Paulo, SP"
    assert result["url"] == "https://br.linkedin.com/jobs/view/123"


def test_parse_job_card_missing_fields() -> None:
    """Verify _parse_job_card handles missing fields gracefully."""
    html = '<div class="job-search-card"></div>'
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", {"class": "job-search-card"})
    assert card is not None
    provider = _provider()
    result = provider._parse_job_card(card)

    assert result["title"] is None
    assert result["company"] is None
    assert result["location"] is None
    assert result["url"] is None


def test_parse_job_card_partial_fields() -> None:
    """Verify _parse_job_card handles partial fields."""
    html = """
    <div class="job-search-card">
        <h3 class="base-search-card__title">Data Scientist</h3>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", {"class": "job-search-card"})
    assert card is not None
    provider = _provider()
    result = provider._parse_job_card(card)

    assert result["title"] == "Data Scientist"
    assert result["company"] is None
    assert result["url"] is None


def test_parse_detail_page_with_description() -> None:
    """Verify _parse_detail_page extracts description."""
    html = """
    <div class="show-more-less-html__markup">
        <p>We are looking for a Python developer.</p>
    </div>
    """
    provider = _provider()
    raw = {"description": None}
    result = provider._parse_detail_page(html, raw)

    assert result["description"] == "We are looking for a Python developer."


def test_parse_detail_page_without_description() -> None:
    """Verify _parse_detail_page handles missing description element."""
    html = "<div>No description here</div>"
    provider = _provider()
    raw = {"description": None}
    result = provider._parse_detail_page(html, raw)

    assert result["description"] is None


def test_parse_detail_page_empty_html() -> None:
    """Verify _parse_detail_page handles empty HTML."""
    provider = _provider()
    raw = {"description": None}
    result = provider._parse_detail_page("", raw)

    assert result["description"] is None


def test_search_returns_list() -> None:
    """Verify search returns a list when network fails."""
    provider = _provider()
    with patch.object(provider, "_search_async", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = []
        result = provider.search("Python", "SP", "São Paulo")
    assert isinstance(result, list)


def test_get_job_returns_none_for_invalid_url() -> None:
    """Verify get_job returns None for unreachable URLs."""
    provider = _provider()
    with patch.object(provider, "_get_job_async", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        result = provider.get_job("https://www.linkedin.com/jobs/view/999999999")
    assert result is None


def test_get_job_returns_none_for_empty_url() -> None:
    """Verify get_job returns None for empty URL."""
    provider = _provider()
    with patch.object(provider, "_get_job_async", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        result = provider.get_job("")
    assert result is None


def test_normalize_uses_external_id_from_url_when_missing() -> None:
    """Verify normalize extracts external_id from URL if not in raw data."""
    provider = _provider()
    raw = {
        "title": "Backend Engineer",
        "company": "Backend Inc",
        "location": "São Paulo, SP",
        "url": "https://www.linkedin.com/jobs/view/123456789",
        "description": "Build APIs.",
    }
    vacancy = provider.normalize(raw)
    assert vacancy.external_id == "123456789"


def test_normalize_url_is_cleaned() -> None:
    """Verify normalize cleans the URL."""
    provider = _provider()
    raw = {
        "title": "Frontend Engineer",
        "company": "Frontend Co",
        "location": "SP, São Paulo",
        "url": ("https://www.linkedin.com/jobs/view/frontend-111222333?refId=abc"),
        "description": "Build UIs.",
    }
    vacancy = provider.normalize(raw)
    assert "?" not in vacancy.url
    assert vacancy.external_id == "111222333"


def test_provider_implements_base_provider() -> None:
    """Verify LinkedinProvider implements BaseProvider protocol."""
    from src.providers.base import BaseProvider

    provider = _provider()
    assert isinstance(provider, BaseProvider)


def test_search_async_with_mocked_html() -> None:
    """Verify _search_async parses job cards from HTML."""
    provider = _provider()
    listing_html = """
    <div class="job-search-card">
        <h3 class="base-search-card__title">Python Dev</h3>
        <a class="hidden-nested-link">Tech Corp</a>
        <span class="job-search-card__location">SP, São Paulo</span>
        <a class="base-card__full-link" href="https://br.linkedin.com/jobs/view/111"></a>
    </div>
    """
    detail_html = """
    <div class="show-more-less-html__markup">
        <p>Python development role.</p>
    </div>
    """

    async def mock_fetch(*args: object, **kwargs: object) -> str:
        url = str(args[1]) if len(args) > 1 else ""
        return listing_html if "search" in url else detail_html

    with patch.object(provider, "_fetch_with_retry", side_effect=mock_fetch):
        vacancies = asyncio.run(provider._search_async("Python", "SP", "São Paulo"))

    assert len(vacancies) == 3
    assert vacancies[0].title == "Python Dev"
    assert vacancies[0].company == "Tech Corp"
    assert vacancies[0].external_id == "111"


def test_search_async_with_no_results() -> None:
    """Verify _search_async returns empty list when no cards found."""
    provider = _provider()
    listing_html = "<div>No jobs here</div>"

    async def mock_fetch(*args: object, **kwargs: object) -> str:
        return listing_html

    with patch.object(provider, "_fetch_with_retry", side_effect=mock_fetch):
        vacancies = asyncio.run(provider._search_async("Python", "SP", "São Paulo"))

    assert vacancies == []


def test_get_job_async_with_mocked_html() -> None:
    """Verify _get_job_async parses a single job page."""
    provider = _provider()
    detail_html = """
    <h1 class="top-card__title">Senior Python Dev</h1>
    <span class="top-card__flavor">São Paulo, SP</span>
    <div class="show-more-less-html__markup">
        <p>Senior Python role at Tech Corp.</p>
    </div>
    """

    async def mock_fetch(*args: object, **kwargs: object) -> str:
        return detail_html

    with patch.object(provider, "_fetch_with_retry", side_effect=mock_fetch):
        vacancy = asyncio.run(
            provider._get_job_async("https://br.linkedin.com/jobs/view/222")
        )

    assert vacancy is not None
    assert vacancy.title == "Senior Python Dev"
    assert vacancy.state == "SP"
    assert vacancy.municipality == "São Paulo"
    assert vacancy.description == "Senior Python role at Tech Corp."


def test_get_job_async_returns_none_on_fetch_failure() -> None:
    """Verify _get_job_async returns None when fetch fails."""
    provider = _provider()

    async def mock_fetch(*args: object, **kwargs: object) -> None:
        return None

    with patch.object(provider, "_fetch_with_retry", side_effect=mock_fetch):
        vacancy = asyncio.run(
            provider._get_job_async("https://br.linkedin.com/jobs/view/333")
        )

    assert vacancy is None


def test_search_async_with_remote_location() -> None:
    """Verify _search_async handles remote location."""
    provider = _provider()
    listing_html = """
    <div class="job-search-card">
        <h3 class="base-search-card__title">Remote Dev</h3>
        <a class="hidden-nested-link">Remote Corp</a>
        <span class="job-search-card__location">Remoto</span>
        <a class="base-card__full-link" href="https://br.linkedin.com/jobs/view/444"></a>
    </div>
    """

    async def mock_fetch(*args: object, **kwargs: object) -> str:
        return listing_html

    with patch.object(provider, "_fetch_with_retry", side_effect=mock_fetch):
        vacancies = asyncio.run(provider._search_async("Python", "SP", "São Paulo"))

    assert len(vacancies) >= 1
    assert vacancies[0].state == "Remoto"
    assert vacancies[0].municipality == "Remoto"


def test_parse_job_card_with_no_title() -> None:
    """Verify _parse_job_card handles missing title."""
    html = """
    <div class="job-search-card">
        <a class="hidden-nested-link">Some Corp</a>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", {"class": "job-search-card"})
    assert card is not None
    provider = _provider()
    result = provider._parse_job_card(card)

    assert result["title"] is None
    assert result["company"] == "Some Corp"


def test_parse_detail_page_with_no_markup_class() -> None:
    """Verify _parse_detail_page handles missing markup class."""
    html = '<div class="other-class"><p>Some text</p></div>'
    provider = _provider()
    raw = {"description": None}
    result = provider._parse_detail_page(html, raw)

    assert result["description"] is None


def test_get_job_async_with_fallback_title_selector() -> None:
    """Verify _get_job_async uses fallback title selector."""
    provider = _provider()
    detail_html = """
    <h1 class="jobs-unified-top-card__job-title">Backend Engineer</h1>
    <span class="top-card__flavor">SP, São Paulo</span>
    <div class="show-more-less-html__markup">
        <p>Backend role.</p>
    </div>
    """

    async def mock_fetch(*args: object, **kwargs: object) -> str:
        return detail_html

    with patch.object(provider, "_fetch_with_retry", side_effect=mock_fetch):
        vacancy = asyncio.run(
            provider._get_job_async("https://br.linkedin.com/jobs/view/555")
        )

    assert vacancy is not None
    assert vacancy.title == "Backend Engineer"


def test_get_job_async_with_fallback_company_selector() -> None:
    """Verify _get_job_async uses fallback company selector."""
    provider = _provider()
    detail_html = """
    <h1 class="top-card__title">Frontend Dev</h1>
    <span class="top-card__company-name">Frontend Inc</span>
    <span class="top-card__flavor">SP, São Paulo</span>
    <div class="show-more-less-html__markup">
        <p>Frontend role.</p>
    </div>
    """

    async def mock_fetch(*args: object, **kwargs: object) -> str:
        return detail_html

    with patch.object(provider, "_fetch_with_retry", side_effect=mock_fetch):
        vacancy = asyncio.run(
            provider._get_job_async("https://br.linkedin.com/jobs/view/666")
        )

    assert vacancy is not None
    assert vacancy.company == "Frontend Inc"


def test_search_async_stops_on_fetch_failure() -> None:
    """Verify _search_async stops pagination when fetch returns None."""
    provider = _provider()

    async def mock_fetch(*args: object, **kwargs: object) -> None:
        return None

    with patch.object(provider, "_fetch_with_retry", side_effect=mock_fetch):
        vacancies = asyncio.run(provider._search_async("Python", "SP", "São Paulo"))

    assert vacancies == []


def test_search_async_continues_on_card_parse_error() -> None:
    """Verify _search_async continues when a job card raises an exception."""
    provider = _provider()
    listing_html = """
    <div class="job-search-card">
        <h3 class="base-search-card__title">Python Dev</h3>
        <a class="hidden-nested-link">Tech Corp</a>
        <span class="job-search-card__location">SP, São Paulo</span>
        <a class="base-card__full-link" href="https://br.linkedin.com/jobs/view/111"></a>
    </div>
    <div class="job-search-card">
        <h3 class="base-search-card__title">Data Scientist</h3>
        <a class="hidden-nested-link">Data Corp</a>
        <span class="job-search-card__location">RJ, Rio</span>
        <a class="base-card__full-link" href="https://br.linkedin.com/jobs/view/222"></a>
    </div>
    """

    fetch_count = 0

    async def mock_fetch(*args: object, **kwargs: object) -> str | None:
        nonlocal fetch_count
        fetch_count += 1
        if fetch_count == 1:
            return listing_html
        return None

    call_count = 0
    real_parse = provider._parse_job_card

    def failing_parse(card: Tag) -> dict[str, object]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("Parse boom")
        return real_parse(card)

    with (
        patch.object(provider, "_fetch_with_retry", side_effect=mock_fetch),
        patch.object(provider, "_parse_job_card", side_effect=failing_parse),
    ):
        vacancies = asyncio.run(provider._search_async("Python", "SP", "São Paulo"))

    assert len(vacancies) == 1
    assert vacancies[0].title == "Data Scientist"


def test_fetch_with_retry_handles_timeout() -> None:
    """Verify _fetch_with_retry retries on TimeoutError."""
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
    mock_response.text = AsyncMock(return_value="<html></html>")

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.get = MagicMock(side_effect=[TimeoutError(), mock_response])

    with (
        patch("src.providers.linkedin.get_settings", return_value=mock_settings),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        result = asyncio.run(
            provider._fetch_with_retry(mock_session, "https://example.com")
        )

    assert result == "<html></html>"
    assert mock_session.get.call_count == 2


def test_fetch_with_retry_handles_client_error() -> None:
    """Verify _fetch_with_retry retries on ClientError."""
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
    mock_response.text = AsyncMock(return_value="<html></html>")

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.get = MagicMock(side_effect=[ClientError("boom"), mock_response])

    with (
        patch("src.providers.linkedin.get_settings", return_value=mock_settings),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        result = asyncio.run(
            provider._fetch_with_retry(mock_session, "https://example.com")
        )

    assert result == "<html></html>"


def test_fetch_with_retry_handles_unexpected_exception() -> None:
    """Verify _fetch_with_retry retries on unexpected exceptions."""
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
    mock_response.text = AsyncMock(return_value="<html></html>")

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.get = MagicMock(side_effect=[RuntimeError("boom"), mock_response])

    with (
        patch("src.providers.linkedin.get_settings", return_value=mock_settings),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        result = asyncio.run(
            provider._fetch_with_retry(mock_session, "https://example.com")
        )

    assert result == "<html></html>"


def test_fetch_with_retry_returns_none_after_max_attempts() -> None:
    """Verify _fetch_with_retry returns None after exhausting retries."""
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
        patch("src.providers.linkedin.get_settings", return_value=mock_settings),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        result = asyncio.run(
            provider._fetch_with_retry(mock_session, "https://example.com")
        )

    assert result is None
    assert mock_session.get.call_count == 2


def test_parse_job_card_handles_title_exception() -> None:
    """Verify _parse_job_card handles exception when parsing title."""
    html = """
    <div class="job-search-card">
        <h3 class="base-search-card__title">Python Dev</h3>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", {"class": "job-search-card"})
    assert card is not None
    provider = _provider()

    bad_element = MagicMock()
    bad_element.text.strip.side_effect = RuntimeError("boom")

    with patch.object(card, "find", return_value=bad_element):
        result = provider._parse_job_card(card)

    assert result["title"] is None


def test_parse_job_card_handles_company_exception() -> None:
    """Verify _parse_job_card handles exception when parsing company."""
    html = """
    <div class="job-search-card">
        <a class="hidden-nested-link">Acme</a>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", {"class": "job-search-card"})
    assert card is not None
    provider = _provider()

    bad_element = MagicMock()
    bad_element.text.strip.side_effect = RuntimeError("boom")

    with patch.object(card, "find", side_effect=[None, bad_element]):
        result = provider._parse_job_card(card)

    assert result["company"] is None


def test_parse_job_card_handles_location_exception() -> None:
    """Verify _parse_job_card handles exception when parsing location."""
    html = """
    <div class="job-search-card">
        <span class="job-search-card__location">SP, São Paulo</span>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", {"class": "job-search-card"})
    assert card is not None
    provider = _provider()

    bad_element = MagicMock()
    bad_element.text.strip.side_effect = RuntimeError("boom")

    with patch.object(card, "find", side_effect=[None, None, bad_element]):
        result = provider._parse_job_card(card)

    assert result["location"] is None


def test_parse_job_card_handles_link_exception() -> None:
    """Verify _parse_job_card handles exception when parsing link."""
    html = """
    <div class="job-search-card">
        <a class="base-card__full-link" href="https://example.com"></a>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", {"class": "job-search-card"})
    assert card is not None
    provider = _provider()

    bad_element = MagicMock()
    bad_element.has_attr.side_effect = RuntimeError("boom")

    with patch.object(card, "find", side_effect=[None, None, None, bad_element]):
        result = provider._parse_job_card(card)

    assert result["url"] is None


def test_parse_detail_page_handles_exception() -> None:
    """Verify _parse_detail_page handles exception during parsing."""
    provider = _provider()
    raw = {"description": None}

    with patch(
        "src.providers.linkedin.BeautifulSoup",
        side_effect=RuntimeError("boom"),
    ):
        result = provider._parse_detail_page("<html></html>", raw)

    assert result["description"] is None


def test_get_job_async_handles_parse_exception() -> None:
    """Verify _get_job_async handles exception during detail page parsing."""
    provider = _provider()
    detail_html = """
    <h1 class="top-card__title">Senior Python Dev</h1>
    <span class="top-card__flavor">SP, São Paulo</span>
    <div class="show-more-less-html__markup">
        <p>Senior Python role.</p>
    </div>
    """

    async def mock_fetch(*args: object, **kwargs: object) -> str:
        return detail_html

    with (
        patch.object(provider, "_fetch_with_retry", side_effect=mock_fetch),
        patch(
            "src.providers.linkedin.BeautifulSoup",
            side_effect=RuntimeError("boom"),
        ),
    ):
        vacancy = asyncio.run(
            provider._get_job_async("https://br.linkedin.com/jobs/view/777")
        )

    assert vacancy is not None
    assert vacancy.title == ""
