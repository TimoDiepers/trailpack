"""Configuration management for Trailpack.

This module provides utilities for exporting and loading configuration files
that can be used for reproducible data package creation.

Note: Config validation is handled by StandardValidator in the validation module.
"""

from trailpack.config.config_builder import (
    build_mapping_config,
    build_metadata_config,
    export_mapping_json,
    export_metadata_json,
    generate_config_filename,
)
from trailpack.config.config_loader import (
    load_mapping_config,
    load_metadata_config,
    extract_column_mappings,
    extract_file_info,
    extract_general_details,
    validate_config_compatibility,
    load_configs,
    ConfigLoadError,
)

__all__ = [
    # Config builder (export)
    "build_mapping_config",
    "build_metadata_config",
    "export_mapping_json",
    "export_metadata_json",
    "generate_config_filename",
    # Config loader (import)
    "load_mapping_config",
    "load_metadata_config",
    "extract_column_mappings",
    "extract_file_info",
    "extract_general_details",
    "validate_config_compatibility",
    "load_configs",
    "ConfigLoadError",
]
