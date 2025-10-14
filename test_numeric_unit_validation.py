#!/usr/bin/env python3
"""
Test script to verify that numeric fields require units.
"""

import sys
sys.path.insert(0, '/Users/ajakobs/Documents/brightcon2025_hackthon/trailpack')

from trailpack.packing.datapackage_schema import Field, Unit

def test_numeric_unit_validation():
    """Test that numeric fields require units."""
    
    print("Testing Numeric Field Unit Validation")
    print("=" * 50)
    
    # Test 1: Create a number field WITHOUT a unit (should fail)
    print("\n1. Testing number field without unit (should fail):")
    try:
        field_no_unit = Field(
            name="temperature",
            type="number",
            description="Temperature measurement"
        )
        print(f"✗ FAILED: Field was created without unit: {field_no_unit.name}")
    except ValueError as e:
        print(f"✓ PASSED: Correctly rejected numeric field without unit")
        print(f"  Error message: {e}")
    
    # Test 2: Create a number field WITH a unit (should succeed)
    print("\n2. Testing number field with unit (should succeed):")
    try:
        unit = Unit(
            name="°C",
            long_name="degree Celsius",
            path="http://qudt.org/vocab/unit/DEG_C"
        )
        field_with_unit = Field(
            name="temperature",
            type="number",
            description="Temperature measurement",
            unit=unit
        )
        print(f"✓ PASSED: Number field created with unit: {field_with_unit.name}")
        print(f"  Unit: {field_with_unit.unit.name} ({field_with_unit.unit.long_name})")
    except Exception as e:
        print(f"✗ FAILED: Could not create field with unit: {e}")
    
    # Test 3: Create an integer field WITHOUT a unit (should fail)
    print("\n3. Testing integer field without unit (should fail):")
    try:
        field_int_no_unit = Field(
            name="count",
            type="integer",
            description="Count of items"
        )
        print(f"✗ FAILED: Integer field was created without unit: {field_int_no_unit.name}")
    except ValueError as e:
        print(f"✓ PASSED: Correctly rejected integer field without unit")
        print(f"  Error message: {e}")
    
    # Test 4: Create an integer field WITH a unit (should succeed)
    print("\n4. Testing integer field with unit (should succeed):")
    try:
        unit_count = Unit(
            name="items",
            long_name="number of items",
            path="http://qudt.org/vocab/unit/NUM"
        )
        field_int_with_unit = Field(
            name="count",
            type="integer",
            description="Count of items",
            unit=unit_count
        )
        print(f"✓ PASSED: Integer field created with unit: {field_int_with_unit.name}")
        print(f"  Unit: {field_int_with_unit.unit.name}")
    except Exception as e:
        print(f"✗ FAILED: Could not create integer field with unit: {e}")
    
    # Test 5: Create a string field WITHOUT a unit (should succeed - strings don't need units)
    print("\n5. Testing string field without unit (should succeed):")
    try:
        field_string = Field(
            name="species",
            type="string",
            description="Species name"
        )
        print(f"✓ PASSED: String field created without unit: {field_string.name}")
    except Exception as e:
        print(f"✗ FAILED: String field should not require unit: {e}")
    
    # Test 6: Test the to_dict() method includes unit information
    print("\n6. Testing to_dict() includes unit information:")
    unit_kg = Unit(name="kg", long_name="kilogram", path="http://qudt.org/vocab/unit/KiloGM")
    field_mass = Field(
        name="mass",
        type="number",
        description="Object mass",
        unit=unit_kg
    )
    field_dict = field_mass.to_dict()
    print(f"✓ Field dictionary: {field_dict}")
    if 'unit' in field_dict:
        print(f"✓ PASSED: Unit information included in dictionary")
        print(f"  Unit data: {field_dict['unit']}")
    else:
        print(f"✗ FAILED: Unit information missing from dictionary")
    
    print("\n" + "=" * 50)
    print("Numeric field unit validation test completed!")

if __name__ == "__main__":
    test_numeric_unit_validation()
