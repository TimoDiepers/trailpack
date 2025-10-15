# Validation Module

The validation module provides standards-based validation for Trailpack data packages, ensuring quality and compliance before submission to repositories.

## Overview

The validator checks:
- ✅ **Metadata completeness**: All required fields present
- ✅ **Data quality**: Missing values, duplicates, type consistency
- ✅ **Field definitions**: Proper types, units for numeric fields
- ✅ **Standards compliance**: Adherence to Frictionless Data Package spec

## Quick Start

```python
from trailpack.validation import StandardValidator

# Create validator
validator = StandardValidator("1.0.0")

# Validate metadata
result = validator.validate_metadata(metadata_dict)

if result.is_valid:
    print("✅ Valid!")
else:
    print(result)  # Shows errors and warnings
```

## Usage Examples

### 1. Validate Metadata Only

```python
from trailpack.validation import StandardValidator

metadata = {
    "name": "my-dataset",
    "title": "My Research Dataset",
    "resources": [...],
    "licenses": [...],
    "created": "2025-10-15",
    "contributors": [...],
    "sources": [...]
}

validator = StandardValidator("1.0.0")
result = validator.validate_metadata(metadata)

print(f"Valid: {result.is_valid}")
print(f"Errors: {len(result.errors)}")
print(f"Warnings: {len(result.warnings)}")
```

### 2. Validate Data Quality

```python
import pandas as pd
from trailpack.validation import StandardValidator

# Load your data
df = pd.read_csv("mydata.csv")

# Validate
validator = StandardValidator("1.0.0")
result = validator.validate_data_quality(df)

# Check for quality issues
if not result.is_valid:
    for error in result.errors:
        print(f"❌ {error}")
    for warning in result.warnings:
        print(f"⚠️  {warning}")
```

### 3. Complete Validation

```python
from trailpack.validation import StandardValidator

# Validate everything at once
validator = StandardValidator("1.0.0")
result = validator.validate_all(
    metadata=metadata_dict,
    df=dataframe,
    mappings=field_mappings  # Optional
)

# Get compliance level
print(result.level)
# Output: "✅ STRICT COMPLIANCE" or "✓ STANDARD COMPLIANCE"
```

### 4. Validate Individual Resources

```python
resource = {
    "name": "data",
    "path": "data.parquet",
    "format": "parquet",
    "schema": {
        "fields": [...]
    }
}

result = validator.validate_resource(resource)
```

### 5. Validate Field Definitions

```python
field = {
    "name": "temperature",
    "type": "number",
    "unit": {
        "name": "°C",
        "long_name": "degree Celsius",
        "path": "http://qudt.org/vocab/unit/DEG_C"
    },
    "description": "Ambient temperature"
}

result = validator.validate_field_definition(field)
```

### 6. Schema-Based Data Validation

The validator can check that DataFrame values match their field type definitions:

```python
import pandas as pd
from trailpack.validation import StandardValidator

# Define schema
schema = {
    "fields": [
        {
            "name": "id",
            "type": "integer",
            "description": "Unique identifier",
            "unit": {
                "name": "dimensionless",
                "long_name": "dimensionless number",
                "path": "http://qudt.org/vocab/unit/NUM"
            }
        },
        {
            "name": "mass",
            "type": "number",
            "description": "Mass measurement",
            "unit": {
                "name": "kg",
                "long_name": "kilogram",
                "path": "http://qudt.org/vocab/unit/KiloGM"
            }
        }
    ]
}

# Your data
df = pd.DataFrame({
    "id": [1, 2, 3],
    "mass": [10.5, 20.3, 15.7]
})

# Validate data against schema
validator = StandardValidator("1.0.0")
result = validator.validate_data_quality(df, schema=schema)

if not result.is_valid:
    for error in result.errors:
        print(f"❌ {error}")
```

#### Unit Requirements for Numeric Fields

**All numeric fields (type: "number" or "integer") must have units specified**, even for dimensionless quantities:

- **Measurements**: Use appropriate SI or domain units (kg, m, °C, etc.)
- **Counts/IDs**: Use dimensionless unit with QUDT path
- **Percentages**: Use dimensionless or percent unit
- **Indices**: Use dimensionless unit

**Identifier fields** (like "id", "index", "key") with "identifier" in the description are automatically recognized and can use dimensionless units.

Example units:
```python
# Physical measurement
{"name": "kg", "long_name": "kilogram", "path": "http://qudt.org/vocab/unit/KiloGM"}

# Dimensionless count/ID
{"name": "dimensionless", "long_name": "dimensionless number", "path": "http://qudt.org/vocab/unit/NUM"}

# Percentage
{"name": "%", "long_name": "percent", "path": "http://qudt.org/vocab/unit/PERCENT"}
```

## Validation Levels

The validator assigns one of four compliance levels:

### ✅ STRICT COMPLIANCE
- All required fields present
- All recommended fields present
- All data quality checks pass
- No warnings
- **Use case**: Production datasets ready for publication

### ✓ STANDARD COMPLIANCE
- All required fields present
- Some recommended fields may be missing
- Minor quality warnings allowed (≤5)
- **Use case**: Good quality datasets ready for review

### ~ BASIC COMPLIANCE
- Required fields present
- Multiple quality warnings
- Needs improvement before publication
- **Use case**: Draft datasets in development

### ✗ NON-COMPLIANT
- Missing required fields
- Significant quality issues
- Cannot be processed
- **Use case**: Incomplete or problematic datasets

## ValidationResult Object

The `ValidationResult` class provides detailed validation information:

```python
result = validator.validate_all(metadata, df)

# Check validity
if result.is_valid:  # No errors
    print("✅ Valid!")

if result.has_warnings:  # Has warnings
    print("⚠️  Warnings present")

# Access details
print(result.level)           # Compliance level badge
print(result.errors)          # List of error messages
print(result.warnings)        # List of warning messages
print(result.info)            # List of info messages
print(result.get_summary())   # One-line summary

# Pretty print
print(result)  # Shows formatted output with all errors/warnings
```

## Standard Specification

The validator uses YAML-based standards in `standards/v1.0.0.yaml`:

```yaml
metadata:
  required:
    - name: { type: string, pattern: "^[a-z0-9\\-_\\.]+$" }
    - title: { type: string, min_length: 5 }
    - resources: { type: array, min_items: 1 }
    # ... more fields

data_quality:
  missing_data:
    max_null_percentage: 0.20  # Max 20% nulls per column
  duplicates:
    max_duplicate_percentage: 0.05  # Max 5% duplicates
  # ... more rules
```

## Integration with Streamlit UI

```python
import streamlit as st
from trailpack.validation import StandardValidator

# In your Streamlit app
validator = StandardValidator("1.0.0")
result = validator.validate_all(metadata, df)

if result.is_valid:
    st.success(f"{result.level}")
    st.balloons()
    # Enable export button
else:
    st.error("Cannot export: validation failed")
    with st.expander("❌ Errors"):
        for error in result.errors:
            st.write(f"• {error}")
    with st.expander("⚠️  Warnings"):
        for warning in result.warnings:
            st.write(f"• {warning}")
```

## Integration with CLI

```python
# In cli.py
import typer
from trailpack.validation import StandardValidator

app = typer.Typer()

@app.command()
def validate(
    metadata_file: str,
    data_file: str = None
):
    """Validate a data package."""
    import json
    import pandas as pd
    
    # Load metadata
    with open(metadata_file) as f:
        metadata = json.load(f)
    
    # Validate
    validator = StandardValidator("1.0.0")
    
    if data_file:
        df = pd.read_parquet(data_file)
        result = validator.validate_all(metadata, df)
    else:
        result = validator.validate_metadata(metadata)
    
    # Print results
    print(result)
    
    # Exit code
    return 0 if result.is_valid else 1
```

## Custom Validation Rules

You can extend the validator for project-specific rules:

```python
from trailpack.validation import StandardValidator, ValidationResult

class CustomValidator(StandardValidator):
    """Custom validator with additional rules."""
    
    def validate_custom_rule(self, metadata):
        """Add custom validation logic."""
        result = ValidationResult()
        
        # Your custom checks
        if "project_code" not in metadata:
            result.add_warning("Project code is missing")
        
        return result
    
    def validate_all(self, metadata, df=None, mappings=None):
        """Override to include custom checks."""
        # Run standard validation
        result = super().validate_all(metadata, df, mappings)
        
        # Add custom checks
        custom_result = self.validate_custom_rule(metadata)
        result.errors.extend(custom_result.errors)
        result.warnings.extend(custom_result.warnings)
        
        return result
```

## Error Messages

All error messages are clear and actionable:

```
❌ ERRORS:
  • [name] Package name must be lowercase, alphanumeric with hyphens, underscores, or dots
  • [resources] At least one resource (data file) is required
  • [contributors] At least one contributor with role 'author' is required
  • [data_quality] Column 'temperature' has 35% missing values (max: 20%)

⚠️  WARNINGS:
  • [description] Description should be at least 50 characters for clarity
  • [keywords] At least 3 keywords help improve discoverability
  • [format] Format 'csv' is acceptable, but 'parquet' is preferred
```

## API Reference

### StandardValidator

#### `__init__(version: str = "1.0.0")`
Initialize validator with a specific standard version.

#### `validate_all(metadata, df=None, mappings=None) -> ValidationResult`
Validate everything: metadata, data quality, and mappings.

#### `validate_metadata(metadata: dict) -> ValidationResult`
Validate metadata against required and recommended fields.

#### `validate_resource(resource: dict) -> ValidationResult`
Validate a resource (data file) definition.

#### `validate_field_definition(field: dict) -> ValidationResult`
Validate a field (column) definition.

#### `validate_data_quality(df: pd.DataFrame) -> ValidationResult`
Validate data quality of a DataFrame.

#### `get_help_url(topic: str) -> Optional[str]`
Get help URL for a specific topic.

### ValidationResult

#### Properties
- `is_valid: bool` - True if no errors
- `has_warnings: bool` - True if warnings exist
- `level: str` - Compliance level badge
- `errors: List[str]` - Error messages
- `warnings: List[str]` - Warning messages
- `info: List[str]` - Info messages

#### Methods
- `add_error(message, field=None)` - Add an error
- `add_warning(message, field=None)` - Add a warning
- `add_info(message)` - Add an info message
- `get_summary() -> str` - Get one-line summary
- `__str__()` - Pretty formatted output

## Testing

Run the examples:

```bash
python examples/standard_validator_demo.py
```

Run unit tests:

```bash
pytest tests/test_standard_validator.py -v
```

## Help and Resources

- [Frictionless Data Package Spec](https://specs.frictionlessdata.org/data-package/)
- [QUDT Units Ontology](http://qudt.org/vocab/unit/)
- [SPDX License List](https://spdx.org/licenses/)
- [Trailpack Documentation](https://github.com/TimoDiepers/trailpack)

## Contributing

To improve validation rules:

1. Update `standards/v1.0.0.yaml` with new requirements
2. Add validation logic in `standard_validator.py`
3. Add tests in `tests/test_standard_validator.py`
4. Update documentation

See `standards/README.md` for details on standard evolution.
