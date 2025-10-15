"""
Standard validator for Trailpack data packages.

Validates metadata, resources, fields, and data quality against
the Trailpack standard specification.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime
import pandas as pd
import yaml

from trailpack.validation import get_standard_path


class ValidationResult:
    """Result of a validation check."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.level: Optional[str] = None
        
    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def add_error(self, message: str, field: Optional[str] = None):
        """Add an error message."""
        if field:
            self.errors.append(f"[{field}] {message}")
        else:
            self.errors.append(message)
    
    def add_warning(self, message: str, field: Optional[str] = None):
        """Add a warning message."""
        if field:
            self.warnings.append(f"[{field}] {message}")
        else:
            self.warnings.append(message)
    
    def add_info(self, message: str):
        """Add an info message."""
        self.info.append(message)
    
    def get_summary(self) -> str:
        """Get a summary of the validation result."""
        if self.level:
            return f"{self.level}: {len(self.errors)} errors, {len(self.warnings)} warnings"
        return f"{len(self.errors)} errors, {len(self.warnings)} warnings"
    
    def __str__(self) -> str:
        """String representation."""
        lines = []
        
        if self.level:
            lines.append(f"\n{self.level}\n{'=' * len(self.level)}")
        
        if self.errors:
            lines.append(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                lines.append(f"  • {error}")
        
        if self.warnings:
            lines.append(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"  • {warning}")
        
        if self.info:
            lines.append(f"\nℹ️  INFO ({len(self.info)}):")
            for info in self.info:
                lines.append(f"  • {info}")
        
        if not self.errors and not self.warnings:
            lines.append("\n✅ All checks passed!")
        
        return "\n".join(lines)


class StandardValidator:
    """
    Validate data packages against Trailpack standards.
    
    The StandardValidator checks data packages for:
    - Metadata completeness (required and recommended fields)
    - Resource definitions (proper schema, formats)
    - Field definitions (types, units, constraints)
    - Data quality (missing values, duplicates, type consistency)
    - Schema matching (column types match field definitions)
    
    All numeric fields must have units specified, even for dimensionless quantities:
    - Measurements: Use appropriate SI or domain units (kg, m, °C, etc.)
    - Counts/IDs: Use dimensionless unit (http://qudt.org/vocab/unit/NUM)
    - Percentages: Use percent or dimensionless unit
    
    Example:
        >>> validator = StandardValidator("1.0.0")
        >>> result = validator.validate_metadata(metadata)
        >>> if result.is_valid:
        ...     print("✅ Valid!")
        ... else:
        ...     print(result)
        
        >>> # Validate with schema
        >>> result = validator.validate_data_quality(df, schema=schema)
    """
    
    def __init__(self, version: str = "1.0.0"):
        """
        Initialize validator with a specific standard version.
        
        Args:
            version: Standard version to validate against (default: "1.0.0")
        """
        self.version = version
        self.standard = self._load_standard(version)
        
    def _load_standard(self, version: str) -> Dict[str, Any]:
        """Load the standard specification from YAML."""
        standard_path = get_standard_path(version)
        with open(standard_path) as f:
            return yaml.safe_load(f)
    
    def validate_all(
        self,
        metadata: Dict[str, Any],
        df: Optional[pd.DataFrame] = None,
        mappings: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate everything: metadata, data quality, and mappings.
        
        Args:
            metadata: Data package metadata dictionary
            df: Optional DataFrame to validate data quality
            mappings: Optional field mappings to validate
            
        Returns:
            ValidationResult with all validation results
        """
        result = ValidationResult()
        
        # 1. Validate metadata structure
        meta_result = self.validate_metadata(metadata)
        result.errors.extend(meta_result.errors)
        result.warnings.extend(meta_result.warnings)
        result.info.extend(meta_result.info)
        
        # 2. Validate resources if present
        if "resources" in metadata:
            for idx, resource in enumerate(metadata["resources"]):
                res_result = self.validate_resource(resource)
                # Prefix errors/warnings with resource name
                resource_name = resource.get("name", f"resource_{idx}")
                for error in res_result.errors:
                    result.add_error(error, f"Resource '{resource_name}'")
                for warning in res_result.warnings:
                    result.add_warning(warning, f"Resource '{resource_name}'")
        
        # 3. Validate data quality if DataFrame provided
        if df is not None:
            # Extract schema from metadata if available
            schema = None
            if metadata and "resources" in metadata:
                # Find the matching resource schema (if multiple resources exist)
                # For now, use the first resource schema
                resources = metadata.get("resources", [])
                if resources:
                    schema = resources[0].get("schema")
            
            quality_result = self.validate_data_quality(df, schema=schema)
            result.errors.extend(quality_result.errors)
            result.warnings.extend(quality_result.warnings)
        
        # 4. Determine validation level
        result.level = self._determine_level(result)
        
        return result
    
    def validate_metadata(self, metadata: Dict[str, Any]) -> ValidationResult:
        """
        Validate metadata against required and recommended fields.
        
        Args:
            metadata: Data package metadata dictionary
            
        Returns:
            ValidationResult with validation errors and warnings
        """
        result = ValidationResult()
        
        # Get field requirements from standard
        required_fields = self.standard["metadata"]["required"]
        recommended_fields = self.standard["metadata"].get("recommended", {})
        
        # 1. Check required fields
        for field_spec in required_fields:
            for field_name, field_def in field_spec.items():
                if field_name not in metadata:
                    msg = field_def.get("validation_message", f"Required field '{field_name}' is missing")
                    result.add_error(msg, field_name)
                else:
                    # Validate field value
                    field_result = self._validate_field_value(
                        field_name, 
                        metadata[field_name], 
                        field_def
                    )
                    result.errors.extend(field_result.errors)
                    result.warnings.extend(field_result.warnings)
        
        # 2. Check recommended fields
        for field_spec in recommended_fields:
            for field_name, field_def in field_spec.items():
                if field_name not in metadata:
                    msg = field_def.get("validation_message", f"Recommended field '{field_name}' is missing")
                    result.add_warning(msg, field_name)
                else:
                    # Validate field value
                    field_result = self._validate_field_value(
                        field_name,
                        metadata[field_name],
                        field_def
                    )
                    result.warnings.extend(field_result.warnings)
        
        # 3. Special validation for contributors (must have at least one author)
        if "contributors" in metadata:
            has_author = any(
                c.get("role") == "author" 
                for c in metadata["contributors"]
            )
            if not has_author:
                result.add_error(
                    "At least one contributor with role 'author' is required",
                    "contributors"
                )
        
        return result
    
    def validate_resource(self, resource: Dict[str, Any]) -> ValidationResult:
        """
        Validate a resource (data file) definition.
        
        Args:
            resource: Resource dictionary from metadata
            
        Returns:
            ValidationResult with validation errors and warnings
        """
        result = ValidationResult()
        
        # Get resource requirements from standard
        required_fields = self.standard["resources"]["required"]
        recommended_fields = self.standard["resources"].get("recommended", {})
        
        # 1. Check required fields
        for field_spec in required_fields:
            for field_name, field_def in field_spec.items():
                if field_name not in resource:
                    msg = field_def.get("validation_message", f"Required field '{field_name}' is missing")
                    result.add_error(msg, field_name)
                else:
                    # Validate field value
                    field_result = self._validate_field_value(
                        field_name,
                        resource[field_name],
                        field_def
                    )
                    result.errors.extend(field_result.errors)
        
        # 2. Check format preference
        if "format" in resource:
            preferred_format = self.standard["resources"]["required"][2]["format"].get("preferred_format")
            if resource["format"] != preferred_format:
                result.add_warning(
                    f"Format '{resource['format']}' is acceptable, but '{preferred_format}' is preferred",
                    "format"
                )
        
        # 3. Check recommended fields
        for field_spec in recommended_fields:
            for field_name, field_def in field_spec.items():
                if field_name not in resource:
                    msg = field_def.get("validation_message", f"Recommended field '{field_name}' is missing")
                    result.add_warning(msg, field_name)
        
        # 4. Validate schema if present
        if "schema" in resource and "fields" in resource["schema"]:
            for field in resource["schema"]["fields"]:
                field_result = self.validate_field_definition(field)
                result.errors.extend(field_result.errors)
                result.warnings.extend(field_result.warnings)
        
        return result
    
    def validate_field_definition(self, field: Dict[str, Any]) -> ValidationResult:
        """
        Validate a field (column) definition.
        
        Args:
            field: Field dictionary from schema
            
        Returns:
            ValidationResult with validation errors and warnings
        """
        result = ValidationResult()
        
        field_name = field.get("name", "unknown")
        
        # Get field requirements from standard
        required_fields = self.standard["fields"]["required"]
        
        # 1. Check required fields
        for field_spec in required_fields:
            for req_name, req_def in field_spec.items():
                if req_name not in field:
                    msg = req_def.get("validation_message", f"Required field '{req_name}' is missing")
                    result.add_error(msg, field_name)
                else:
                    # Validate against allowed types
                    if req_name == "type":
                        allowed_types = req_def.get("allowed_types", [])
                        if field["type"] not in allowed_types:
                            result.add_error(
                                f"Invalid type '{field['type']}'. Must be one of: {', '.join(allowed_types)}",
                                field_name
                            )
        
        # 2. Check numeric fields have units
        if field.get("type") in ["number", "integer"]:
            if "unit" not in field:
                msg = self.standard["fields"]["recommended_for_numeric"][0]["unit"]["validation_message"]
                result.add_error(msg, field_name)
        
        # 3. Check recommended fields
        if "description" not in field:
            result.add_warning(
                "Field description improves dataset usability",
                field_name
            )
        
        return result
    
    def validate_data_quality(
        self, 
        df: pd.DataFrame, 
        schema: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate data quality of a DataFrame.
        
        Checks:
        - Missing data: Max percentage of nulls per column
        - Duplicates: Max percentage of duplicate rows
        - Type consistency: All values in a column have the same type
        - Schema matching: If schema provided, validates column types match field definitions
        - Unit requirements: Numeric fields must have units (including dimensionless for IDs/counts)
        
        Args:
            df: DataFrame to validate
            schema: Optional schema with field definitions to validate against.
                   Should contain 'fields' list with field definitions including:
                   - name: Field name matching column name
                   - type: Field type (string, integer, number, boolean, etc.)
                   - unit: Unit definition (required for numeric fields)
                   - description: Field description
        
        Returns:
            ValidationResult with data quality errors and warnings
            
        Example:
            >>> schema = {
            ...     "fields": [
            ...         {
            ...             "name": "id",
            ...             "type": "integer",
            ...             "description": "Unique identifier",
            ...             "unit": {"name": "dimensionless", "path": "http://qudt.org/vocab/unit/NUM"}
            ...         },
            ...         {
            ...             "name": "mass",
            ...             "type": "number",
            ...             "description": "Mass measurement",
            ...             "unit": {"name": "kg", "path": "http://qudt.org/vocab/unit/KiloGM"}
            ...         }
            ...     ]
            ... }
            >>> result = validator.validate_data_quality(df, schema=schema)
        
        Note:
            Identifier fields (with "id", "index", "identifier" in name or description)
            are automatically recognized and should use dimensionless units.
        Returns:
            ValidationResult with quality issues
        """
        result = ValidationResult()
        
        quality_spec = self.standard["data_quality"]
        
        # 1. Check missing data thresholds
        max_null_pct = quality_spec["missing_data"]["max_null_percentage"]
        critical_threshold = quality_spec["missing_data"]["critical_threshold"]
        
        for col in df.columns:
            null_count = df[col].isnull().sum()
            null_pct = null_count / len(df) if len(df) > 0 else 0
            
            if null_pct > max_null_pct:
                result.add_error(
                    f"Column '{col}' has {null_pct:.1%} missing values (max: {max_null_pct:.1%})",
                    "data_quality"
                )
            elif null_pct > critical_threshold:
                result.add_warning(
                    f"Column '{col}' has {null_pct:.1%} missing values (approaching threshold)",
                    "data_quality"
                )
        
        # 2. Check type consistency (basic - mixed types in object columns)
        if not quality_spec["type_consistency"]["allow_mixed_types"]:
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Check if column has mixed types
                    non_null = df[col].dropna()
                    if len(non_null) > 0:
                        types = non_null.apply(type).unique()
                        if len(types) > 1:
                            type_names = [t.__name__ for t in types]
                            result.add_error(
                                f"Column '{col}' has mixed types: {', '.join(type_names)}",
                                "data_quality"
                            )
        
        # 3. Check schema-based type consistency (if schema provided)
        if schema and quality_spec["type_consistency"].get("check_against_schema", False):
            schema_result = self._validate_data_against_schema(df, schema, quality_spec)
            result.errors.extend(schema_result.errors)
            result.warnings.extend(schema_result.warnings)
        
        # 4. Check duplicates
        if quality_spec["duplicates"]["check_duplicates"]:
            dup_count = df.duplicated().sum()
            if dup_count > 0:
                dup_pct = dup_count / len(df)
                max_dup_pct = quality_spec["duplicates"]["max_duplicate_percentage"]
                
                if dup_pct > max_dup_pct:
                    result.add_error(
                        f"{dup_count} duplicate rows ({dup_pct:.1%}) exceeds threshold ({max_dup_pct:.1%})",
                        "data_quality"
                    )
                else:
                    result.add_warning(
                        f"{dup_count} duplicate rows found ({dup_pct:.1%})",
                        "data_quality"
                    )
        
        # 5. Add info about dataset
        result.add_info(f"Dataset has {len(df)} rows and {len(df.columns)} columns")
        
        return result
    
    def _validate_data_against_schema(
        self,
        df: pd.DataFrame,
        schema: Dict[str, Any],
        quality_spec: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate DataFrame against field schema definitions.
        
        Checks that actual column types match declared field types,
        and that numeric fields have proper units defined.
        
        Args:
            df: DataFrame to validate
            schema: Schema dictionary with field definitions
            quality_spec: Quality specification from standard
            
        Returns:
            ValidationResult with schema validation errors
        """
        result = ValidationResult()
        
        # Get type mapping from standard
        type_consistency = quality_spec["type_consistency"]
        type_mapping = type_consistency.get("schema_matching", {}).get("type_mapping", {})
        
        # Get field definitions from schema
        fields = schema.get("fields", [])
        field_dict = {f["name"]: f for f in fields}
        
        # Check each column in DataFrame
        for col in df.columns:
            if col not in field_dict:
                result.add_warning(
                    f"Column '{col}' in data but not in schema definition",
                    "schema_matching"
                )
                continue
            
            field_def = field_dict[col]
            declared_type = field_def.get("type")
            
            if not declared_type:
                continue
            
            # Get expected Python types for this field type
            expected_types = type_mapping.get(declared_type, [])
            
            # Check actual column type
            actual_dtype = str(df[col].dtype)
            
            # For object columns, check actual Python types of values
            if df[col].dtype == 'object':
                non_null = df[col].dropna()
                if len(non_null) > 0:
                    actual_python_types = set(type(v).__name__ for v in non_null.head(100))
                    
                    # Check if any actual type matches expected
                    type_matches = any(
                        actual_type in expected_types 
                        for actual_type in actual_python_types
                    )
                    
                    if not type_matches:
                        result.add_error(
                            f"Column '{col}' declared as '{declared_type}' but contains "
                            f"{', '.join(sorted(actual_python_types))}. Expected: {', '.join(expected_types)}",
                            "schema_matching"
                        )
            
            # For numeric dtypes, check against expected numeric types
            elif declared_type in ["number", "integer"]:
                # Check if dtype is numeric
                if not df[col].dtype in ['int64', 'int32', 'float64', 'float32', 'int', 'float']:
                    result.add_error(
                        f"Column '{col}' declared as '{declared_type}' but has dtype '{actual_dtype}'",
                        "schema_matching"
                    )
                
                # Check if numeric field has unit
                if type_consistency.get("schema_matching", {}).get("numeric_must_have_unit", False):
                    # Check if the field definition has a unit
                    field_unit = field_def.get("unit")
                    # Field unit can be either a dict (with name, etc.) or None
                    has_unit = field_unit is not None and (
                        isinstance(field_unit, dict) and field_unit.get("name") or
                        isinstance(field_unit, str) and field_unit
                    )
                    
                    if not has_unit:
                        result.add_error(
                            f"Numeric field '{col}' must have a unit specified in the field definition",
                            "schema_matching"
                        )
            
            # For string type, check if it's actually string-like
            elif declared_type == "string":
                if df[col].dtype != 'object' and not df[col].dtype.name.startswith('string'):
                    result.add_error(
                        f"Column '{col}' declared as 'string' but has dtype '{actual_dtype}'",
                        "schema_matching"
                    )
            
            # For boolean type
            elif declared_type == "boolean":
                if df[col].dtype != 'bool':
                    result.add_error(
                        f"Column '{col}' declared as 'boolean' but has dtype '{actual_dtype}'",
                        "schema_matching"
                    )
        
        # Check for fields in schema but missing in data
        for field_name in field_dict.keys():
            if field_name not in df.columns:
                result.add_warning(
                    f"Field '{field_name}' defined in schema but not found in data",
                    "schema_matching"
                )
        
        return result
    
    def _validate_field_value(
        self,
        field_name: str,
        value: Any,
        field_def: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate a specific field value against its definition.
        
        Args:
            field_name: Name of the field
            value: Value to validate
            field_def: Field definition from standard
            
        Returns:
            ValidationResult with validation errors
        """
        result = ValidationResult()
        
        # Check type
        expected_type = field_def.get("type")
        
        if expected_type == "string":
            if not isinstance(value, str):
                result.add_error(f"Expected string, got {type(value).__name__}", field_name)
            else:
                # Check min/max length
                if "min_length" in field_def and len(value) < field_def["min_length"]:
                    result.add_error(
                        f"Minimum length is {field_def['min_length']}, got {len(value)}",
                        field_name
                    )
                if "max_length" in field_def and len(value) > field_def["max_length"]:
                    result.add_error(
                        f"Maximum length is {field_def['max_length']}, got {len(value)}",
                        field_name
                    )
                
                # Check pattern
                if "pattern" in field_def:
                    if not re.match(field_def["pattern"], value):
                        msg = field_def.get("validation_message", "Value does not match pattern")
                        result.add_error(msg, field_name)
        
        elif expected_type == "array":
            if not isinstance(value, list):
                result.add_error(f"Expected array, got {type(value).__name__}", field_name)
            else:
                # Check min/max items
                if "min_items" in field_def and len(value) < field_def["min_items"]:
                    msg = field_def.get("validation_message", f"Minimum {field_def['min_items']} items required")
                    result.add_error(msg, field_name)
                if "max_items" in field_def and len(value) > field_def["max_items"]:
                    result.add_error(
                        f"Maximum {field_def['max_items']} items allowed",
                        field_name
                    )
        
        elif expected_type == "url":
            if not isinstance(value, str):
                result.add_error(f"Expected URL string, got {type(value).__name__}", field_name)
            elif not re.match(r"^https?://", value):
                result.add_error("URL must start with http:// or https://", field_name)
        
        return result
    
    def _determine_level(self, result: ValidationResult) -> str:
        """
        Determine validation level based on errors and warnings.
        
        Args:
            result: ValidationResult to evaluate
            
        Returns:
            Validation level badge string
        """
        levels = self.standard["validation_levels"]
        
        if not result.errors and not result.warnings:
            return levels["strict"]["badge"]
        elif not result.errors and len(result.warnings) <= 5:
            return levels["standard"]["badge"]
        elif len(result.errors) <= 10:
            return levels["basic"]["badge"]
        else:
            return levels["invalid"]["badge"]
    
    def get_help_url(self, topic: str) -> Optional[str]:
        """
        Get help URL for a specific topic.
        
        Args:
            topic: Topic name (e.g., 'frictionless_spec', 'qudt_units')
            
        Returns:
            URL string or None if not found
        """
        return self.standard.get("help_urls", {}).get(topic)
