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
    COMMON_LICENSES
)


class TestDataPackageSchema:
    """Test the DataPackageSchema class."""
    
    def test_schema_initialization(self):
        """Test schema initializes correctly."""
        schema = DataPackageSchema()
        
        assert len(schema.get_required_fields()) == 2
        assert "name" in schema.get_required_fields()
        assert "resources" in schema.get_required_fields()
        
        assert len(schema.get_recommended_fields()) > 0
        assert "title" in schema.get_recommended_fields()
    
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
                   .add_resource(Resource(name="data", path="test.csv"))
                   .build())
        
        assert metadata["name"] == "fluent-test"
        assert metadata["profile"] == "tabular-data-package"
        assert "test" in metadata["keywords"]
        assert len(metadata["licenses"]) == 1
        assert len(metadata["contributors"]) == 1
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
        
        field = Field(
            name="temperature",
            type="number",
            description="Temperature measurement",
            unit="°C",
            unit_code="http://qudt.org/vocab/unit/DegreeCelsius",
            constraints=constraints
        )
        
        field_dict = field.to_dict()
        
        assert field_dict["name"] == "temperature"
        assert field_dict["type"] == "number" 
        assert field_dict["unit"] == "°C"
        assert field_dict["constraints"]["required"] is True
        assert field_dict["constraints"]["minimum"] == 0
    
    def test_resource_with_schema(self):
        """Test resource with field schema."""
        fields = [
            Field(name="id", type="integer", description="Identifier"),
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