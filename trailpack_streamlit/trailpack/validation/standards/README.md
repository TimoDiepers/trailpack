# Trailpack Standards

This directory contains validation standards for data packages created with Trailpack.

## Overview

Standards define what is **required** and **recommended** for datasets to be accepted by data repositories. They ensure:

- **Data Quality**: Consistency, completeness, and correctness
- **Metadata Completeness**: All necessary information is documented
- **Interoperability**: Data can be understood and used by others
- **Best Practices**: Following scientific data management standards

## Available Standards

### v1.0.0 (Current)

The initial Trailpack standard based on the [Frictionless Data Package specification](https://specs.frictionlessdata.org/data-package/) with additional requirements for scientific data.

**Key Requirements:**
- All metadata fields from DataPackageSchema must be present
- Numeric fields MUST have units specified
- At least one data source must be documented
- License information is required
- Data quality thresholds must be met

**Validation Levels:**
- **STRICT**: Production-ready, all checks pass
- **STANDARD**: Good quality, minor warnings allowed
- **BASIC**: Draft quality, needs improvement
- **INVALID**: Does not meet minimum requirements

## Using Standards in Code

```python
from trailpack.validation import get_standard_path, list_available_standards

# List available standards
versions = list_available_standards()
print(versions)  # ["1.0.0"]

# Get path to standard
standard_path = get_standard_path("1.0.0")

# Load standard for validation
import yaml
with open(standard_path) as f:
    standard = yaml.safe_load(f)

# Use with validator (coming soon)
from trailpack.validation.standard_validator import StandardValidator
validator = StandardValidator(standard)
is_valid, errors = validator.validate_metadata(metadata)
```

## Standard Structure

Each standard YAML file contains:

### 1. Metadata Requirements
- `required`: Fields that MUST be present
- `recommended`: Fields that SHOULD be present
- `optional`: Fields that MAY be present

### 2. Resource Requirements
Requirements for each data file in the package.

### 3. Field Requirements
Requirements for column/field definitions, including:
- Data types
- Units for numeric fields
- Constraints and validation rules

### 4. Data Quality Requirements
Thresholds for:
- Missing data percentages
- Duplicate detection
- Outlier identification
- Type consistency

### 5. Validation Levels
Different compliance levels with specific criteria:
- **STRICT**: All requirements met, no warnings
- **STANDARD**: Required fields present, minor quality issues
- **BASIC**: Minimal requirements, significant improvements needed
- **INVALID**: Does not meet minimum standards

## Future Standards

As Trailpack evolves, new standard versions will be added here. Each version will:

1. Maintain backward compatibility where possible
2. Document all changes in the changelog section
3. Provide migration guides if breaking changes occur
4. Follow semantic versioning

Example future versions:
- `v1.1.0.yaml`: Minor additions (backward compatible)
- `v2.0.0.yaml`: Major changes (may break compatibility)

## Contributing

To propose changes to standards:

1. Open an issue describing the proposed change
2. Discuss with maintainers and community
3. Create a draft standard version
4. Test with existing datasets
5. Submit PR with changelog entry

## Standard Validation Test Suite

Each standard should have accompanying tests in `tests/test_standards/` to verify:

- YAML is valid and parsable
- All required sections are present
- Examples in the standard actually validate correctly
- Error messages are clear and helpful

## References

- [Frictionless Data Package](https://specs.frictionlessdata.org/data-package/)
- [QUDT Units Ontology](http://qudt.org/vocab/unit/)
- [SPDX License List](https://spdx.org/licenses/)
- [Semantic Versioning](https://semver.org/)
- [ISO 8601 Date Format](https://www.iso.org/iso-8601-date-and-time-format.html)
