"""Tests for streamlit_app URL helper functions."""

from trailpack.ui.streamlit_app import iri_to_web_url


def test_iri_to_web_url_geonames():
    """Test converting a Geonames IRI to web URL."""
    iri = "https://vocab.sentier.dev/Geonames/A"
    web_url = iri_to_web_url(iri, "en")

    # Check the structure
    assert web_url.startswith("https://vocab.sentier.dev/web/concept/")
    assert "concept_scheme=" in web_url
    assert "language=en" in web_url

    # Check that the IRI and concept scheme are properly encoded
    # IRI should have only colon encoded, not slashes
    assert "https%3A//vocab.sentier.dev/Geonames/A" in web_url
    # Concept scheme should have all characters encoded, no trailing slash
    assert "concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2FGeonames" in web_url
    assert "concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2FGeonames%2F" not in web_url


def test_iri_to_web_url_units():
    """Test converting a units IRI to web URL."""
    iri = "https://vocab.sentier.dev/units/unit/NUM"
    web_url = iri_to_web_url(iri, "en")

    # Check the structure
    assert web_url.startswith("https://vocab.sentier.dev/web/concept/")
    assert "concept_scheme=" in web_url
    assert "language=en" in web_url

    # Check that the IRI and concept scheme are properly encoded
    # IRI should have only colon encoded, not slashes
    assert "https%3A//vocab.sentier.dev/units/unit/NUM" in web_url
    # Concept scheme should have all characters encoded, no trailing slash
    assert "concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2Funits" in web_url
    assert "concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2Funits%2F" not in web_url


def test_iri_to_web_url_products():
    """Test converting a products IRI to web URL."""
    iri = "https://vocab.sentier.dev/products/product/Product"
    web_url = iri_to_web_url(iri, "de")  # Test different language

    # Check the structure
    assert web_url.startswith("https://vocab.sentier.dev/web/concept/")
    assert "concept_scheme=" in web_url
    assert "language=de" in web_url

    # Check that the IRI and concept scheme are properly encoded
    # IRI should have only colon encoded, not slashes
    assert "https%3A//vocab.sentier.dev/products/product/Product" in web_url
    # Concept scheme should have all characters encoded, no trailing slash
    assert "concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2Fproducts" in web_url
    assert "concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2Fproducts%2F" not in web_url


def test_iri_to_web_url_model_terms():
    """Test converting a model-terms IRI to web URL."""
    iri = "https://vocab.sentier.dev/model-terms/generic-terms/Emission"
    web_url = iri_to_web_url(iri, "en")

    # Check the structure
    assert web_url.startswith("https://vocab.sentier.dev/web/concept/")
    assert "concept_scheme=" in web_url
    assert "language=en" in web_url

    # Check that the IRI and concept scheme are properly encoded
    # IRI should have only colon encoded, not slashes
    assert (
        "https%3A//vocab.sentier.dev/model-terms/generic-terms/Emission"
        in web_url
    )
    # Concept scheme should have all characters encoded, no trailing slash
    assert "concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2Fmodel-terms" in web_url
    assert "concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2Fmodel-terms%2F" not in web_url


def test_iri_to_web_url_wgs84():
    """Test converting a WGS84 IRI to web URL (issue-specific test)."""
    iri = "https://vocab.sentier.dev/WGS84/latitude"
    web_url = iri_to_web_url(iri, "en")

    # Check the structure
    assert web_url.startswith("https://vocab.sentier.dev/web/concept/")
    assert "concept_scheme=" in web_url
    assert "language=en" in web_url

    # Check that the IRI and concept scheme are properly encoded
    # IRI should have only colon encoded, not slashes
    assert "https%3A//vocab.sentier.dev/WGS84/latitude" in web_url
    # Concept scheme should have all characters encoded, no trailing slash
    assert "concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2FWGS84" in web_url
    assert "concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2FWGS84%2F" not in web_url

    # Verify the exact expected URL format from the issue
    expected = "https://vocab.sentier.dev/web/concept/https%3A//vocab.sentier.dev/WGS84/latitude?concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2FWGS84&language=en"
    assert web_url == expected


def test_iri_to_web_url_bonsai():
    """Test converting a BONSAI product IRI to web URL (issue-specific test)."""
    iri = "https://vocab.sentier.dev/products/bonsai/2025.1/BONSAI2025.1/fi_01314"
    web_url = iri_to_web_url(iri, "en")

    # Check the structure
    assert web_url.startswith("https://vocab.sentier.dev/web/concept/")
    assert "concept_scheme=" in web_url
    assert "language=en" in web_url

    # Check that the IRI and concept scheme are properly encoded
    # IRI should have only colon encoded, not slashes
    assert "https%3A//vocab.sentier.dev/products/bonsai/2025.1/BONSAI2025.1/fi_01314" in web_url
    # Concept scheme should have all characters encoded, no trailing slash
    assert "concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2Fproducts" in web_url
    assert "concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2Fproducts%2F" not in web_url

    # Verify the expected URL format
    expected = "https://vocab.sentier.dev/web/concept/https%3A//vocab.sentier.dev/products/bonsai/2025.1/BONSAI2025.1/fi_01314?concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2Fproducts&language=en"
    assert web_url == expected
