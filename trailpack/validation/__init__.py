"""
Validation module for Trailpack.

Provides standards-based validation for data packages to ensure
quality and compliance before submission to repositories.

The validation system checks:
- Metadata completeness: All required fields present (name, title, resources, etc.)
- Data quality metrics: Missing values and duplicates (logged as info)
- Type consistency: Mixed types and schema matching (raises errors)
- Field definitions: Proper types, units for numeric fields

Key Components:
- StandardValidator: Main validation class for all checks
- ValidationResult: Result object with errors, warnings, info, and compliance level
- Standards YAML: Versioned validation rules in standards/v*.yaml

Data Quality vs Type Consistency:
- Data quality metrics (nulls, duplicates) are logged as INFO messages
- Type consistency issues (mixed types, schema mismatches) raise ERRORS
- Only errors cause validation to fail

Unit Requirements:
All numeric fields (type "number" or "integer") must have units specified,
even for dimensionless quantities like IDs and counts. Use the QUDT vocabulary
for unit definitions (http://qudt.org/vocab/unit/).

Inconsistency Tracking and Export:
When type inconsistencies are detected (e.g., mixed types in a column), each
inconsistent value is automatically tracked and exported to 'data_inconsistencies.csv'
when the ValidationResult is printed. This CSV file contains:
- row: Row index of the inconsistent value
- column: Column name
- value: The actual value
- actual_type: Python type of the value
- expected_type: Most common type in the column

This export happens automatically for easy data cleaning workflows.

Example:
    >>> from trailpack.validation import StandardValidator
    >>> validator = StandardValidator("1.0.0")
    >>> result = validator.validate_data_quality(df, schema)
    >>> print(result)  # Automatically exports inconsistencies.csv if issues found
    >>> if result.is_valid:
    ...     print(f"{result.level}")
    ... else:
    ...     for error in result.errors:
    ...         print(f"Error: {error}")
"""

from pathlib import Path

# Version of the validation module
__version__ = "1.0.0"

# Path to standards directory
STANDARDS_DIR = Path(__file__).parent / "standards"


def get_standard_path(version: str = "1.0.0") -> Path:
    """
    Get the path to a specific standard version.
    
    Args:
        version: Standard version (default: "1.0.0")
        
    Returns:
        Path to the standard YAML file
        
    Raises:
        FileNotFoundError: If the standard version doesn't exist
    """
    standard_path = STANDARDS_DIR / f"v{version}.yaml"
    if not standard_path.exists():
        raise FileNotFoundError(
            f"Standard version v{version} not found. "
            f"Available versions: {list_available_standards()}"
        )
    return standard_path


def list_available_standards() -> list[str]:
    """
    List all available standard versions.
    
    Returns:
        List of version strings (e.g., ["1.0.0"])
    """
    if not STANDARDS_DIR.exists():
        return []
    
    versions = []
    for yaml_file in STANDARDS_DIR.glob("v*.yaml"):
        # Extract version from filename (e.g., "v1.0.0.yaml" -> "1.0.0")
        version = yaml_file.stem[1:]  # Remove 'v' prefix
        versions.append(version)
    
    return sorted(versions)


# Import validator classes
try:
    from trailpack.validation.standard_validator import StandardValidator, ValidationResult
    
    __all__ = [
        "get_standard_path",
        "list_available_standards",
        "StandardValidator",
        "ValidationResult",
        "STANDARDS_DIR",
    ]
except ImportError:
    # If dependencies not installed, just export utility functions
    __all__ = [
        "get_standard_path",
        "list_available_standards",
        "STANDARDS_DIR",
    ]
