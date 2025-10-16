"""
Test that columns without ontology mappings get meaningful descriptions.
"""

import pandas as pd

from trailpack.packing.export_service import DataPackageExporter


class TestColumnDescriptionWithoutOntology:
    """Test description handling for columns without ontology mappings."""

    def test_column_with_ontology_has_generic_description(self):
        """Test that columns with ontology mappings get generic description."""
        df = pd.DataFrame(
            {"temperature": [20.5, 21.0, 22.3], "pressure": [1013, 1012, 1015]}
        )

        column_mappings = {
            "temperature": "https://vocab.sentier.dev/model-terms/temperature",
            "temperature_unit": "https://vocab.sentier.dev/units/unit/DegreeCelsius",
        }

        general_details = {"name": "test-dataset", "title": "Test Dataset"}

        exporter = DataPackageExporter(
            df=df,
            column_mappings=column_mappings,
            general_details=general_details,
            sheet_name="TestSheet",
            file_name="test.xlsx",
        )

        fields = exporter.build_fields()

        # Temperature has ontology - should have generic description
        temp_field = next(f for f in fields if f.name == "temperature")
        assert temp_field.description == "Column from TestSheet"
        assert (
            temp_field.rdf_type == "https://vocab.sentier.dev/model-terms/temperature"
        )

    def test_column_without_ontology_has_column_name_in_description(self):
        """
        Test that columns without ontology mappings
        get column name in description.
        """
        df = pd.DataFrame(
            {
                "capacity": [100, 150, 200],
                "project_name": ["Alpha", "Beta", "Gamma"],
            }
        )

        column_mappings = {}  # No mappings

        general_details = {"name": "test-dataset", "title": "Test Dataset"}

        exporter = DataPackageExporter(
            df=df,
            column_mappings=column_mappings,
            general_details=general_details,
            sheet_name="ProjectData",
            file_name="projects.xlsx",
        )

        fields = exporter.build_fields()

        # capacity has no ontology - should have column name in description
        capacity_field = next(f for f in fields if f.name == "capacity")
        assert capacity_field.description == "capacity (from ProjectData)"
        assert capacity_field.rdf_type is None
        assert capacity_field.taxonomy_url is None

        # project_name has no ontology - should have column name in description
        project_field = next(f for f in fields if f.name == "project_name")
        assert project_field.description == "project_name (from ProjectData)"
        assert project_field.rdf_type is None
        assert project_field.taxonomy_url is None

    def test_custom_description_overrides_auto_generated(self):
        """Test that custom descriptions override auto-generated ones."""
        df = pd.DataFrame(
            {
                "capacity": [100, 150, 200],
                "temperature": [20.5, 21.0, 22.3],
                "notes": ["A", "B", "C"],
            }
        )

        column_mappings = {
            "temperature": "https://vocab.sentier.dev/model-terms/temperature",
            "temperature_unit": "https://vocab.sentier.dev/units/unit/DegreeCelsius",
        }

        column_descriptions = {
            "capacity": "Maximum power generation capacity in MW",
            "temperature": "Ambient temperature during measurement",
        }

        general_details = {"name": "test-dataset", "title": "Test Dataset"}

        exporter = DataPackageExporter(
            df=df,
            column_mappings=column_mappings,
            general_details=general_details,
            sheet_name="MeasurementData",
            file_name="data.xlsx",
            column_descriptions=column_descriptions,
        )

        fields = exporter.build_fields()

        # capacity has custom description - should use it
        capacity_field = next(f for f in fields if f.name == "capacity")
        assert capacity_field.description == "Maximum power generation capacity in MW"
        assert capacity_field.rdf_type is None

        # temperature has custom description - should override ontology description
        temp_field = next(f for f in fields if f.name == "temperature")
        assert temp_field.description == "Ambient temperature during measurement"
        assert (
            temp_field.rdf_type == "https://vocab.sentier.dev/model-terms/temperature"
        )

        # notes has no custom description and no ontology - should use auto-generated
        notes_field = next(f for f in fields if f.name == "notes")
        assert notes_field.description == "notes (from MeasurementData)"
        assert notes_field.rdf_type is None

    def test_mixed_columns_with_and_without_ontology(self):
        """Test that mixed columns (some with, some without ontology) work correctly."""
        df = pd.DataFrame(
            {
                "temperature": [20.5, 21.0, 22.3],
                "capacity": [100, 150, 200],
                "location": ["A", "B", "C"],
            }
        )

        column_mappings = {
            "temperature": "https://vocab.sentier.dev/model-terms/temperature",
            "temperature_unit": "https://vocab.sentier.dev/units/unit/DegreeCelsius",
            "location": "https://vocab.sentier.dev/Geonames/location",
        }

        general_details = {"name": "test-dataset", "title": "Test Dataset"}

        exporter = DataPackageExporter(
            df=df,
            column_mappings=column_mappings,
            general_details=general_details,
            sheet_name="MixedData",
            file_name="mixed.xlsx",
        )

        fields = exporter.build_fields()

        # temperature has ontology - generic description
        temp_field = next(f for f in fields if f.name == "temperature")
        assert temp_field.description == "Column from MixedData"
        assert (
            temp_field.rdf_type == "https://vocab.sentier.dev/model-terms/temperature"
        )

        # capacity has NO ontology - column name in description
        capacity_field = next(f for f in fields if f.name == "capacity")
        assert capacity_field.description == "capacity (from MixedData)"
        assert capacity_field.rdf_type is None

        # location has ontology - generic description
        location_field = next(f for f in fields if f.name == "location")
        assert location_field.description == "Column from MixedData"
        assert location_field.rdf_type == "https://vocab.sentier.dev/Geonames/location"


if __name__ == "__main__":
    # Run basic tests
    test_class = TestColumnDescriptionWithoutOntology()

    print("🧪 Running Description Tests for Non-Ontology Columns")
    print("=" * 60)

    try:
        print("Testing column with ontology...")
        test_class.test_column_with_ontology_has_generic_description()
        print("✅ Passed")

        print("Testing column without ontology...")
        test_class.test_column_without_ontology_has_column_name_in_description()
        print("✅ Passed")

        print("Testing mixed columns...")
        test_class.test_mixed_columns_with_and_without_ontology()
        print("✅ Passed")

        print("\n🎉 All tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
