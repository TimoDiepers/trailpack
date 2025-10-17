"""Tests for streamlit_app URL helper functions."""

from trailpack.ui.streamlit_app import iri_to_web_url


def test_iri_to_web_url_geonames():
    """Test converting a Geonames IRI to web URL."""
    iri = "https://vocab.sentier.dev/Geonames/A"
    web_url = iri_to_web_url(iri, "en")

    # Check the structure
    assert web_url.startswith("https://vocab.sentier.dev/web/concept/")

    # Check that the IRI and concept scheme are properly encoded
    assert "https%3A%2F%2Fvocab.sentier.dev%2FGeonames%2FA" in web_url
    assert "concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2FGeonames%2F" in web_url


def test_iri_to_web_url_units():
    """Test converting a units IRI to web URL."""
    iri = "https://vocab.sentier.dev/units/unit/NUM"
    web_url = iri_to_web_url(iri, "en")

    # Check the structure
    assert web_url.startswith("https://vocab.sentier.dev/web/concept/")

    # Check that the IRI and concept scheme are properly encoded
    assert "https%3A%2F%2Fvocab.sentier.dev%2Funits%2Funit%2FNUM" in web_url
    assert "concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2Funits%2F" in web_url


def test_iri_to_web_url_products():
    """Test converting a products IRI to web URL."""
    iri = "https://vocab.sentier.dev/products/product/Product"
    web_url = iri_to_web_url(iri, "de")  # Test different language

    # Check the structure
    assert web_url.startswith("https://vocab.sentier.dev/web/concept/")

    # Check that the IRI and concept scheme are properly encoded
    assert "https%3A%2F%2Fvocab.sentier.dev%2Fproducts%2Fproduct%2FProduct" in web_url
    assert "concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2Fproducts%2F" in web_url


def test_iri_to_web_url_model_terms():
    """Test converting a model-terms IRI to web URL."""
    iri = "https://vocab.sentier.dev/model-terms/generic-terms/Emission"
    web_url = iri_to_web_url(iri, "en")

    # Check the structure
    assert web_url.startswith("https://vocab.sentier.dev/web/concept/")

    # Check that the IRI and concept scheme are properly encoded
    assert (
        "https%3A%2F%2Fvocab.sentier.dev%2Fmodel-terms%2Fgeneric-terms%2FEmission"
        in web_url
    )
    assert "concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2Fmodel-terms%2F" in web_url
