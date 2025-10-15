"""Configuration builder for exporting UI session state to reusable JSON configs."""

import json
from datetime import datetime
from typing import Dict, Any, Optional


def build_mapping_config(
    column_mappings: Dict[str, str],
    file_name: str,
    sheet_name: str,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Build mapping configuration from column mappings.

    Args:
        column_mappings: Dictionary mapping column names to ontology/unit IDs
        file_name: Original file name
        sheet_name: Sheet name
        language: Language code for ontology mappings (default: "en")

    Returns:
        Dictionary with mapping configuration

    Example:
        >>> mappings = {
        ...     "Product": "https://vocab.sentier.dev/products/product/Product",
        ...     "CO2_unit": "https://vocab.sentier.dev/units/unit/KiloGM"
        ... }
        >>> config = build_mapping_config(mappings, "data.xlsx", "Sheet1")
    """
    return {
        "version": "1.0.0",
        "config_type": "mapping",
        "language": language,
        "file_info": {
            "original_file": file_name,
            "sheet_name": sheet_name
        },
        "column_mappings": column_mappings.copy(),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "created_with": "trailpack-ui"
    }


def build_metadata_config(
    general_details: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build metadata configuration from general details.

    Args:
        general_details: Dictionary with package metadata from UI

    Returns:
        Dictionary with metadata configuration

    Example:
        >>> details = {
        ...     "name": "my-dataset",
        ...     "title": "My Dataset",
        ...     "description": "Description here",
        ...     "licenses": [{"name": "MIT", "path": "..."}],
        ...     "contributors": [{"name": "John", "role": "author"}],
        ... }
        >>> config = build_metadata_config(details)
    """
    # Build package metadata
    package = {}

    # Basic fields
    basic_fields = [
        "name", "title", "description", "version",
        "profile", "keywords", "homepage", "repository"
    ]

    for field in basic_fields:
        if field in general_details:
            package[field] = general_details[field]

    # Date fields
    if "created" in general_details:
        package["created"] = general_details["created"]
    if "modified" in general_details:
        package["modified"] = general_details["modified"]

    # Build config
    config = {
        "version": "1.0.0",
        "config_type": "metadata",
        "package": package
    }

    # Array fields
    if "licenses" in general_details and general_details["licenses"]:
        config["licenses"] = general_details["licenses"].copy()

    if "contributors" in general_details and general_details["contributors"]:
        config["contributors"] = general_details["contributors"].copy()

    if "sources" in general_details and general_details["sources"]:
        config["sources"] = general_details["sources"].copy()

    # Add metadata about config creation
    config["config_created_at"] = datetime.utcnow().isoformat() + "Z"
    config["config_created_with"] = "trailpack-ui"

    return config


def export_mapping_json(config: Dict[str, Any], indent: int = 2) -> str:
    """
    Serialize mapping config to JSON string.

    Args:
        config: Mapping configuration dictionary
        indent: JSON indentation (default: 2)

    Returns:
        JSON string

    Example:
        >>> config = build_mapping_config({}, "data.xlsx", "Sheet1")
        >>> json_str = export_mapping_json(config)
    """
    return json.dumps(config, indent=indent, ensure_ascii=False)


def export_metadata_json(config: Dict[str, Any], indent: int = 2) -> str:
    """
    Serialize metadata config to JSON string.

    Args:
        config: Metadata configuration dictionary
        indent: JSON indentation (default: 2)

    Returns:
        JSON string

    Example:
        >>> config = build_metadata_config({"name": "my-dataset"})
        >>> json_str = export_metadata_json(config)
    """
    return json.dumps(config, indent=indent, ensure_ascii=False)


def generate_config_filename(
    config_type: str,
    package_name: Optional[str] = None,
    file_name: Optional[str] = None,
    sheet_name: Optional[str] = None
) -> str:
    """
    Generate a standardized filename for config export.

    Args:
        config_type: Type of config ("mapping" or "metadata")
        package_name: Package name if available
        file_name: Original file name (fallback)
        sheet_name: Sheet name (for mapping configs)

    Returns:
        Filename string

    Example:
        >>> generate_config_filename("mapping", "my-dataset")
        'my-dataset_mapping_config.json'
        >>> generate_config_filename("mapping", None, "data.xlsx", "Sheet1")
        'data_Sheet1_mapping_config.json'
    """
    if package_name:
        base_name = package_name
    elif file_name:
        # Remove extension
        from pathlib import Path
        base_name = Path(file_name).stem
        if sheet_name:
            base_name = f"{base_name}_{sheet_name.replace(' ', '_')}"
    else:
        base_name = "config"

    return f"{base_name}_{config_type}_config.json"
