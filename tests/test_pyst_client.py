"""Tests for PyST API client."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx


@pytest.mark.anyio
async def test_get_concept_returns_definition():
    """Test that get_concept returns concept details including definition."""
    from trailpack.pyst.api.client import PystSuggestClient

    # Mock response data matching the example in the issue
    mock_concept_data = {
        "@id": "http://data.europa.eu/xsp/cn2024/010021000090",
        "@type": ["http://www.w3.org/2004/02/skos/core#Concept"],
        "http://www.w3.org/2004/02/skos/core#prefLabel": [
            {"@language": "en", "@value": "CHAPTER 1 - LIVE ANIMALS"}
        ],
        "http://www.w3.org/2004/02/skos/core#definition": [
            {
                "@language": "en",
                "@value": (
                    "Includes all sorts of live animals, "
                    "including things you probably never heard of before."
                ),
            }
        ],
    }

    # Create a mock response
    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = mock_concept_data
    mock_response.raise_for_status = Mock()

    # Patch the httpx AsyncClient
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        mock_client_class.return_value = mock_client

        # Create client and call get_concept
        client = PystSuggestClient.get_instance()
        result = await client.get_concept(
            "http://data.europa.eu/xsp/cn2024/010021000090"
        )

        # Verify the result
        assert result == mock_concept_data
        assert "http://www.w3.org/2004/02/skos/core#definition" in result

        # Verify the API call was made correctly
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert (
            "/concepts/http://data.europa.eu/xsp/cn2024/010021000090" in call_args[0][0]
        )


@pytest.mark.anyio
async def test_get_concept_raises_on_empty_iri():
    """Test that get_concept raises ValueError on empty IRI."""
    from trailpack.pyst.api.client import PystSuggestClient

    client = PystSuggestClient.get_instance()

    with pytest.raises(ValueError, match="IRI cannot be empty"):
        await client.get_concept("")

    with pytest.raises(ValueError, match="IRI cannot be empty"):
        await client.get_concept("   ")


@pytest.mark.anyio
async def test_get_concept_handles_http_errors():
    """Test that get_concept handles HTTP errors appropriately."""
    from trailpack.pyst.api.client import PystSuggestClient

    # Create a mock response that raises an HTTP error
    mock_response = Mock(spec=httpx.Response)
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404 Not Found", request=Mock(), response=Mock(status_code=404)
    )

    # Patch the httpx AsyncClient
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        mock_client_class.return_value = mock_client

        # Create client and call get_concept
        client = PystSuggestClient.get_instance()

        with pytest.raises(httpx.HTTPStatusError):
            await client.get_concept("http://example.com/nonexistent")


def test_fetch_concept_async_extracts_definition_correctly():
    """Test that fetch_concept_async extracts SKOS definition correctly."""
    import asyncio
    from trailpack.ui.panel_app import fetch_concept_async
    from trailpack.pyst.api.client import get_suggest_client

    # Mock the async function
    mock_definition = "This is a test definition"
    
    mock_client = AsyncMock()
    mock_concept_data = {
        "http://www.w3.org/2004/02/skos/core#definition": [
            {"@language": "en", "@value": mock_definition}
        ]
    }
    mock_client.get_concept.return_value = mock_concept_data

    result = asyncio.run(fetch_concept_async(mock_client, "http://example.com/concept", "en"))

    assert result == mock_definition


def test_fetch_concept_async_extracts_english_definition():
    """Test that fetch_concept_async extracts definition in requested language."""
    import asyncio
    from trailpack.ui.panel_app import fetch_concept_async

    # Mock response with multiple language definitions
    mock_concept_data = {
        "http://www.w3.org/2004/02/skos/core#definition": [
            {"@language": "de", "@value": "Deutsche Definition"},
            {"@language": "en", "@value": "English definition"},
            {"@language": "fr", "@value": "Définition française"},
        ]
    }

    mock_client = AsyncMock()
    mock_client.get_concept.return_value = mock_concept_data

    # Test English
    result = asyncio.run(fetch_concept_async(mock_client, "http://example.com/concept", "en"))
    assert result == "English definition"


def test_fetch_concept_async_falls_back_to_first_definition():
    """Test fetch_concept_async falls back to first definition if language not found."""
    import asyncio
    from trailpack.ui.panel_app import fetch_concept_async

    # Mock response with only German definition
    mock_concept_data = {
        "http://www.w3.org/2004/02/skos/core#definition": [
            {"@language": "de", "@value": "Deutsche Definition"}
        ]
    }

    mock_client = AsyncMock()
    mock_client.get_concept.return_value = mock_concept_data

    # Request English but only German available - should return German
    result = asyncio.run(fetch_concept_async(mock_client, "http://example.com/concept", "en"))
    assert result == "Deutsche Definition"


def test_fetch_concept_async_returns_none_if_no_definition():
    """Test that fetch_concept_async returns None if no definition exists."""
    import asyncio
    from trailpack.ui.panel_app import fetch_concept_async

    # Mock response without definition
    mock_concept_data = {
        "@id": "http://example.com/concept",
        "http://www.w3.org/2004/02/skos/core#prefLabel": [
            {"@language": "en", "@value": "Test Concept"}
        ],
    }

    mock_client = AsyncMock()
    mock_client.get_concept.return_value = mock_concept_data

    result = asyncio.run(fetch_concept_async(mock_client, "http://example.com/concept", "en"))
    assert result is None


def test_fetch_concept_async_handles_errors_gracefully():
    """Test that fetch_concept_async handles errors gracefully."""
    import asyncio
    from trailpack.ui.panel_app import fetch_concept_async

    mock_client = AsyncMock()
    mock_client.get_concept.side_effect = Exception("API error")

    result = asyncio.run(fetch_concept_async(mock_client, "http://example.com/concept", "en"))
    assert result is None
