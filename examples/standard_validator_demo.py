"""
Example usage of StandardValidator.

Demonstrates how to validate data packages against the Trailpack standard.
"""

from trailpack.validation import StandardValidator, list_available_standards
from trailpack.packing.datapackage_schema import (
    MetaDataBuilder,
    Resource,
    Field,
    Unit,
    FieldConstraints,
)
import pandas as pd


def example_valid_metadata():
    """Create a valid metadata example."""
    print("\n" + "="*60)
    print("Example 1: Valid Metadata")
    print("="*60)
    
    # Build valid metadata using the builder
    builder = MetaDataBuilder()
    metadata = (builder
        .set_basic_info(
            name="solar-panel-lca",
            title="Life Cycle Assessment of Solar Panels 2024",
            description="Comprehensive LCA data for various solar panel technologies including manufacturing, transportation, and end-of-life scenarios. Data collected from 50+ manufacturers across Europe and Asia.",
            version="1.0.0"
        )
        .set_keywords(["lca", "solar", "photovoltaic", "renewable-energy"])
        .add_license("CC-BY-4.0", "Creative Commons Attribution 4.0")
        .add_contributor("Dr. Jane Smith", "author", "jane.smith@university.edu", "Solar Research Institute")
        .add_source("Manufacturer Survey 2024", "https://example.com/survey")
        .add_resource(Resource(
            name="panel-data",
            path="solar_panels.parquet",
            title="Solar Panel Database",
            description="Main dataset with panel specifications and LCA results",
            format="parquet"
        ))
        .build()
    )
    
    # Validate
    validator = StandardValidator("1.0.0")
    result = validator.validate_metadata(metadata)
    
    print(f"\n✅ Valid: {result.is_valid}")
    print(result)
    
    return metadata


def example_invalid_metadata():
    """Create an invalid metadata example (missing required fields)."""
    print("\n" + "="*60)
    print("Example 2: Invalid Metadata (Missing Required Fields)")
    print("="*60)
    
    # Create metadata with missing fields
    metadata = {
        "name": "test-dataset",
        "title": "Test",  # Too short
        # Missing: resources, licenses, created, contributors, sources
    }
    
    # Validate
    validator = StandardValidator("1.0.0")
    result = validator.validate_metadata(metadata)
    
    print(f"\n❌ Valid: {result.is_valid}")
    print(result)
    
    return metadata


def example_data_quality_issues():
    """Validate a DataFrame with quality issues."""
    print("\n" + "="*60)
    print("Example 3: Data Quality Validation")
    print("="*60)
    
    # Create a DataFrame with quality issues
    df = pd.DataFrame({
        "id": [1, 2, 3, 4, 5, 1, 2],  # Duplicates!
        "temperature": [20.5, None, 22.1, None, None, 21.0, 20.5],  # 40% nulls
        "mixed_type": [1, "two", 3, "four", 5, 1, "two"],  # Mixed types!
        "status": ["ok", "ok", "warning", "ok", "error", "ok", "ok"]
    })
    
    print(f"\nDataFrame shape: {df.shape}")
    print(df)
    
    # Validate
    validator = StandardValidator("1.0.0")
    result = validator.validate_data_quality(df)
    
    print(f"\n⚠️  Valid: {result.is_valid}")
    print(result)


def example_field_validation():
    """Validate field definitions."""
    print("\n" + "="*60)
    print("Example 4: Field Definition Validation")
    print("="*60)
    
    # Create field definitions (one valid, one invalid)
    fields = [
        # Valid field with unit
        Field(
            name="temperature",
            type="number",
            description="Ambient temperature during measurement",
            unit=Unit(name="°C", long_name="degree Celsius", path="http://qudt.org/vocab/unit/DEG_C"),
            constraints=FieldConstraints(minimum=-50.0, maximum=100.0)
        ),
        # Invalid: numeric field without unit (this should be caught by Pydantic now)
        # So let's create a dict to bypass Pydantic validation
        {
            "name": "value",
            "type": "number",
            "description": "Some value"
            # Missing unit!
        }
    ]
    
    validator = StandardValidator("1.0.0")
    
    # Validate first field (valid)
    print("\nValidating field 1 (valid):")
    result1 = validator.validate_field_definition(fields[0].to_dict())
    print(result1)
    
    # Validate second field (invalid)
    print("\nValidating field 2 (missing unit):")
    result2 = validator.validate_field_definition(fields[1])
    print(result2)


def example_full_validation():
    """Complete validation example with all components."""
    print("\n" + "="*60)
    print("Example 5: Complete Validation (metadata + data)")
    print("="*60)
    
    # Create good metadata
    builder = MetaDataBuilder()
    metadata = (builder
        .set_basic_info(
            name="electricity-mix-2024",
            title="European Electricity Mix Database 2024",
            description="Detailed breakdown of electricity generation sources across European countries including carbon intensity, generation capacity, and seasonal variations. Based on official statistics from Eurostat and national energy agencies.",
            version="1.0.0"
        )
        .set_keywords(["electricity", "energy", "europe", "carbon-intensity", "power-generation"])
        .set_links(homepage="https://example.com/electricity-db")
        .add_license("CC0-1.0", "Creative Commons Zero")
        .add_contributor("Energy Research Team", "author", "team@energy.org", "European Energy Institute")
        .add_source("Eurostat Energy Statistics", "https://ec.europa.eu/eurostat/energy")
        .add_resource(Resource(
            name="electricity-mix",
            path="electricity_mix.parquet",
            title="Electricity Mix Data",
            format="parquet",
            fields=[
                Field(
                    name="country",
                    type="string",
                    description="ISO 3166-1 alpha-2 country code"
                ),
                Field(
                    name="year",
                    type="integer",
                    description="Year of data collection",
                    unit=Unit(name="year", long_name="calendar year", path="http://qudt.org/vocab/unit/YR")
                ),
                Field(
                    name="carbon_intensity",
                    type="number",
                    description="Grid carbon intensity",
                    unit=Unit(name="gCO2/kWh", long_name="grams CO2 per kilowatt-hour"),
                    constraints=FieldConstraints(minimum=0.0, maximum=2000.0)
                )
            ]
        ))
        .build()
    )
    
    # Create clean DataFrame
    df = pd.DataFrame({
        "country": ["DE", "FR", "UK", "ES", "IT"],
        "year": [2024, 2024, 2024, 2024, 2024],
        "carbon_intensity": [420.5, 65.2, 287.3, 198.7, 315.6]
    })
    
    # Validate everything
    validator = StandardValidator("1.0.0")
    result = validator.validate_all(metadata, df)
    
    print(f"\n{'✅' if result.is_valid else '❌'} Overall: {result.level}")
    print(result)


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("TRAILPACK STANDARD VALIDATOR EXAMPLES")
    print("="*60)
    
    # Show available standards
    standards = list_available_standards()
    print(f"\nAvailable standards: {standards}")
    
    # Run examples
    example_valid_metadata()
    example_invalid_metadata()
    example_data_quality_issues()
    example_field_validation()
    example_full_validation()
    
    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
