"""PyST API client for suggest endpoint."""

import httpx
from typing import Optional, Any
from trailpack.pyst.api.config import config
from trailpack.pyst.api.requests.suggest import SuggestRequest


class PystSuggestClient:
    """
    Singleton client for PyST concept suggest endpoint.

    This client manages HTTP connections to the PyST API and provides
    a simple interface for concept suggestions.

    Example:
        >>> client = PystSuggestClient.get_instance()
        >>> results = await client.suggest("carbon", "en")
    """

    _instance: Optional["PystSuggestClient"] = None
    _http_client: Optional[httpx.AsyncClient] = None

    def __new__(cls):
        """Singleton pattern - only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the client with configuration."""
        if self._http_client is None:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize the HTTP client with configuration."""
        headers = {}

        if config.auth_token:
            headers["Authorization"] = f"Bearer {config.auth_token}"

        self._http_client = httpx.AsyncClient(
            base_url=config.host,
            timeout=config.timeout,
            headers=headers,
            follow_redirects=True
        )

    @classmethod
    def get_instance(cls) -> "PystSuggestClient":
        """
        Get the singleton instance of the client.

        Returns:
            PystSuggestClient instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def suggest(
        self,
        query: str,
        language: str
    ) -> list[dict[str, Any]]:
        """
        Get concept suggestions from PyST API.

        Args:
            query: Search query string
            language: ISO 639-1 language code (en, de, es, fr, pt, it, da)

        Returns:
            List of concept suggestions

        Raises:
            httpx.HTTPError: If the API request fails
            ValueError: If request parameters are invalid

        Example:
            >>> client = PystSuggestClient.get_instance()
            >>> results = await client.suggest("carbon", "en")
            >>> for concept in results:
            ...     print(concept["label"])
        """
        # Validate request parameters
        request = SuggestRequest(query=query, language=language)
        params = request.to_query_params()

        # Make API request
        response = await self._http_client.get(
            "/concepts/suggest/",
            params=params
        )

        # Raise for HTTP errors
        response.raise_for_status()

        # Return JSON response
        return response.json()

    async def close(self):
        """Close the HTTP client connection."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Convenience function to get client instance
def get_suggest_client() -> PystSuggestClient:
    """
    Get the singleton PyST suggest client instance.

    Returns:
        PystSuggestClient instance

    Example:
        >>> from trailpack.pyst.api.client import get_suggest_client
        >>> client = get_suggest_client()
        >>> results = await client.suggest("sustainability", "en")
    """
    return PystSuggestClient.get_instance()
