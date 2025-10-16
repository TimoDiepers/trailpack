"""Configuration loader for reading and applying JSON configs in CLI."""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoadError(Exception):
    """Raised when config loading fails."""
    pass


def load_mapping_config(config_path: Path) -> Dict[str, Any]:
    """
    Load mapping configuration from JSON file.

    Args:
        config_path: Path to mapping config JSON file

    Returns:
        Dictionary with mapping configuration

    Raises:
        ConfigLoadError: If file doesn't exist, is invalid JSON, or wrong type

    Example:
        >>> config = load_mapping_config(Path("mapping_config.json"))
        >>> column_mappings = config["column_mappings"]
    """
    if not config_path.exists():
        raise ConfigLoadError(f"Config file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigLoadError(f"Invalid JSON in {config_path}: {e}")

    # Validate config type
    if config.get("config_type") != "mapping":
        raise ConfigLoadError(
            f"Expected mapping config, got: {config.get('config_type')}"
        )

    # Validate required fields
    required_fields = ["version", "column_mappings"]
    missing = [f for f in required_fields if f not in config]
    if missing:
        raise ConfigLoadError(f"Missing required fields: {missing}")

    return config


def load_metadata_config(config_path: Path) -> Dict[str, Any]:
    """
    Load metadata configuration from JSON file.

    Args:
        config_path: Path to metadata config JSON file

    Returns:
        Dictionary with metadata configuration

    Raises:
        ConfigLoadError: If file doesn't exist, is invalid JSON, or wrong type

    Example:
        >>> config = load_metadata_config(Path("metadata_config.json"))
        >>> package_info = config["package"]
    """
    if not config_path.exists():
        raise ConfigLoadError(f"Config file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigLoadError(f"Invalid JSON in {config_path}: {e}")

    # Validate config type
    if config.get("config_type") != "metadata":
        raise ConfigLoadError(
            f"Expected metadata config, got: {config.get('config_type')}"
        )

    # Validate required fields
    required_fields = ["version", "package"]
    missing = [f for f in required_fields if f not in config]
    if missing:
        raise ConfigLoadError(f"Missing required fields: {missing}")

    return config


def extract_column_mappings(mapping_config: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract column mappings dictionary from mapping config.

    Args:
        mapping_config: Mapping configuration dictionary

    Returns:
        Dictionary mapping column names to ontology/unit IDs

    Example:
        >>> config = load_mapping_config(Path("mapping_config.json"))
        >>> mappings = extract_column_mappings(config)
        >>> # {"Product": "https://vocab.sentier.dev/...", ...}
    """
    return mapping_config.get("column_mappings", {}).copy()


def extract_file_info(mapping_config: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract file information from mapping config.

    Args:
        mapping_config: Mapping configuration dictionary

    Returns:
        Dictionary with original_file and sheet_name

    Example:
        >>> config = load_mapping_config(Path("mapping_config.json"))
        >>> file_info = extract_file_info(config)
        >>> # {"original_file": "data.xlsx", "sheet_name": "Sheet1"}
    """
    return mapping_config.get("file_info", {}).copy()


def extract_general_details(metadata_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract general details from metadata config for UI compatibility.

    Args:
        metadata_config: Metadata configuration dictionary

    Returns:
        Dictionary with package metadata in UI format

    Example:
        >>> config = load_metadata_config(Path("metadata_config.json"))
        >>> details = extract_general_details(config)
        >>> # {"name": "my-dataset", "title": "...", ...}
    """
    general_details = {}

    # Extract package fields
    package = metadata_config.get("package", {})
    for key, value in package.items():
        general_details[key] = value

    # Extract array fields
    if "licenses" in metadata_config:
        general_details["licenses"] = metadata_config["licenses"].copy()

    if "contributors" in metadata_config:
        general_details["contributors"] = metadata_config["contributors"].copy()

    if "sources" in metadata_config:
        general_details["sources"] = metadata_config["sources"].copy()

    return general_details


def validate_config_compatibility(
    mapping_config: Dict[str, Any],
    metadata_config: Dict[str, Any]
) -> bool:
    """
    Check if mapping and metadata configs are compatible.

    Args:
        mapping_config: Mapping configuration dictionary
        metadata_config: Metadata configuration dictionary

    Returns:
        True if configs are compatible

    Raises:
        ConfigLoadError: If configs are incompatible

    Example:
        >>> mapping = load_mapping_config(Path("mapping.json"))
        >>> metadata = load_metadata_config(Path("metadata.json"))
        >>> validate_config_compatibility(mapping, metadata)
        True
    """
    # Check version compatibility
    mapping_version = mapping_config.get("version", "unknown")
    metadata_version = metadata_config.get("version", "unknown")

    if mapping_version != metadata_version:
        raise ConfigLoadError(
            f"Config version mismatch: mapping={mapping_version}, "
            f"metadata={metadata_version}"
        )

    # Check package name matches if available
    file_info = mapping_config.get("file_info", {})
    package_name = metadata_config.get("package", {}).get("name")

    if file_info and package_name:
        # This is just a warning, not an error
        original_file = file_info.get("original_file", "")
        if package_name.lower() not in original_file.lower():
            import warnings
            warnings.warn(
                f"Package name '{package_name}' doesn't match file "
                f"'{original_file}' - this may be intentional"
            )

    return True


def load_configs(
    mapping_path: Optional[Path] = None,
    metadata_path: Optional[Path] = None
) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Load both mapping and metadata configs with validation.

    Args:
        mapping_path: Path to mapping config JSON (optional)
        metadata_path: Path to metadata config JSON (optional)

    Returns:
        Tuple of (mapping_config, metadata_config)

    Raises:
        ConfigLoadError: If loading fails or configs are incompatible

    Example:
        >>> mapping, metadata = load_configs(
        ...     mapping_path=Path("mapping.json"),
        ...     metadata_path=Path("metadata.json")
        ... )
    """
    mapping_config = None
    metadata_config = None

    if mapping_path:
        mapping_config = load_mapping_config(mapping_path)

    if metadata_path:
        metadata_config = load_metadata_config(metadata_path)

    # Validate compatibility if both provided
    if mapping_config and metadata_config:
        validate_config_compatibility(mapping_config, metadata_config)

    return mapping_config, metadata_config
