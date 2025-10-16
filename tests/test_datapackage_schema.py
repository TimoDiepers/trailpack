"""
Test the DataPackage schema classes.
"""

import pytest
import json
from trailpack.packing.datapackage_schema import (
    DataPackageSchema,
    MetaDataBuilder,
    Field,
    FieldConstraints,
    Resource,
    Unit,
    COMMON_LICENSES
)


class TestDataPackageSchema:
    """Test the DataPackageSchema class."""
    
    def test_schema_initialization(self):
        """Test schema initializes correctly."""
        schema = DataPackageSchema()
        
        # Check that required fields list is correct
        required_fields = schema.get_required_fields()
        assert len(required_fields) == 7
        assert "name" in required_fields
        assert "resources" in required_fields
        assert "title" in required_fields
        assert "licenses" in required_fields
        assert "created" in required_fields
        assert "contributors" in required_fields
        assert "sources" in required_fields
        
        assert len(schema.get_recommended_fields()) > 0
        assert "description" in schema.get_recommended_fields()
    
    def test_field_definitions(self):
        """Test field definitions are properly structured."""
        schema = DataPackageSchema()
        
        name_def = schema.get_field_definition("name")
        assert name_def["required"] is True
        assert name_def["type"] == "string"
        assert "pattern" in name_def
        
        title_def = schema.get_field_definition("title") 
        assert title_def["required"] is False
        assert title_def["type"] == "string"
    
    def test_package_name_validation(self):
        """Test package name validation."""
        schema = DataPackageSchema()
        
        # Valid names
        valid, _ = schema.validate_package_name("my-dataset")
        assert valid is True
        
        valid, _ = schema.validate_package_name("dataset_123")
        assert valid is True
        
        # Invalid names
        valid, error = schema.validate_package_name("My Dataset")
        assert valid is False
        assert "lowercase" in error
        
        valid, error = schema.validate_package_name("")
        assert valid is False
        assert "required" in error
        
        valid, error = schema.validate_package_name(".hidden")
        assert valid is False
        assert "dot" in error
    
    def test_version_validation(self):
        """Test semantic version validation."""
        schema = DataPackageSchema()
        
        # Valid versions
        valid, _ = schema.validate_version("1.0.0")
        assert valid is True
        
        valid, _ = schema.validate_version("1.2.3-beta")
        assert valid is True
        
        valid, _ = schema.validate_version("")  # Empty is ok (optional)
        assert valid is True
        
        # Invalid versions
        valid, error = schema.validate_version("1.0")
        assert valid is False
        assert "semantic" in error
        
        valid, error = schema.validate_version("not-a-version")
        assert valid is False
    
    def test_url_validation(self):
        """Test URL validation."""
        schema = DataPackageSchema()
        
        # Valid URLs
        valid, _ = schema.validate_url("https://example.com")
        assert valid is True
        
        valid, _ = schema.validate_url("http://test.org/path")
        assert valid is True
        
        valid, _ = schema.validate_url("")  # Empty is ok (optional)
        assert valid is True
        
        # Invalid URLs
        valid, error = schema.validate_url("ftp://example.com")
        assert valid is False
        assert "http" in error


class TestMetaDataBuilder:
    """Test the MetaDataBuilder class."""
    
    def test_basic_builder_workflow(self):
        """Test basic builder workflow."""
        builder = MetaDataBuilder()
        
        # Set basic info
        builder.set_basic_info(
            name="test-dataset",
            title="Test Dataset", 
            description="A test dataset",
            version="1.0.0"
        )
        
        # Add license
        builder.add_license("MIT", "MIT License")
        
        # Add contributor
        builder.add_contributor("Test User", "author", "test@example.com")
        
        # Add source (now required)
        builder.add_source("Test Source", "https://example.com")
        
        # Add resource
        resource = Resource(
            name="data",
            path="data.csv",
            description="Main data file"
        )
        builder.add_resource(resource)
        
        # Build metadata
        metadata = builder.build()
        
        # Verify structure
        assert metadata["name"] == "test-dataset"
        assert metadata["title"] == "Test Dataset"
        assert len(metadata["licenses"]) == 1
        assert len(metadata["contributors"]) == 1
        assert len(metadata["sources"]) == 1
        assert len(metadata["resources"]) == 1
        
        # Verify it's valid JSON
        json_str = json.dumps(metadata)
        parsed = json.loads(json_str)
        assert parsed["name"] == "test-dataset"
    
    def test_builder_validation(self):
        """Test builder validation."""
        builder = MetaDataBuilder()
        
        # Should fail without name
        with pytest.raises(ValueError, match="package name"):
            builder.set_basic_info(name="Invalid Name!")
        
        # Should fail without resources
        builder.set_basic_info(name="valid-name")
        with pytest.raises(ValueError, match="resource"):
            builder.build()
    
    def test_fluent_interface(self):
        """Test fluent interface chaining."""
        metadata = (MetaDataBuilder()
                   .set_basic_info(name="fluent-test", title="Fluent Test")
                   .set_profile("tabular-data-package") 
                   .set_keywords(["test", "fluent"])
                   .add_license("CC0-1.0")
                   .add_contributor("Test Author")
                   .add_source("Test Source", "https://example.com")
                   .add_resource(Resource(name="data", path="test.csv"))
                   .build())
        
        assert metadata["name"] == "fluent-test"
        assert metadata["profile"] == "tabular-data-package"
        assert "test" in metadata["keywords"]
        assert len(metadata["licenses"]) == 1
        assert len(metadata["contributors"]) == 1
        assert len(metadata["sources"]) == 1
        assert len(metadata["resources"]) == 1


class TestFieldAndResource:
    """Test Field and Resource classes."""
    
    def test_field_creation(self):
        """Test field creation and serialization."""
        constraints = FieldConstraints(
            required=True,
            minimum=0,
            maximum=100
        )
        
        unit = Unit(
            name="°C",
            long_name="degree Celsius",
            path="http://qudt.org/vocab/unit/DegreeCelsius"
        )
        
        field = Field(
            name="temperature",
            type="number",
            description="Temperature measurement",
            unit=unit,
            constraints=constraints
        )
        
        field_dict = field.to_dict()
        
        assert field_dict["name"] == "temperature"
        assert field_dict["type"] == "number" 
        assert field_dict["unit"]["name"] == "°C"
        assert field_dict["unit"]["longName"] == "degree Celsius"
        assert field_dict["constraints"]["required"] is True
        assert field_dict["constraints"]["minimum"] == 0
    
    def test_resource_with_schema(self):
        """Test resource with field schema."""
        # Create unit for dimensionless number (id)
        id_unit = Unit(
            name="NUM",
            long_name="dimensionless number",
            path="https://vocab.sentier.dev/web/concept/https%3A//vocab.sentier.dev/units/unit/NUM?concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2Funits%2F&language=en"
        )
        
        fields = [
            Field(name="id", type="integer", description="Identifier", unit=id_unit),
            Field(name="name", type="string", description="Name")
        ]
        
        resource = Resource(
            name="test-resource",
            path="test.csv",
            description="Test resource",
            fields=fields,
            primary_key=["id"]
        )
        
        resource_dict = resource.to_dict()
        
        assert resource_dict["name"] == "test-resource"
        assert "schema" in resource_dict
        assert len(resource_dict["schema"]["fields"]) == 2
        assert resource_dict["schema"]["primaryKey"] == ["id"]
    
    def test_numeric_field_requires_unit(self):
        """Test that numeric fields must have a unit."""
        # Should raise error for number without unit
        with pytest.raises(ValueError, match="no unit specified"):
            Field(
                name="temperature",
                type="number",
                description="Temperature measurement"
            )
        
        # Should raise error for integer without unit
        with pytest.raises(ValueError, match="no unit specified"):
            Field(
                name="count",
                type="integer",
                description="Count of items"
            )
        
        # Should succeed with unit for number
        unit_temp = Unit(name="°C", long_name="degree Celsius", path="http://qudt.org/vocab/unit/DEG_C")
        field_with_unit = Field(
            name="temperature",
            type="number",
            description="Temperature measurement",
            unit=unit_temp
        )
        assert field_with_unit.unit.name == "°C"
        
        # Should succeed with dimensionless unit for integer
        unit_dim = Unit(name="dimensionless", long_name="dimensionless number", path="http://qudt.org/vocab/unit/NUM")
        field_int_with_unit = Field(
            name="count",
            type="integer",
            description="Count of items",
            unit=unit_dim
        )
        assert field_int_with_unit.unit.name == "dimensionless"
        
        # Non-numeric fields should not require unit
        field_string = Field(
            name="name",
            type="string",
            description="Name field"
        )
        assert field_string.unit is None


class TestUnitClass:
    """Test the Unit class."""
    
    def test_unit_minimal(self):
        """Test creating a Unit with only name (minimal)."""
        unit = Unit(name="m")
        assert unit.name == "m"
        assert unit.long_name is None
        assert unit.path is None
        
        unit_dict = unit.to_dict()
        assert unit_dict["name"] == "m"
        # Optional fields should not be in dict if None
        assert "longName" not in unit_dict or unit_dict.get("longName") is None
    
    def test_unit_full(self):
        """Test creating a Unit with all parameters."""
        unit = Unit(
            name="kg",
            long_name="kilogram",
            path="http://qudt.org/vocab/unit/KiloGM"
        )
        assert unit.name == "kg"
        assert unit.long_name == "kilogram"
        assert unit.path == "http://qudt.org/vocab/unit/KiloGM"
        
        unit_dict = unit.to_dict()
        assert unit_dict["name"] == "kg"
        assert unit_dict["longName"] == "kilogram"
        assert unit_dict["path"] == "http://qudt.org/vocab/unit/KiloGM"
    
    def test_unit_invalid_url(self):
        """Test that invalid URLs are caught."""
        # Should raise error for invalid URL
        with pytest.raises(ValueError, match="path must be a valid URL"):
            Unit(
                name="m",
                path="not-a-valid-url"
            )
    
    def test_field_templates_have_units(self):
        """Test that FIELD_TEMPLATES numeric fields have units."""
        from trailpack.packing.datapackage_schema import FIELD_TEMPLATES
        
        # Check latitude template
        lat_template = FIELD_TEMPLATES["latitude"]
        assert lat_template.name == "latitude"
        assert lat_template.type == "number"
        assert lat_template.unit is not None
        assert lat_template.unit.name == "DEG"
        assert "degree" in lat_template.unit.long_name.lower()
        assert lat_template.unit.path is not None
        
        # Check longitude template
        lon_template = FIELD_TEMPLATES["longitude"]
        assert lon_template.name == "longitude"
        assert lon_template.type == "number"
        assert lon_template.unit is not None
        assert lon_template.unit.name == "DEG"


class TestCommonLicenses:
    """Test common license definitions."""
    
    def test_common_licenses_structure(self):
        """Test common licenses are properly structured."""
        assert "CC-BY-4.0" in COMMON_LICENSES
        assert "MIT" in COMMON_LICENSES
        
        cc_license = COMMON_LICENSES["CC-BY-4.0"]
        assert cc_license["name"] == "CC-BY-4.0"
        assert "Creative Commons" in cc_license["title"]
        assert cc_license["path"].startswith("https://")


if __name__ == "__main__":
    # Run basic tests
    test_schema = TestDataPackageSchema()
    test_builder = TestMetaDataBuilder()
    test_field = TestFieldAndResource()
    test_licenses = TestCommonLicenses()
    
    print("🧪 Running DataPackage Schema Tests")
    print("=" * 40)
    
    try:
        print("Testing schema initialization...")
        test_schema.test_schema_initialization()
        test_schema.test_field_definitions()
        print("✅ Schema tests passed")
        
        print("Testing validation...")
        test_schema.test_package_name_validation()
        test_schema.test_version_validation() 
        test_schema.test_url_validation()
        print("✅ Validation tests passed")
        
        print("Testing builder...")
        test_builder.test_basic_builder_workflow()
        test_builder.test_fluent_interface()
        print("✅ Builder tests passed")
        
        print("Testing fields and resources...")
        test_field.test_field_creation()
        test_field.test_resource_with_schema()
        print("✅ Field/resource tests passed")
        
        print("Testing common licenses...")
        test_licenses.test_common_licenses_structure()
        print("✅ License tests passed")
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()