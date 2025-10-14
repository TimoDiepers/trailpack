#!/usr/bin/env python3
"""
Test script to verify Pydantic conversion of DataPackage schema classes.
"""

import sys
sys.path.insert(0, '/Users/ajakobs/Documents/brightcon2025_hackthon/trailpack')

from trailpack.packing.datapackage_schema import (
    License, Contributor, Source, FieldConstraints, Field, Resource, DataPackageSchema
)

def test_pydantic_models():
    """Test that all Pydantic models work correctly."""
    
    print("Testing Pydantic DataPackage Schema Classes")
    print("=" * 50)
    
    # Test License with validation
    print("\n1. Testing License class:")
    try:
        license_obj = License(
            name="CC-BY-4.0",
            title="Creative Commons Attribution 4.0",
            path="https://creativecommons.org/licenses/by/4.0/"
        )
        print(f"✓ License created: {license_obj.name}")
        print(f"  Dict format: {license_obj.to_dict()}")
    except Exception as e:
        print(f"✗ License validation error: {e}")
    
    # Test invalid URL
    try:
        bad_license = License(name="MIT", path="not-a-url")
        print(f"✗ Should have failed URL validation")
    except ValueError as e:
        print(f"✓ Correctly caught invalid URL: {e}")
    
    # Test Contributor with email validation
    print("\n2. Testing Contributor class:")
    try:
        contributor = Contributor(
            name="John Doe", 
            email="john@example.com",
            role="author",
            organization="Example Org"
        )
        print(f"✓ Contributor created: {contributor.name}")
        print(f"  Dict format: {contributor.to_dict()}")
    except Exception as e:
        print(f"✗ Contributor validation error: {e}")
    
    # Test invalid email
    try:
        bad_contributor = Contributor(name="Jane", email="invalid-email")
        print(f"✗ Should have failed email validation")
    except ValueError as e:
        print(f"✓ Correctly caught invalid email: {e}")
    
    # Test invalid role
    try:
        bad_role = Contributor(name="Bob", role="invalid-role")
        print(f"✗ Should have failed role validation")
    except ValueError as e:
        print(f"✓ Correctly caught invalid role: {e}")
    
    # Test FieldConstraints with regex validation
    print("\n3. Testing FieldConstraints class:")
    try:
        constraints = FieldConstraints(
            required=True,
            pattern=r'^[A-Z]{3}$',
            minimum=0,
            maximum=100
        )
        print(f"✓ FieldConstraints created with pattern validation")
        print(f"  Dict format: {constraints.to_dict()}")
    except Exception as e:
        print(f"✗ FieldConstraints validation error: {e}")
    
    # Test invalid regex
    try:
        bad_constraints = FieldConstraints(pattern="[invalid regex")
        print(f"✗ Should have failed regex validation")
    except ValueError as e:
        print(f"✓ Correctly caught invalid regex: {e}")
    
    # Test Field with type validation
    print("\n4. Testing Field class:")
    try:
        field = Field(
            name="temperature",
            type="number",
            description="Temperature measurement",
            unit="celsius",
            unit_code="http://qudt.org/vocab/unit/DEG_C",
            constraints=constraints
        )
        print(f"✓ Field created: {field.name}")
        print(f"  Dict format: {field.to_dict()}")
    except Exception as e:
        print(f"✗ Field validation error: {e}")
    
    # Test invalid field type
    try:
        bad_field = Field(name="test", type="invalid-type")
        print(f"✗ Should have failed type validation")
    except ValueError as e:
        print(f"✓ Correctly caught invalid field type: {e}")
    
    # Test Resource with encoding validation
    print("\n5. Testing Resource class:")
    try:
        resource = Resource(
            name="data",
            path="data.csv",
            title="Sample Data",
            format="csv",
            encoding="utf-8",
            fields=[field],
            primary_key=["id"]
        )
        print(f"✓ Resource created: {resource.name}")
        print(f"  Dict format keys: {list(resource.to_dict().keys())}")
    except Exception as e:
        print(f"✗ Resource validation error: {e}")
    
    # Test invalid encoding
    try:
        bad_resource = Resource(name="test", path="test.csv", encoding="invalid-encoding")
        print(f"✗ Should have failed encoding validation")
    except ValueError as e:
        print(f"✓ Correctly caught invalid encoding: {e}")
    
    print("\n" + "=" * 50)
    print("Pydantic conversion test completed!")
    print("All classes now have automatic validation and type checking.")

if __name__ == "__main__":
    test_pydantic_models()