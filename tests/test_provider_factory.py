"""Provider factory tests."""

from collections.abc import Mapping

import pytest

from src.database.models.vacancy import Vacancy
from src.providers.base import BaseProvider
from src.providers.factory import ProviderFactory


class StubProvider(BaseProvider):
    """Stub provider for tests."""

    def search(self, keyword: str, state: str, municipality: str) -> list[Vacancy]:
        """Stub search."""
        return []

    def get_job(self, url: str) -> Vacancy | None:
        """Stub get job."""
        return None

    def normalize(self, raw_data: Mapping[str, object]) -> Vacancy:
        """Stub normalize."""
        raise NotImplementedError


def test_register_and_get_provider() -> None:
    """Verify provider registration and retrieval."""
    factory = ProviderFactory()
    provider = StubProvider()
    factory.register("stub", provider)

    assert factory.get("stub") is provider


def test_get_unknown_provider_raises() -> None:
    """Verify getting unknown provider raises ValueError."""
    factory = ProviderFactory()

    with pytest.raises(ValueError):
        factory.get("unknown")


def test_get_names_returns_registered_providers() -> None:
    """Verify get_names returns registered providers."""
    factory = ProviderFactory()
    provider_a = StubProvider()
    provider_b = StubProvider()

    factory.register("a", provider_a)
    factory.register("b", provider_b)

    assert factory.get_names() == ["a", "b"]
