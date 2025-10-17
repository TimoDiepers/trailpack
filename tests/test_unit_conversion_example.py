"""Tests for the unit conversion and concatenation example."""

import pytest
import pandas as pd
import json
from pathlib import Path
import sys

# Add examples to path
sys.path.insert(0, str(Path(__file__).parent.parent / "examples"))

from unit_conversion_concatenation import (
    read_parquet_with_metadata,
    convert_column_units,
    concatenate_with_unit_conversion,
)


class TestReadParquetWithMetadata:
    """Test reading parquet files with metadata."""

    def test_read_kg_file(self):
        """Test reading a file with kg units."""
        df, metadata = read_parquet_with_metadata("tests/data/sample_kg.parquet")
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "mass" in df.columns
        assert metadata["columns"]["mass"]["unit"] == "kilogram"
        assert metadata["columns"]["mass"]["unit_symbol"] == "kg"

    def test_read_g_file(self):
        """Test reading a file with gram units."""
        df, metadata = read_parquet_with_metadata("tests/data/sample_g.parquet")
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "mass" in df.columns
        assert metadata["columns"]["mass"]["unit"] == "gram"
        assert metadata["columns"]["mass"]["unit_symbol"] == "g"

    def test_dataframe_structure(self):
        """Test that dataframe has expected structure."""
        df, _ = read_parquet_with_metadata("tests/data/sample_kg.parquet")
        
        expected_columns = ["location", "timestamp", "mass"]
        assert df.columns.tolist() == expected_columns
        assert df["location"].dtype == "object"
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
        assert df["mass"].dtype == "float64"


class TestConvertColumnUnits:
    """Test unit conversion functionality."""

    def test_gram_to_kilogram_conversion(self):
        """Test converting grams to kilograms."""
        df = pd.DataFrame({"mass": [1000.0, 2000.0, 3000.0]})
        
        converted_df = convert_column_units(df, "mass", "gram", "kilogram")
        
        assert converted_df["mass"].tolist() == [1.0, 2.0, 3.0]

    def test_kilogram_to_gram_conversion(self):
        """Test converting kilograms to grams."""
        df = pd.DataFrame({"mass": [1.0, 2.0, 3.0]})
        
        converted_df = convert_column_units(df, "mass", "kilogram", "gram")
        
        assert converted_df["mass"].tolist() == [1000.0, 2000.0, 3000.0]

    def test_same_unit_conversion(self):
        """Test that converting to same unit doesn't change values."""
        df = pd.DataFrame({"mass": [1.5, 2.5, 3.5]})
        
        converted_df = convert_column_units(df, "mass", "kilogram", "kilogram")
        
        assert converted_df["mass"].tolist() == [1.5, 2.5, 3.5]

    def test_conversion_does_not_modify_original(self):
        """Test that conversion creates a copy and doesn't modify original."""
        df = pd.DataFrame({"mass": [1000.0, 2000.0]})
        original_values = df["mass"].copy()
        
        converted_df = convert_column_units(df, "mass", "gram", "kilogram")
        
        # Original should be unchanged
        assert df["mass"].tolist() == original_values.tolist()
        # Converted should be different
        assert converted_df["mass"].tolist() != original_values.tolist()


class TestConcatenateWithUnitConversion:
    """Test concatenation with unit conversion."""

    def test_concatenate_two_files(self):
        """Test concatenating two files with different units."""
        filepaths = [
            "tests/data/sample_kg.parquet",
            "tests/data/sample_g.parquet"
        ]
        
        concatenated_df, metadata = concatenate_with_unit_conversion(
            filepaths,
            target_unit="kilogram",
            target_unit_symbol="kg"
        )
        
        # Check concatenation
        assert len(concatenated_df) == 6  # 3 rows from each file
        assert "mass" in concatenated_df.columns
        
        # Check metadata
        assert metadata["target_unit"] == "kilogram"
        assert metadata["target_unit_symbol"] == "kg"
        assert metadata["total_rows"] == 6
        assert len(metadata["source_files"]) == 2

    def test_mass_values_are_converted(self):
        """Test that mass values are properly converted to kg."""
        filepaths = [
            "tests/data/sample_kg.parquet",
            "tests/data/sample_g.parquet"
        ]
        
        concatenated_df, _ = concatenate_with_unit_conversion(
            filepaths,
            target_unit="kilogram",
            target_unit_symbol="kg"
        )
        
        # The gram file has values [2500, 8000, 6200]
        # which should be converted to [2.5, 8.0, 6.2] kg
        # The kg file has values [4.5, 10.2, 7.8]
        
        # Check that all values are in a reasonable kg range (not g range)
        assert concatenated_df["mass"].max() < 20  # Should be around 10.2 kg
        assert concatenated_df["mass"].min() > 1   # Should be around 2.5 kg
        
        # Check specific converted values (from gram file)
        gram_rows = concatenated_df.iloc[3:6]  # Last 3 rows are from gram file
        expected_masses = [2.5, 8.0, 6.2]
        actual_masses = gram_rows["mass"].tolist()
        
        for expected, actual in zip(expected_masses, actual_masses):
            assert abs(expected - actual) < 0.01  # Allow small floating point differences

    def test_all_columns_preserved(self):
        """Test that all columns are preserved after concatenation."""
        filepaths = [
            "tests/data/sample_kg.parquet",
            "tests/data/sample_g.parquet"
        ]
        
        concatenated_df, _ = concatenate_with_unit_conversion(filepaths)
        
        expected_columns = ["location", "timestamp", "mass"]
        assert concatenated_df.columns.tolist() == expected_columns

    def test_timestamp_types_preserved(self):
        """Test that timestamp column types are preserved."""
        filepaths = [
            "tests/data/sample_kg.parquet",
            "tests/data/sample_g.parquet"
        ]
        
        concatenated_df, _ = concatenate_with_unit_conversion(filepaths)
        
        assert pd.api.types.is_datetime64_any_dtype(concatenated_df["timestamp"])

    def test_concatenation_order(self):
        """Test that rows maintain order from input files."""
        filepaths = [
            "tests/data/sample_kg.parquet",
            "tests/data/sample_g.parquet"
        ]
        
        concatenated_df, _ = concatenate_with_unit_conversion(filepaths)
        
        # First file locations should come first
        first_three_locations = concatenated_df["location"].iloc[:3].tolist()
        assert first_three_locations == ["New York", "Berlin", "Tokyo"]
        
        # Second file locations should come after
        last_three_locations = concatenated_df["location"].iloc[3:].tolist()
        assert last_three_locations == ["London", "Paris", "Sydney"]


class TestExampleExecution:
    """Test that the example can be executed."""

    def test_example_files_exist(self):
        """Test that required example data files exist."""
        assert Path("tests/data/sample_kg.parquet").exists()
        assert Path("tests/data/sample_g.parquet").exists()

    def test_can_import_example_module(self):
        """Test that the example module can be imported."""
        import unit_conversion_concatenation
        
        assert hasattr(unit_conversion_concatenation, "main")
        assert hasattr(unit_conversion_concatenation, "concatenate_with_unit_conversion")
        assert hasattr(unit_conversion_concatenation, "convert_column_units")


@pytest.mark.anyio
async def test_get_unit_info_from_pyst_handles_errors():
    """Test that get_unit_info_from_pyst handles API errors gracefully."""
    from unit_conversion_concatenation import get_unit_info_from_pyst
    
    # This will likely fail in test environment (no API access)
    # but should return None or a fallback URI, not raise an exception
    result = await get_unit_info_from_pyst("kilogram", "en")
    
    # Should return either None or a valid URI
    assert result is None or result.startswith("http://")


@pytest.mark.anyio
async def test_create_datapackage_with_pyst():
    """Test creating a data package with PyST metadata."""
    from unit_conversion_concatenation import create_datapackage_with_pyst
    
    # Create a simple test dataframe
    df = pd.DataFrame({
        "location": ["Test"],
        "timestamp": pd.to_datetime(["2025-01-01"]),
        "mass": [1.0]
    })
    
    # Create metadata
    metadata = await create_datapackage_with_pyst(
        df,
        name="test-package",
        title="Test Package",
        description="Test description",
        output_path="test.parquet"
    )
    
    # Verify metadata structure
    assert "name" in metadata
    assert metadata["name"] == "test-package"
    assert "resources" in metadata
    assert len(metadata["resources"]) == 1
    
    # Verify field definitions
    fields = metadata["resources"][0]["schema"]["fields"]
    assert len(fields) == 3
    
    # Check mass field has unit
    mass_field = next(f for f in fields if f["name"] == "mass")
    assert "unit" in mass_field
    assert mass_field["unit"]["name"] == "kg"
