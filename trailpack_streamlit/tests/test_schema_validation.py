"""Tests for schema-based data validation."""

import pandas as pd
import pytest

from trailpack.validation import StandardValidator


@pytest.fixture
def validator():
    """Create a StandardValidator instance."""
    return StandardValidator()


@pytest.fixture
def sample_schema():
    """Create a sample schema for testing."""
    return {
        "fields": [
            {
                "name": "id",
                "type": "integer",
                "description": "Unique identifier",
                "unit": {
                    "name": "dimensionless",
                    "long_name": "dimensionless number",
                    "path": "http://qudt.org/vocab/unit/NUM",
                },
            },
            {"name": "name", "type": "string", "description": "Name of the item"},
            {
                "name": "mass",
                "type": "number",
                "description": "Mass measurement",
                "unit": {
                    "name": "kg",
                    "long_name": "kilogram",
                    "path": "http://qudt.org/vocab/unit/KiloGM",
                },
            },
            {
                "name": "temperature",
                "type": "number",
                "description": "Temperature measurement",
                "unit": {
                    "name": "degC",
                    "long_name": "degree Celsius",
                    "path": "http://qudt.org/vocab/unit/DEG_C",
                },
            },
            {"name": "is_active", "type": "boolean", "description": "Active status"},
            {
                "name": "count",
                "type": "integer",
                "description": "Count of items",
                "unit": {
                    "name": "dimensionless",
                    "long_name": "dimensionless number",
                    "path": "http://qudt.org/vocab/unit/NUM",
                },
            },
        ]
    }


@pytest.fixture
def valid_dataframe():
    """Create a valid DataFrame matching the schema."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
            "mass": [10.5, 20.3, 15.7],
            "temperature": [25.0, 30.0, 28.5],
            "is_active": [True, False, True],
            "count": [5, 10, 8],
        }
    )


def test_valid_data_passes_schema_validation(validator, sample_schema, valid_dataframe):
    """Test that valid data passes schema validation."""
    result = validator.validate_data_quality(valid_dataframe, schema=sample_schema)

    # Should have no schema-matching errors
    schema_errors = [e for e in result.errors if "schema_matching" in str(e)]
    assert len(schema_errors) == 0, f"Expected no schema errors, got: {schema_errors}"


def test_type_mismatch_detected(validator, sample_schema):
    """Test that type mismatches are detected."""
    # Create DataFrame with wrong types
    df = pd.DataFrame(
        {
            "id": [
                "not_an_integer",
                "also_string",
                "still_string",
            ],  # Should be integer
            "name": ["A", "B", "C"],
            "mass": [10.5, 20.3, 15.7],
            "temperature": [25.0, 30.0, 28.5],
            "is_active": [True, False, True],
            "count": [5, 10, 8],
        }
    )

    result = validator.validate_data_quality(df, schema=sample_schema)

    # Should have error for 'id' column
    errors_str = " ".join([str(e) for e in result.errors])
    assert "id" in errors_str
    assert "integer" in errors_str or "int" in errors_str


def test_numeric_without_unit_detected(validator):
    """Test that numeric fields without units are detected."""
    # Schema with numeric field but no unit
    schema = {
        "fields": [
            {
                "name": "value",
                "type": "number",
                "description": "A numeric value",
                # No unit specified!
            }
        ]
    }

    df = pd.DataFrame({"value": [1.0, 2.0, 3.0]})

    result = validator.validate_data_quality(df, schema=schema)

    # Should have error about missing unit
    errors_str = " ".join([str(e) for e in result.errors])
    assert "unit" in errors_str.lower()
    assert "value" in errors_str


def test_mixed_types_in_column(validator, sample_schema):
    """Test that mixed types within a column are detected."""
    # Create DataFrame with mixed types in 'name' column
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["A", 123, "C"],  # Mixed string and int
            "mass": [10.5, 20.3, 15.7],
            "temperature": [25.0, 30.0, 28.5],
            "is_active": [True, False, True],
            "count": [5, 10, 8],
        }
    )

    result = validator.validate_data_quality(df, schema=sample_schema)

    # Should have error about mixed types
    errors_str = " ".join([str(e) for e in result.errors])
    assert "name" in errors_str
    assert "mixed" in errors_str.lower() or "type" in errors_str.lower()


def test_missing_column_warning(validator, sample_schema):
    """Test that missing columns generate warnings."""
    # Create DataFrame missing some columns
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
            # Missing: mass, temperature, is_active, count
        }
    )

    result = validator.validate_data_quality(df, schema=sample_schema)

    # Should have warnings about missing columns
    warnings_str = " ".join([str(w) for w in result.warnings])
    assert "mass" in warnings_str or "temperature" in warnings_str


def test_extra_column_warning(validator, sample_schema):
    """Test that extra columns generate warnings."""
    # Create DataFrame with extra columns
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
            "mass": [10.5, 20.3, 15.7],
            "temperature": [25.0, 30.0, 28.5],
            "is_active": [True, False, True],
            "count": [5, 10, 8],
            "extra_column": [100, 200, 300],  # Not in schema
        }
    )

    result = validator.validate_data_quality(df, schema=sample_schema)

    # Should have warning about extra column
    warnings_str = " ".join([str(w) for w in result.warnings])
    assert "extra_column" in warnings_str


def test_validation_without_schema(validator, valid_dataframe):
    """Test that validation still works without schema."""
    # Should not crash when schema is None
    result = validator.validate_data_quality(valid_dataframe, schema=None)

    # Should still perform basic validations
    assert result is not None
    assert hasattr(result, "errors")
    assert hasattr(result, "warnings")


def test_boolean_type_validation(validator):
    """Test boolean type validation."""
    schema = {
        "fields": [{"name": "flag", "type": "boolean", "description": "A boolean flag"}]
    }

    # Wrong type for boolean
    df = pd.DataFrame({"flag": ["yes", "no", "yes"]})  # Should be bool

    result = validator.validate_data_quality(df, schema=schema)

    errors_str = " ".join([str(e) for e in result.errors])
    assert "flag" in errors_str
    assert "boolean" in errors_str.lower()


def test_integer_vs_number_types(validator):
    """Test differentiation between integer and number types."""
    schema = {
        "fields": [
            {
                "name": "count",
                "type": "integer",
                "description": "Integer count",
                "unit": {
                    "name": "dimensionless",
                    "long_name": "dimensionless number",
                    "path": "http://qudt.org/vocab/unit/NUM",
                },
            },
            {
                "name": "value",
                "type": "number",
                "description": "Numeric value",
                "unit": {
                    "name": "m",
                    "long_name": "meter",
                    "path": "http://qudt.org/vocab/unit/M",
                },
            },
        ]
    }

    # Valid: integers for count, floats for value
    df = pd.DataFrame({"count": [1, 2, 3], "value": [1.5, 2.7, 3.9]})

    result = validator.validate_data_quality(df, schema=schema)

    # Should pass - both integer and number types accept numeric dtypes
    schema_errors = [e for e in result.errors if "schema_matching" in str(e)]
    assert len(schema_errors) == 0


def test_validate_all_with_schema(validator, sample_schema, valid_dataframe):
    """Test validate_all method passes schema to data quality validation."""
    # Create complete metadata with schema
    metadata = {
        "name": "test-dataset",
        "title": "Test Dataset",
        "description": "A test dataset for validation",
        "version": "1.0.0",
        "licenses": [
            {
                "name": "CC-BY-4.0",
                "path": "https://creativecommons.org/licenses/by/4.0/",
                "title": "Creative Commons Attribution 4.0",
            }
        ],
        "contributors": [
            {"title": "Test Author", "role": "author", "email": "author@example.com"}
        ],
        "sources": [{"title": "Test Source", "path": "https://example.com/data"}],
        "resources": [
            {"name": "main-data", "path": "data.csv", "schema": sample_schema}
        ],
    }

    result = validator.validate_all(metadata=metadata, df=valid_dataframe)

    # Should have no schema errors for valid data
    assert result is not None
    schema_errors = [e for e in result.errors if "schema_matching" in str(e)]
    assert len(schema_errors) == 0


def test_validate_all_with_invalid_data(validator, sample_schema):
    """Test validate_all detects schema violations in data."""
    # Create metadata with schema
    metadata = {
        "name": "test-dataset",
        "title": "Test Dataset",
        "description": "A test dataset for validation",
        "version": "1.0.0",
        "licenses": [
            {
                "name": "CC-BY-4.0",
                "path": "https://creativecommons.org/licenses/by/4.0/",
                "title": "Creative Commons Attribution 4.0",
            }
        ],
        "contributors": [
            {"title": "Test Author", "role": "author", "email": "author@example.com"}
        ],
        "sources": [{"title": "Test Source", "path": "https://example.com/data"}],
        "resources": [
            {"name": "main-data", "path": "data.csv", "schema": sample_schema}
        ],
    }

    # Create invalid DataFrame (string where number expected)
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
            "mass": ["not_a_number", "still_not", "nope"],  # Should be numeric!
            "temperature": [25.0, 30.0, 28.5],
            "is_active": [True, False, True],
            "count": [5, 10, 8],
        }
    )

    result = validator.validate_all(metadata=metadata, df=df)

    # Should have errors about type mismatch
    errors_str = " ".join([str(e) for e in result.errors])
    assert "mass" in errors_str


def test_inconsistencies_export_to_csv(validator, sample_schema, tmp_path):
    """Test that type inconsistencies can be exported to CSV."""
    import os

    # Create DataFrame with mixed types in 'name' column
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["A", 123, "C", 456, "E"],  # Mixed string and int
            "mass": [10.5, 20.3, 15.7, 18.2, 22.1],
            "temperature": [25.0, 30.0, 28.5, 27.0, 29.5],
            "is_active": [True, False, True, False, True],
            "count": [5, 10, 8, 12, 7],
        }
    )

    result = validator.validate_data_quality(df, schema=sample_schema)

    # Should have tracked inconsistencies
    assert len(result.inconsistencies) > 0

    # Export to CSV
    csv_path = tmp_path / "test_inconsistencies.csv"
    exported_path = result.export_inconsistencies_to_csv(str(csv_path))

    assert exported_path is not None
    assert os.path.exists(exported_path)

    # Read and verify CSV content
    import csv

    with open(exported_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Should have 2 inconsistent values (123 and 456 in 'name' column)
    assert len(rows) == 2
    assert all(row["column"] == "name" for row in rows)
    assert any(row["value"] == "123" for row in rows)
    assert any(row["value"] == "456" for row in rows)
    assert all(row["actual_type"] == "int" for row in rows)
    assert all(row["expected_type"] == "str" for row in rows)


def test_sanitize_resource_name(validator):
    """Test resource name sanitization."""
    # Test with invalid characters
    assert validator.sanitize_resource_name("My Resource!") == "my_resource"
    assert validator.sanitize_resource_name("Test@123#ABC") == "test123abc"
    assert validator.sanitize_resource_name("DATA FILE") == "data_file"

    # Test with special characters
    assert validator.sanitize_resource_name("20_mw+") == "20_mw"
    assert validator.sanitize_resource_name("test@#$%") == "test"

    # Test with dots
    assert validator.sanitize_resource_name(".test.name.") == "test.name"

    # Test with valid name
    assert validator.sanitize_resource_name("valid-name_123") == "valid-name_123"

    # Test empty string and None
    assert validator.sanitize_resource_name("") == "resource"
    assert validator.sanitize_resource_name("@#$%") == "resource"
    assert validator.sanitize_resource_name(None) == "resource"


def test_validate_and_sanitize_resource_name(validator):
    """Test resource name validation with sanitization."""
    # Valid name
    is_valid, name, suggestion = validator.validate_and_sanitize_resource_name(
        "valid-name"
    )
    assert is_valid is True
    assert name == "valid-name"
    assert suggestion is None

    # Invalid name - get suggestion
    is_valid, name, suggestion = validator.validate_and_sanitize_resource_name(
        "Invalid Name!"
    )
    assert is_valid is False
    assert name == "Invalid Name!"  # Original preserved when not auto_fix
    assert suggestion == "invalid_name"

    # Invalid name - auto fix
    is_valid, name, suggestion = validator.validate_and_sanitize_resource_name(
        "Invalid Name!", auto_fix=True
    )
    assert is_valid is False
    assert name == "invalid_name"  # Sanitized when auto_fix
    assert suggestion is None

    # Test None input
    is_valid, name, suggestion = validator.validate_and_sanitize_resource_name(None)
    assert is_valid is False
    assert name == ""
    assert suggestion == "resource"

    # Test None with auto_fix
    is_valid, name, suggestion = validator.validate_and_sanitize_resource_name(
        None, auto_fix=True
    )
    assert is_valid is False
    assert name == "resource"
    assert suggestion is None

    # Test empty string
    is_valid, name, suggestion = validator.validate_and_sanitize_resource_name("")
    assert is_valid is False
    assert name == ""
    assert suggestion == "resource"

    # Test whitespace only
    is_valid, name, suggestion = validator.validate_and_sanitize_resource_name("   ")
    assert is_valid is False
    assert name == "   "
    assert suggestion == "___"


def test_validate_resource_suggests_sanitized_name(validator):
    """Test that resource validation suggests sanitized names."""
    resource = {"name": "My Resource!", "path": "data.csv", "format": "csv"}

    result = validator.validate_resource(resource)

    # Should have a warning with suggested name
    warnings_str = " ".join([str(w) for w in result.warnings])
    assert "My Resource!" in warnings_str
    assert "my_resource" in warnings_str
    assert "Suggested name" in warnings_str or "suggested" in warnings_str.lower()
