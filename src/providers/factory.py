"""Provider factory for provider registration and retrieval."""

from src.providers.base import BaseProvider


class ProviderFactory:
    """Factory for registering and retrieving providers."""

    def __init__(self) -> None:
        """Initialize factory with empty provider registry."""
        self._providers: dict[str, BaseProvider] = {}

    def register(self, name: str, provider: BaseProvider) -> None:
        """Register a provider.

        Args:
            name (str): Provider name.
            provider (BaseProvider): Provider instance.
        """
        self._providers[name] = provider

    def get(self, name: str) -> BaseProvider:
        """Retrieve a provider by name.

        Args:
            name (str): Provider name.

        Returns:
            BaseProvider: Registered provider.

        Raises:
            ValueError: If provider is not registered.
        """
        try:
            return self._providers[name]
        except KeyError as exc:
            raise ValueError(f"Provider '{name}' is not registered.") from exc

    def get_names(self) -> list[str]:
        """Return registered provider names.

        Returns:
            list[str]: Registered provider names.
        """
        return list(self._providers.keys())
