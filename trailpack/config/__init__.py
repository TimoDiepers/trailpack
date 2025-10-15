"""Configuration management for Trailpack.

This module provides utilities for exporting configuration files
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

__all__ = [
    "build_mapping_config",
    "build_metadata_config",
    "export_mapping_json",
    "export_metadata_json",
    "generate_config_filename",
]
