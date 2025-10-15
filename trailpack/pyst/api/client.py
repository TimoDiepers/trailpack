"""PyST API client for suggest endpoint.

Based on pyst_client.simple.client pattern:
https://github.com/cauldron/pyst-client/blob/main/pyst_client/simple/client.py
"""

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
    _api_client: Optional[httpx.AsyncClient] = None

    def __new__(cls):
        """Singleton pattern - only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the client with configuration."""
        if self._api_client is None:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize the HTTP client with configuration."""
        headers = {
            "Content-Type": "application/json",
        }

        # Set up authentication if token is provided
        # PyST uses "x-pyst-auth-token" header, not Bearer token
        if config.auth_token:
            headers["x-pyst-auth-token"] = config.auth_token

        # Create httpx AsyncClient
        import httpx
        self._api_client = httpx.AsyncClient(
            base_url=config.host.rstrip('/'),
            timeout=config.timeout,
            headers=headers,
            follow_redirects=True
        )

    def _ensure_client_valid(self):
        """
        Ensure the client is valid for the current event loop.

        If the client is closed or tied to a different event loop,
        reinitialize it. This is necessary for Streamlit compatibility.
        """
        import asyncio

        if self._api_client is None:
            self._initialize_client()
            return

        if self._api_client.is_closed:
            # Client is closed, reinitialize
            self._initialize_client()
            return

        # For Streamlit: always recreate client if we're in a new event loop
        # This avoids "bound to different event loop" errors
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, client is fine
            return

        # Store the loop ID when client is created, check if it changed
        if not hasattr(self, '_loop_id'):
            self._loop_id = id(current_loop)
        elif self._loop_id != id(current_loop):
            # Different event loop detected, recreate client
            try:
                # Try to close old client gracefully
                import asyncio
                asyncio.create_task(self._api_client.aclose())
            except Exception:
                pass
            finally:
                self._api_client = None
                self._initialize_client()
                self._loop_id = id(current_loop)

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
            ApiException: If the API request fails
            ValueError: If request parameters are invalid

        Example:
            >>> client = PystSuggestClient.get_instance()
            >>> results = await client.suggest("carbon", "en")
            >>> for concept in results:
            ...     print(concept["label"])
        """
        # Ensure client is valid for current event loop
        self._ensure_client_valid()

        # Validate request parameters
        request = SuggestRequest(query=query, language=language)
        params = request.to_query_params()

        # Make API request using httpx AsyncClient
        response = await self._api_client.get(
            "/concepts/suggest/",
            params=params
        )

        # Raise for HTTP errors
        response.raise_for_status()

        # Return JSON response
        return response.json()

    async def close(self):
        """Close the API client connection."""
        if self._api_client is not None:
            await self._api_client.aclose()
            self._api_client = None

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
