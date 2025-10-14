#!/usr/bin/env python3
"""
Test script to verify the new Unit class in Field definitions.
"""

import sys
sys.path.insert(0, '/Users/ajakobs/Documents/brightcon2025_hackthon/trailpack')

from trailpack.packing.datapackage_schema import Unit, Field, FieldConstraints

def test_unit_class():
    """Test the Unit class functionality."""
    
    print("Testing Unit Class Implementation")
    print("=" * 50)
    
    # Test 1: Create a simple unit
    print("\n1. Creating a simple unit (kg):")
    try:
        kg_unit = Unit(
            name="kg",
            long_name="kilogram",
            path="http://qudt.org/vocab/unit/KiloGM"
        )
        print(f"✓ Unit created: {kg_unit.name}")
        print(f"  Long name: {kg_unit.long_name}")
        print(f"  Path: {kg_unit.path}")
        print(f"  Dict format: {kg_unit.to_dict()}")
    except Exception as e:
        print(f"✗ Error creating unit: {e}")
    
    # Test 2: Create unit with only name (minimal)
    print("\n2. Creating minimal unit (only name):")
    try:
        simple_unit = Unit(name="m")
        print(f"✓ Minimal unit created: {simple_unit.name}")
        print(f"  Dict format: {simple_unit.to_dict()}")
    except Exception as e:
        print(f"✗ Error creating minimal unit: {e}")
    
    # Test 3: Test invalid unit path
    print("\n3. Testing invalid unit path:")
    try:
        bad_unit = Unit(
            name="m",
            path="not-a-valid-url"
        )
        print(f"✗ Should have failed URL validation")
    except ValueError as e:
        print(f"✓ Correctly caught invalid URL: {e}")
    
    # Test 4: Create a Field with Unit
    print("\n4. Creating Field with Unit:")
    try:
        temp_field = Field(
            name="temperature",
            type="number",
            description="Temperature measurement",
            unit=Unit(
                name="celsius",
                long_name="degree Celsius",
                path="http://qudt.org/vocab/unit/DEG_C"
            ),
            constraints=FieldConstraints(minimum=-273.15, maximum=1000.0)
        )
        print(f"✓ Field created: {temp_field.name}")
        print(f"  Unit: {temp_field.unit.name} ({temp_field.unit.long_name})")
        print(f"\nField as dict:")
        field_dict = temp_field.to_dict()
        for key, value in field_dict.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"✗ Error creating field with unit: {e}")
    
    # Test 5: Create Field without unit (optional)
    print("\n5. Creating Field without unit:")
    try:
        name_field = Field(
            name="product_name",
            type="string",
            description="Product name"
        )
        print(f"✓ Field created without unit: {name_field.name}")
        print(f"  Dict format: {name_field.to_dict()}")
    except Exception as e:
        print(f"✗ Error creating field without unit: {e}")
    
    # Test 6: Test FIELD_TEMPLATES
    print("\n6. Testing updated FIELD_TEMPLATES:")
    from trailpack.packing.datapackage_schema import FIELD_TEMPLATES
    
    lat_template = FIELD_TEMPLATES["latitude"]
    print(f"✓ Latitude template loaded")
    print(f"  Name: {lat_template.name}")
    print(f"  Type: {lat_template.type}")
    print(f"  Unit: {lat_template.unit.name} ({lat_template.unit.long_name})")
    print(f"  Unit path: {lat_template.unit.path}")
    print(f"\nLatitude template as dict:")
    for key, value in lat_template.to_dict().items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 50)
    print("Unit class test completed!")
    print("Unit class now provides structured metadata for units of measurement.")

if __name__ == "__main__":
    test_unit_class()
