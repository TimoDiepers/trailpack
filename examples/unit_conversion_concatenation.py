"""
Example: Reading multiple parquet files and concatenating them with unit conversion.

This example demonstrates:
1. Reading multiple parquet files with data in different units
2. Using PyST API to get unit information
3. Converting data to a common unit using pint
4. Concatenating the dataframes
5. Creating proper metadata with unit information

Based on the pyst API: https://docs.pyst.dev/api/
"""

import pandas as pd
import pint
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio

# Import trailpack components
from trailpack.packing.datapackage_schema import (
    MetaDataBuilder,
    Resource,
    Field,
    Unit,
)
from trailpack.pyst.api.client import get_suggest_client


# Initialize pint unit registry
ureg = pint.UnitRegistry()


def read_parquet_with_metadata(filepath: str) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Read a parquet file and extract metadata about units.
    
    Args:
        filepath: Path to the parquet file
        
    Returns:
        Tuple of (DataFrame, metadata dict with unit information)
    """
    df = pd.read_parquet(filepath)
    
    # In a real scenario, metadata would be embedded in the parquet file
    # For this example, we infer from the filename
    filename = Path(filepath).stem
    
    # Define metadata based on file
    metadata = {
        'filepath': filepath,
        'columns': {}
    }
    
    # Extract unit information from filename (simplified)
    if 'kg' in filename.lower():
        metadata['columns']['mass'] = {'unit': 'kilogram', 'unit_symbol': 'kg'}
    elif '_g' in filename.lower():
        metadata['columns']['mass'] = {'unit': 'gram', 'unit_symbol': 'g'}
    else:
        # Default to detecting from data characteristics
        if 'mass' in df.columns and df['mass'].max() < 100:
            metadata['columns']['mass'] = {'unit': 'kilogram', 'unit_symbol': 'kg'}
        elif 'mass' in df.columns:
            metadata['columns']['mass'] = {'unit': 'gram', 'unit_symbol': 'g'}
    
    return df, metadata


def convert_column_units(
    df: pd.DataFrame, 
    column: str, 
    from_unit: str, 
    to_unit: str
) -> pd.DataFrame:
    """
    Convert a column from one unit to another using pint.
    
    Args:
        df: Input DataFrame
        column: Name of the column to convert
        from_unit: Source unit (e.g., 'gram', 'g')
        to_unit: Target unit (e.g., 'kilogram', 'kg')
        
    Returns:
        DataFrame with converted column
    """
    df = df.copy()
    
    # Create quantity array with units
    quantities = df[column].values * ureg(from_unit)
    
    # Convert to target unit
    converted = quantities.to(to_unit)
    
    # Update dataframe with converted values
    df[column] = converted.magnitude
    
    return df


async def get_unit_info_from_pyst(unit_name: str, language: str = "en") -> Optional[str]:
    """
    Get unit information from PyST API.
    
    Args:
        unit_name: Name of the unit (e.g., 'kilogram', 'gram')
        language: Language code for the query
        
    Returns:
        Unit URI from QUDT vocabulary or None
    """
    try:
        client = get_suggest_client()
        
        # Search for the unit in PyST
        results = await client.suggest(unit_name, language)
        
        # Look for QUDT unit in results
        for result in results:
            label = result.get('label', '').lower()
            iri = result.get('iri', '')
            
            # Check if this is a unit concept
            if unit_name.lower() in label.lower() and 'qudt.org/vocab/unit' in iri:
                print(f"Found unit in PyST: {label} -> {iri}")
                return iri
        
        # If no exact match, return a default QUDT URI
        if unit_name.lower() == 'kilogram':
            return "http://qudt.org/vocab/unit/KiloGM"
        elif unit_name.lower() in ['gram', 'g']:
            return "http://qudt.org/vocab/unit/GM"
        
        return None
        
    except Exception as e:
        print(f"Error querying PyST API: {e}")
        return None


def concatenate_with_unit_conversion(
    filepaths: List[str],
    target_unit: str = 'kilogram',
    target_unit_symbol: str = 'kg'
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Read multiple parquet files, convert units, and concatenate.
    
    Args:
        filepaths: List of paths to parquet files
        target_unit: Target unit for conversion (default: 'kilogram')
        target_unit_symbol: Symbol for the target unit (default: 'kg')
        
    Returns:
        Tuple of (concatenated DataFrame, unified metadata)
    """
    dataframes = []
    all_metadata = []
    
    print(f"Reading and converting {len(filepaths)} files to {target_unit}...\n")
    
    for filepath in filepaths:
        # Read file with metadata
        df, metadata = read_parquet_with_metadata(filepath)
        
        print(f"Processing: {Path(filepath).name}")
        print(f"  Rows: {len(df)}, Columns: {df.columns.tolist()}")
        
        # Convert units if needed
        if 'mass' in df.columns and 'mass' in metadata['columns']:
            source_unit = metadata['columns']['mass']['unit']
            print(f"  Converting mass from {source_unit} to {target_unit}")
            
            if source_unit != target_unit:
                df = convert_column_units(df, 'mass', source_unit, target_unit)
        
        dataframes.append(df)
        all_metadata.append(metadata)
        print(f"  Converted mass range: {df['mass'].min():.2f} - {df['mass'].max():.2f} {target_unit_symbol}\n")
    
    # Concatenate all dataframes
    concatenated_df = pd.concat(dataframes, ignore_index=True)
    
    # Create unified metadata
    unified_metadata = {
        'source_files': [m['filepath'] for m in all_metadata],
        'target_unit': target_unit,
        'target_unit_symbol': target_unit_symbol,
        'total_rows': len(concatenated_df)
    }
    
    return concatenated_df, unified_metadata


async def create_datapackage_with_pyst(
    df: pd.DataFrame,
    name: str,
    title: str,
    description: str,
    output_path: str = "concatenated_data.parquet"
) -> Dict[str, Any]:
    """
    Create a Frictionless Data Package metadata using PyST API for unit URIs.
    
    Args:
        df: The dataframe to package
        name: Package name
        title: Package title
        description: Package description
        output_path: Path where the data will be saved
        
    Returns:
        Complete metadata dictionary
    """
    print("\nCreating data package metadata with PyST unit information...\n")
    
    # Get unit URI from PyST API
    mass_unit_uri = await get_unit_info_from_pyst("kilogram", "en")
    
    # Build metadata using MetaDataBuilder
    metadata = (MetaDataBuilder()
        .set_basic_info(
            name=name,
            title=title,
            description=description,
            version="1.0.0"
        )
        .set_keywords(["mass", "measurement", "unit-conversion", "concatenated"])
        .add_license("CC-BY-4.0", "Creative Commons Attribution 4.0")
        .add_contributor("Example Author", "author", "author@example.com")
        .add_source("Sample Data Generator", "Generated for demonstration")
        .add_resource(Resource(
            name="mass-measurements",
            path=output_path,
            title="Mass Measurements (Concatenated)",
            description="Mass measurements from multiple sources, unified to kilogram units",
            format="parquet",
            fields=[
                Field(
                    name="location",
                    type="string",
                    description="Measurement location"
                ),
                Field(
                    name="timestamp",
                    type="datetime",
                    description="Measurement timestamp",
                    unit=Unit(
                        name="datetime",
                        long_name="ISO 8601 datetime",
                        path="http://www.w3.org/2001/XMLSchema#dateTime"
                    )
                ),
                Field(
                    name="mass",
                    type="number",
                    description="Mass measurement in kilograms",
                    unit=Unit(
                        name="kg",
                        long_name="kilogram",
                        path=mass_unit_uri if mass_unit_uri else "http://qudt.org/vocab/unit/KiloGM"
                    )
                )
            ]
        ))
        .build()
    )
    
    print("Data package metadata created successfully!")
    print(f"  Package name: {metadata['name']}")
    print(f"  Resources: {len(metadata['resources'])}")
    print(f"  Fields: {len(metadata['resources'][0]['schema']['fields'])}")
    
    return metadata


def main():
    """Main example execution."""
    print("="*70)
    print("UNIT CONVERSION AND CONCATENATION EXAMPLE")
    print("="*70)
    print()
    print("This example demonstrates:")
    print("  1. Reading multiple parquet files with different units")
    print("  2. Converting units to a common unit using pint")
    print("  3. Concatenating the data")
    print("  4. Using PyST API to get unit URIs for metadata")
    print("="*70)
    print()
    
    # Define input files (created earlier)
    input_files = [
        'tests/data/sample_kg.parquet',
        'tests/data/sample_g.parquet'
    ]
    
    # Verify files exist
    for filepath in input_files:
        if not Path(filepath).exists():
            print(f"Error: File not found: {filepath}")
            print("Please run the data generation script first.")
            return
    
    # Step 1: Concatenate with unit conversion
    concatenated_df, metadata = concatenate_with_unit_conversion(
        input_files,
        target_unit='kilogram',
        target_unit_symbol='kg'
    )
    
    print("="*70)
    print("CONCATENATION COMPLETE")
    print("="*70)
    print(f"\nTotal rows: {len(concatenated_df)}")
    print(f"Columns: {concatenated_df.columns.tolist()}")
    print("\nFirst few rows:")
    print(concatenated_df.head())
    print("\nLast few rows:")
    print(concatenated_df.tail())
    print(f"\nMass statistics (in kg):")
    print(concatenated_df['mass'].describe())
    
    # Step 2: Create data package metadata with PyST
    async def create_metadata_async():
        return await create_datapackage_with_pyst(
            concatenated_df,
            name="unified-mass-measurements",
            title="Unified Mass Measurements Dataset",
            description="Mass measurements from multiple sources with different original units (kg and g), unified to kilograms for consistency",
            output_path="concatenated_mass_data.parquet"
        )
    
    # Run async function
    datapackage_metadata = asyncio.run(create_metadata_async())
    
    # Step 3: Save the concatenated data
    output_file = "concatenated_mass_data.parquet"
    concatenated_df.to_parquet(output_file, index=False)
    print(f"\n✅ Data saved to: {output_file}")
    
    # Step 4: Save the metadata
    import json
    metadata_file = "concatenated_mass_data_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(datapackage_metadata, f, indent=2, default=str)
    print(f"✅ Metadata saved to: {metadata_file}")
    
    print("\n" + "="*70)
    print("EXAMPLE COMPLETE!")
    print("="*70)
    print("\nKey takeaways:")
    print("  ✓ Successfully read 2 parquet files with different units")
    print("  ✓ Converted grams to kilograms automatically")
    print("  ✓ Concatenated data into unified dataset")
    print("  ✓ Created Frictionless Data Package metadata")
    print("  ✓ Used PyST API to get standard unit URIs")
    print()


if __name__ == "__main__":
    main()
