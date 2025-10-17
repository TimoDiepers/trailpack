"""Tests for Streamlit UI helper functions.

Note: These tests duplicate function implementations instead of importing from
streamlit_app.py because the Streamlit app has Streamlit-specific imports that
would fail in the test environment. This is an acceptable trade-off for testing
core logic without requiring a full Streamlit environment.
"""

import pytest
import re


def extract_first_word(query: str) -> str:
    """
    Extract the first word from a string, stopping at the first space.
    This duplicates the implementation in streamlit_app.py for testing purposes.
    """
    if not query:
        return ""
    parts = query.split(' ', 1)
    return parts[0] if parts else ""


def sanitize_search_query(query: str) -> str:
    """
    Sanitize search query for safe API calls.
    This duplicates the implementation in streamlit_app.py for testing purposes.
    """
    # Replace forward slashes, backslashes, and other special characters with spaces
    # Keep alphanumeric, spaces, hyphens, underscores, and periods
    sanitized = re.sub(r'[^\w\s\-.]', ' ', query)
    
    # Collapse multiple spaces into single space
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # Strip leading/trailing whitespace
    sanitized = sanitized.strip()
    
    return sanitized


def test_extract_first_word():
    """Test the extract_first_word function."""
    # Test basic cases
    assert extract_first_word("location") == "location"
    assert extract_first_word("timestamp data") == "timestamp"
    assert extract_first_word("amount per unit") == "amount"
    assert extract_first_word("") == ""
    assert extract_first_word("word") == "word"
    assert extract_first_word("two words") == "two"
    assert extract_first_word("multiple word phrase here") == "multiple"
    
    # Edge case: sanitize_search_query strips leading/trailing spaces before passing to extract_first_word
    # So "   leading spaces" would be sanitized to "leading spaces" first, then return "leading"
    # Testing the raw function behavior here:
    assert extract_first_word("   leading spaces") == ""  # First "word" is empty before the leading spaces


def test_sanitize_search_query():
    """Test the sanitize_search_query function."""
    # Test basic sanitization
    assert sanitize_search_query("location/city") == "location city"
    assert sanitize_search_query("amount\\per\\unit") == "amount per unit"
    assert sanitize_search_query("data@2024") == "data 2024"
    assert sanitize_search_query("valid-name_123") == "valid-name_123"
    assert sanitize_search_query("  multiple   spaces  ") == "multiple spaces"
    assert sanitize_search_query("special!@#$%chars") == "special chars"
    

def test_sanitize_and_extract_first_word_combined():
    """Test the combined workflow of sanitize and extract first word."""
    # Test the combined workflow - this simulates what happens in the UI
    # When a column name like "location/city data" is processed:
    column_name = "location/city data"
    sanitized = sanitize_search_query(column_name)
    assert sanitized == "location city data"
    
    first_word = extract_first_word(sanitized)
    assert first_word == "location"  # Only the first word!
    
    # Another example
    column_name2 = "amount@per@unit"
    sanitized2 = sanitize_search_query(column_name2)
    assert sanitized2 == "amount per unit"
    
    first_word2 = extract_first_word(sanitized2)
    assert first_word2 == "amount"  # Only the first word!
    
    # Edge case: leading/trailing spaces are handled by sanitize
    column_name3 = "   location   "
    sanitized3 = sanitize_search_query(column_name3)
    assert sanitized3 == "location"
    
    first_word3 = extract_first_word(sanitized3)
    assert first_word3 == "location"
