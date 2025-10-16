"""
Export service for converting UI data to Frictionless Data Package in Parquet.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from trailpack.packing.datapackage_schema import (
    DataPackageSchema,
    Field,
    MetaDataBuilder,
    Resource,
    Unit,
)
from trailpack.packing.packing import Packing
from trailpack.validation.standard_validator import StandardValidator


class DataPackageExporter:
    """Service for exporting UI data to Frictionless Data Package in Parquet."""

    def __init__(
        self,
        df: pd.DataFrame,
        column_mappings: Dict[str, str],
        general_details: Dict[str, Any],
        sheet_name: str,
        file_name: str,
        suggestions_cache: Dict[str, List] = None,
        standard_version: str = "1.0.0",
    ):
        """
        Initialize with UI session state data.

        Args:
            df: Pandas DataFrame with the actual data
            column_mappings: Mapping of column names to PyST concept IDs
            general_details: Metadata from the general details form
            sheet_name: Name of the Excel sheet
            file_name: Original file name
            suggestions_cache: Cache of PyST suggestions with id and label
            standard_version: Trailpack standard version to validate against
        """
        self.df = df
        self.column_mappings = column_mappings
        self.general_details = general_details
        self.sheet_name = sheet_name
        self.file_name = file_name
        self.suggestions_cache = suggestions_cache or {}
        self.schema = DataPackageSchema()
        self.validator = StandardValidator(standard_version)

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate all inputs before processing."""
        errors = []

        if self.df is None or self.df.empty:
            errors.append("DataFrame is empty or None")

        if not self.general_details.get("name"):
            errors.append("Package name is required")

        if "name" in self.general_details:
            is_valid, error_msg = self.schema.validate_package_name(
                self.general_details["name"]
            )
            if not is_valid:
                errors.append(f"Invalid package name: {error_msg}")

        return len(errors) == 0, errors

    def build_fields(self) -> List[Field]:
        """Convert column mappings to Field definitions."""
        fields = []

        for column in self.df.columns:
            # Infer type
            field_type = self._infer_field_type(self.df[column])

            # Get ontology mapping
            ontology_id = self.column_mappings.get(column)

            # Build unit if numeric
            unit = None
            if pd.api.types.is_numeric_dtype(self.df[column]):
                unit_id = self.column_mappings.get(f"{column}_unit")
                if unit_id:
                    # Find label from suggestions cache
                    unit_label = self._find_label_for_id(unit_id)
                    unit = Unit(
                        name=unit_label or unit_id.split("/")[-1],
                        long_name=unit_label,
                        path=unit_id,
                    )

            # Handle numeric fields without unit - use dimensionless
            if field_type in ["number", "integer"] and not unit:
                unit = Unit(
                    name="NUM",
                    long_name="dimensionless number",
                    path="https://vocab.sentier.dev/units/unit/NUM",
                )

            # Build description: use column name if no ontology mapping found
            if ontology_id:
                # Has ontology mapping - use generic description
                description = f"Column from {self.sheet_name}"
            else:
                # No ontology mapping - use column name in description for better metadata
                description = f"{column} (from {self.sheet_name})"

            field = Field(
                name=column,
                type=field_type,
                description=description,
                unit=unit,
                rdf_type=ontology_id,
                taxonomy_url=ontology_id if ontology_id else None,
            )
            fields.append(field)

        return fields

    def build_resource(self, fields: List[Field]) -> Resource:
        """Create Resource definition with fields."""
        resource_name = f"{Path(self.file_name).stem}_{self.sheet_name.replace(' ', '_')}".lower().replace(
            " ", "_"
        )

        return Resource(
            name=resource_name,
            path=f"{resource_name}.parquet",
            title=self.general_details.get("title", self.file_name),
            description=self.general_details.get(
                "description", f"Data from {self.sheet_name}"
            ),
            format="parquet",
            mediatype="application/vnd.apache.parquet",
            encoding="utf-8",
            profile="tabular-data-resource",
            fields=fields,
        )

    def build_metadata(self, resource: Resource) -> Dict[str, Any]:
        """Build complete metadata using MetaDataBuilder."""
        builder = MetaDataBuilder()

        builder.set_basic_info(
            name=self.general_details["name"],
            title=self.general_details.get("title"),
            description=self.general_details.get("description"),
            version=self.general_details.get("version"),
        )

        if "profile" in self.general_details:
            builder.set_profile(self.general_details["profile"])
        if "keywords" in self.general_details:
            builder.set_keywords(self.general_details["keywords"])

        builder.set_links(
            homepage=self.general_details.get("homepage"),
            repository=self.general_details.get("repository"),
        )

        for license_data in self.general_details.get("licenses", []):
            builder.add_license(
                name=license_data["name"],
                title=license_data.get("title"),
                path=license_data.get("path"),
            )

        for contrib in self.general_details.get("contributors", []):
            builder.add_contributor(
                name=contrib["name"],
                role=contrib.get("role", "author"),
                email=contrib.get("email"),
                organization=contrib.get("organization"),
            )

        for source in self.general_details.get("sources", []):
            builder.add_source(
                title=source["title"],
                path=source.get("path"),
                description=source.get("description"),
            )

        if "created" in self.general_details:
            builder.metadata["created"] = self.general_details["created"]
        if "modified" in self.general_details:
            builder.metadata["modified"] = self.general_details["modified"]

        builder.add_resource(resource)

        return builder.build()

    def export(
        self, output_path: str, validate_standard: bool = True
    ) -> Tuple[str, Optional[str], Optional[Any]]:
        """
        Execute full export workflow and write Parquet.

        Args:
            output_path: Path where Parquet file will be written
            validate_standard: Whether to validate against Trailpack standard (default: True)

        Returns:
            Tuple of (output_path, quality_level, validation_result)
            - output_path: Path to exported Parquet file
            - quality_level: Validation level ("STRICT", "STANDARD", "BASIC", "INVALID") or None if validation skipped
            - validation_result: Full ValidationResult object for report generation, or None if validation skipped

        Raises:
            ValueError: If validation fails or data quality issues found
        """
        # Validate basic inputs
        is_valid, errors = self.validate()
        if not is_valid:
            raise ValueError(f"Validation failed: {', '.join(errors)}")

        # Validate DataFrame for Parquet compatibility
        self._validate_dataframe_for_parquet(self.df)

        # Build fields
        fields = self.build_fields()

        # Build resource
        resource = self.build_resource(fields)

        # Build metadata
        metadata = self.build_metadata(resource)

        # Validate against Trailpack standard (if enabled)
        quality_level = None
        validation_result = None
        if validate_standard:
            validation_result = self.validator.validate_all(
                metadata=metadata, df=self.df, mappings=self.column_mappings
            )

            # Check if validation passed
            if not validation_result.is_valid:
                error_msg = self._format_validation_errors(validation_result)
                raise ValueError(error_msg)

            quality_level = (
                validation_result.level
            )  # "STRICT", "STANDARD", "BASIC", or "INVALID"

        # Write to Parquet
        packer = Packing(data=self.df, meta_data=metadata)
        packer.write_parquet(output_path)

        return output_path, quality_level, validation_result

    def _validate_dataframe_for_parquet(self, df: pd.DataFrame) -> None:
        """Validate DataFrame is compatible with Arrow/Parquet format.

        Raises:
            ValueError: If data quality issues are found (e.g., mixed types in columns)
        """
        errors = []

        for column in df.columns:
            # Check for mixed types in object columns
            if df[column].dtype == "object":
                non_null_values = df[column].dropna()
                if len(non_null_values) == 0:
                    continue

                # Get unique types in the column
                types = non_null_values.apply(type).unique()

                if len(types) > 1:
                    type_names = [t.__name__ for t in types]
                    sample_values = []
                    for t in types:
                        sample = non_null_values[non_null_values.apply(type) == t].iloc[
                            0
                        ]
                        sample_values.append(f"{t.__name__}: {repr(sample)}")

                    errors.append(
                        f"Column '{column}' contains mixed data types: {', '.join(type_names)}.\n"
                        f"  Examples: {' | '.join(sample_values)}\n"
                        f"  Please ensure all values in this column are of the same type."
                    )

        if errors:
            error_message = (
                "Data quality issues found that prevent Parquet conversion:\n\n"
            )
            error_message += "\n\n".join(f"{i+1}. {e}" for i, e in enumerate(errors))
            error_message += "\n\nPlease clean your data and try again."
            raise ValueError(error_message)

    def _infer_field_type(self, series: pd.Series) -> str:
        """Infer Frictionless field type from pandas Series."""
        if pd.api.types.is_integer_dtype(series):
            return "integer"
        elif pd.api.types.is_float_dtype(series):
            return "number"
        elif pd.api.types.is_bool_dtype(series):
            return "boolean"
        elif pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        else:
            return "string"

    def _find_label_for_id(self, concept_id: str) -> Optional[str]:
        """Find label for a PyST concept ID from suggestions cache."""
        for cache_key, suggestions in self.suggestions_cache.items():
            for s in suggestions:
                try:
                    if isinstance(s, dict):
                        s_id = s.get("id") or s.get("id_") or s.get("uri")
                        s_label = s.get("label") or s.get("name")
                    else:
                        s_id = getattr(s, "id", None) or getattr(s, "id_", None)
                        s_label = getattr(s, "label", None) or getattr(s, "name", None)

                    if str(s_id) == str(concept_id):
                        return str(s_label) if s_label else None
                except Exception:
                    continue
        return None

    def _format_validation_errors(self, validation_result) -> str:
        """Format validation errors for better readability."""
        lines = []
        lines.append("=" * 80)
        lines.append("STANDARD VALIDATION FAILED")
        lines.append("=" * 80)

        if validation_result.level:
            lines.append(f"\nValidation Level: {validation_result.level}")

        # Format errors
        if validation_result.errors:
            lines.append(f"\nERRORS ({len(validation_result.errors)}):")
            lines.append("-" * 80)
            for i, error in enumerate(validation_result.errors, 1):
                lines.append(f"{i}. {error}")

        # Format warnings
        if validation_result.warnings:
            lines.append(f"\nWARNINGS ({len(validation_result.warnings)}):")
            lines.append("-" * 80)
            for i, warning in enumerate(validation_result.warnings, 1):
                lines.append(f"{i}. {warning}")

        lines.append("\n" + "=" * 80)
        lines.append("Please fix the errors above and try again.")
        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_validation_report(self, validation_result) -> str:
        """
        Generate a complete validation report for download.

        Includes errors, warnings, and info (data quality metrics).

        Args:
            validation_result: ValidationResult object from validation

        Returns:
            Formatted report as string
        """
        from datetime import datetime

        lines = []
        lines.append("=" * 80)
        lines.append("TRAILPACK VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Dataset: {self.file_name} - {self.sheet_name}")
        lines.append(f"Package Name: {self.general_details.get('name', 'N/A')}")

        if validation_result.level:
            lines.append(f"\nValidation Level: {validation_result.level}")

        lines.append(
            f"\nValidation Status: {'PASSED' if validation_result.is_valid else 'FAILED'}"
        )

        # Summary
        lines.append("\n" + "=" * 80)
        lines.append("SUMMARY")
        lines.append("=" * 80)
        lines.append(f"Errors: {len(validation_result.errors)}")
        lines.append(f"Warnings: {len(validation_result.warnings)}")
        lines.append(f"Info Messages: {len(validation_result.info)}")

        # Errors
        if validation_result.errors:
            lines.append("\n" + "=" * 80)
            lines.append("ERRORS")
            lines.append("=" * 80)
            for i, error in enumerate(validation_result.errors, 1):
                lines.append(f"{i}. {error}")

        # Warnings
        if validation_result.warnings:
            lines.append("\n" + "=" * 80)
            lines.append("WARNINGS")
            lines.append("=" * 80)
            for i, warning in enumerate(validation_result.warnings, 1):
                lines.append(f"{i}. {warning}")

        # Info (data quality metrics)
        if validation_result.info:
            lines.append("\n" + "=" * 80)
            lines.append("DATA QUALITY METRICS")
            lines.append("=" * 80)
            for i, info in enumerate(validation_result.info, 1):
                lines.append(f"{i}. {info}")

        # Dataset information
        lines.append("\n" + "=" * 80)
        lines.append("DATASET INFORMATION")
        lines.append("=" * 80)
        lines.append(f"Rows: {len(self.df)}")
        lines.append(f"Columns: {len(self.df.columns)}")
        lines.append(f"Columns mapped: {len(self.column_mappings)}")

        # Column mappings summary
        lines.append("\n" + "=" * 80)
        lines.append("COLUMN MAPPINGS")
        lines.append("=" * 80)
        for col in self.df.columns:
            mapping = self.column_mappings.get(col, "Not mapped")
            unit = self.column_mappings.get(f"{col}_unit", "")
            if unit:
                lines.append(f"- {col}: {mapping} (unit: {unit})")
            else:
                lines.append(f"- {col}: {mapping}")

        lines.append("\n" + "=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)

        return "\n".join(lines)
