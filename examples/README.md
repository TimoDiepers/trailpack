# Trailpack Examples

This directory contains example scripts demonstrating various features of the Trailpack library.

## Available Examples

### 1. test_packing.py
Basic example showing how to create a simple data package with metadata.

**Features:**
- Creating sample data with pandas
- Defining basic metadata structure
- Working with timestamps
- Setting up field schemas with units

**Usage:**
```bash
python examples/test_packing.py
```

### 2. unit_conversion_concatenation.py
**Advanced example demonstrating unit conversion and data concatenation.**

This example shows how to:
- Read multiple parquet files with data in different units
- Automatically detect and convert between units (e.g., grams to kilograms)
- Concatenate dataframes with unified units
- Use PyST API to get standardized unit URIs (QUDT vocabulary)
- Create Frictionless Data Package metadata with proper unit definitions

**Features:**
- Unit conversion using `pint` library
- PyST API integration for unit vocabulary
- Automatic unit detection from filenames or data
- Creates complete Data Package metadata
- Saves both data and metadata

**Usage:**
```bash
# First, ensure sample data files exist (they should be in tests/data/)
python examples/unit_conversion_concatenation.py
```

**Output:**
- `concatenated_mass_data.parquet` - Unified dataset with all measurements in kg
- `concatenated_mass_data_metadata.json` - Complete Data Package metadata

**Key Code Patterns:**

Reading with metadata:
```python
df, metadata = read_parquet_with_metadata('data.parquet')
```

Unit conversion:
```python
df = convert_column_units(df, 'mass', 'gram', 'kilogram')
```

Getting unit URIs from PyST:
```python
mass_unit_uri = await get_unit_info_from_pyst("kilogram", "en")
```

### 3. standard_validator_demo.py
Comprehensive example demonstrating the validation system.

**Features:**
- Metadata validation
- Data quality checks
- Field definition validation
- Compliance level reporting
- Error handling examples

**Usage:**
```bash
python examples/standard_validator_demo.py
```

### 4. test_inconsistencies_demo.py
Example showing how to handle and report data inconsistencies.

**Usage:**
```bash
python examples/test_inconsistencies_demo.py
```

## Requirements

Most examples require the base trailpack installation:
```bash
pip install trailpack
```

For the unit conversion example, you also need `pint`:
```bash
pip install pint
```

## Data Files

Sample data files used by the examples are stored in `tests/data/`:
- `sample_kg.parquet` - Mass measurements in kilograms
- `sample_g.parquet` - Mass measurements in grams
- `example.parquet` - General example data
- `test.parquet` - Test data

## Creating Your Own Examples

When creating new examples:

1. **Follow the pattern** of existing examples
2. **Add documentation** at the top of your script
3. **Use the builder pattern** for metadata when possible
4. **Handle errors gracefully** with try-except blocks
5. **Print clear output** showing what's happening
6. **Update this README** with your example

### Example Template

```python
"""
Example: Brief description

This example demonstrates:
1. First feature
2. Second feature
3. Third feature
"""

def main():
    print("="*70)
    print("YOUR EXAMPLE NAME")
    print("="*70)
    
    # Your code here
    
    print("\n✅ Example complete!")

if __name__ == "__main__":
    main()
```

## PyST API Integration

Several examples use the PyST (Python Semantic Taxonomy) API for concept mapping and unit information.

**Documentation:** https://docs.pyst.dev/api/

**Usage pattern:**
```python
from trailpack.pyst.api.client import get_suggest_client

client = get_suggest_client()
results = await client.suggest("carbon footprint", "en")
```

## Contributing

To contribute a new example:

1. Create your example script in this directory
2. Test it thoroughly
3. Add documentation to this README
4. Include sample output in comments
5. Submit a pull request

## Support

For questions or issues with the examples:
- Open an issue on GitHub
- Check the main documentation at https://trailpack.readthedocs.io/
- Review the API documentation for PyST integration
