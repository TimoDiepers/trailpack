"""
Validation module for Trailpack.

Provides standards-based validation for data packages to ensure
quality and compliance before submission to repositories.

The validation system checks:
- Metadata completeness: All required fields present (name, title, resources, etc.)
- Data quality: Missing values, duplicates, type consistency
- Field definitions: Proper types, units for numeric fields
- Schema matching: Column types match their field definitions

Key Components:
- StandardValidator: Main validation class for all checks
- ValidationResult: Result object with errors, warnings, and compliance level
- Standards YAML: Versioned validation rules in standards/v*.yaml

Unit Requirements:
All numeric fields (type "number" or "integer") must have units specified,
even for dimensionless quantities like IDs and counts. Use the QUDT vocabulary
for unit definitions (http://qudt.org/vocab/unit/).

Example:
    >>> from trailpack.validation import StandardValidator
    >>> validator = StandardValidator("1.0.0")
    >>> result = validator.validate_all(metadata, df)
    >>> if result.is_valid:
    ...     print(f"{result.level}")
    ... else:
    ...     print(result)
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
