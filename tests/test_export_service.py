"""Tests for the DataPackageExporter service."""

import pytest
import pandas as pd
from pathlib import Path

from trailpack.packing.export_service import DataPackageExporter


class TestResourceNameSanitization:
    """Test resource name sanitization to match validation pattern."""
    
    def test_sanitize_resource_name_with_plus_sign(self):
        """Test that plus signs are removed from resource names."""
        df = pd.DataFrame({"col1": [1, 2, 3]})
        column_mappings = {}
        general_details = {
            "name": "test-package",
            "title": "Test Package"
        }
        
        exporter = DataPackageExporter(
            df=df,
            column_mappings=column_mappings,
            general_details=general_details,
            sheet_name="20_MW+",
            file_name="example_global-solar-power-tracker-february-2025.xlsx"
        )
        
        # Test the sanitization method directly
        sanitized = exporter._sanitize_resource_name("20_mw+")
        assert sanitized == "20_mw"
        assert "+" not in sanitized
    
    def test_sanitize_resource_name_with_special_characters(self):
        """Test that various special characters are removed."""
        df = pd.DataFrame({"col1": [1, 2, 3]})
        column_mappings = {}
        general_details = {
            "name": "test-package",
            "title": "Test Package"
        }
        
        exporter = DataPackageExporter(
            df=df,
            column_mappings=column_mappings,
            general_details=general_details,
            sheet_name="test",
            file_name="test.xlsx"
        )
        
        # Test various special characters
        test_cases = [
            ("file@name#with$symbols", "filenamewiththsymbols"),
            ("test (with) parentheses", "test_with_parentheses"),
            ("test&name", "testname"),
            ("test*name", "testname"),
            ("test%name", "testname"),
            ("test!name", "testname"),
        ]
        
        for input_name, expected in test_cases:
            sanitized = exporter._sanitize_resource_name(input_name)
            # Check it matches the pattern
            import re
            assert re.match(r"^[a-z0-9\-_.]+$", sanitized), f"'{sanitized}' doesn't match pattern"
    
    def test_sanitize_resource_name_preserves_valid_characters(self):
        """Test that valid characters are preserved."""
        df = pd.DataFrame({"col1": [1, 2, 3]})
        column_mappings = {}
        general_details = {
            "name": "test-package",
            "title": "Test Package"
        }
        
        exporter = DataPackageExporter(
            df=df,
            column_mappings=column_mappings,
            general_details=general_details,
            sheet_name="test",
            file_name="test.xlsx"
        )
        
        # Valid characters should be preserved
        valid_name = "test-name_123.data"
        sanitized = exporter._sanitize_resource_name(valid_name)
        assert sanitized == valid_name
    
    def test_sanitize_resource_name_handles_uppercase(self):
        """Test that uppercase letters are converted to lowercase."""
        df = pd.DataFrame({"col1": [1, 2, 3]})
        column_mappings = {}
        general_details = {
            "name": "test-package",
            "title": "Test Package"
        }
        
        exporter = DataPackageExporter(
            df=df,
            column_mappings=column_mappings,
            general_details=general_details,
            sheet_name="test",
            file_name="test.xlsx"
        )
        
        sanitized = exporter._sanitize_resource_name("TEST_Name_123")
        assert sanitized == "test_name_123"
        assert sanitized.islower() or any(c.isdigit() or c in '-_.' for c in sanitized)
    
    def test_sanitize_resource_name_handles_dots(self):
        """Test that leading/trailing dots are removed."""
        df = pd.DataFrame({"col1": [1, 2, 3]})
        column_mappings = {}
        general_details = {
            "name": "test-package",
            "title": "Test Package"
        }
        
        exporter = DataPackageExporter(
            df=df,
            column_mappings=column_mappings,
            general_details=general_details,
            sheet_name="test",
            file_name="test.xlsx"
        )
        
        # Leading/trailing dots should be removed
        sanitized = exporter._sanitize_resource_name(".test.name.")
        assert sanitized == "test.name"
        assert not sanitized.startswith(".")
        assert not sanitized.endswith(".")
    
    def test_sanitize_resource_name_handles_empty_string(self):
        """Test that empty strings or all-invalid characters get default name."""
        df = pd.DataFrame({"col1": [1, 2, 3]})
        column_mappings = {}
        general_details = {
            "name": "test-package",
            "title": "Test Package"
        }
        
        exporter = DataPackageExporter(
            df=df,
            column_mappings=column_mappings,
            general_details=general_details,
            sheet_name="test",
            file_name="test.xlsx"
        )
        
        # Empty or all-invalid characters should get default name
        sanitized = exporter._sanitize_resource_name("@#$%^&*()")
        assert sanitized == "resource"
        
        sanitized = exporter._sanitize_resource_name("")
        assert sanitized == "resource"
    
    def test_build_resource_creates_valid_name(self):
        """Test that build_resource creates a valid resource name."""
        df = pd.DataFrame({"col1": [1, 2, 3]})
        column_mappings = {
            "col1": "https://example.com/concept/1",
            "col1_unit": "https://vocab.sentier.dev/units/unit/NUM"
        }
        general_details = {
            "name": "test-package",
            "title": "Test Package",
            "description": "Test description"
        }
        
        # Test with problematic file and sheet names
        exporter = DataPackageExporter(
            df=df,
            column_mappings=column_mappings,
            general_details=general_details,
            sheet_name="20_MW+",
            file_name="example_global-solar-power-tracker-february-2025.xlsx"
        )
        
        fields = exporter.build_fields()
        resource = exporter.build_resource(fields)
        
        # Check the resource name matches the pattern
        import re
        pattern = r"^[a-z0-9\-_.]+$"
        assert re.match(pattern, resource.name), f"Resource name '{resource.name}' doesn't match pattern"
        assert "+" not in resource.name
        assert " " not in resource.name
