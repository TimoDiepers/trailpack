"""
Export service for converting UI data to Frictionless Data Package in Parquet.
Integrates with the Packing class to embed metadata in Parquet files.
"""

from typing import Any, Dict, List, Tuple, Optional
from pathlib import Path
import pandas as pd
import re

from app.packing.datapackage_schema import (
    Field,
    Unit,
    Resource,
    MetaDataBuilder,
)
from app.packing.packing import Packing
from app.models.schemas import ColumnMapping, GeneralDetails


class DataPackageExporter:
    """Service for exporting UI data to Frictionless Data Package in Parquet."""
    
    def __init__(
        self,
        df: pd.DataFrame,
        mappings: List[ColumnMapping],
        general_details: GeneralDetails,
        sheet_name: str,
        file_name: str,
    ):
        """
        Initialize with UI session state data.
        
        Args:
            df: Pandas DataFrame with the actual data
            mappings: List of ColumnMapping objects from UI
            general_details: GeneralDetails object with metadata
            sheet_name: Name of the Excel sheet
            file_name: Original file name
        """
        self.df = df
        self.mappings = mappings
        self.general_details = general_details
        self.sheet_name = sheet_name
        self.file_name = file_name
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate all inputs before processing."""
        errors = []
        
        if self.df is None or self.df.empty:
            errors.append("DataFrame is empty or None")
        
        if not self.general_details.name:
            errors.append("Package name is required")
        
        # Validate package name format
        if self.general_details.name:
            if not re.match(r'^[a-z0-9\-_\.]+$', self.general_details.name):
                errors.append(
                    "Package name must contain only lowercase letters, numbers, "
                    "hyphens, underscores, and dots"
                )
        
        return len(errors) == 0, errors
    
    def _sanitize_resource_name(self, name: str) -> str:
        """
        Sanitize resource name to match the pattern ^[a-z0-9\\-_\\.]+$.
        
        The resource name must only contain:
        - Lowercase letters (a-z)
        - Numbers (0-9)
        - Hyphens (-)
        - Underscores (_)
        - Dots (.)
        
        Args:
            name: Raw name string to sanitize
        
        Returns:
            Sanitized name matching the required pattern
        """
        # Convert to lowercase
        name = name.lower()
        
        # Replace spaces with underscores
        name = name.replace(" ", "_")
        
        # Remove or replace invalid characters
        # Keep only lowercase letters, numbers, hyphens, underscores, and dots
        name = re.sub(r"[^a-z0-9\-_.]", "", name)
        
        # Ensure name doesn't start or end with dots
        name = name.strip(".")
        
        # Ensure name is not empty after sanitization
        if not name:
            name = "resource"
        
        return name
    
    def build_fields(self) -> List[Field]:
        """Convert column mappings to Field definitions."""
        fields = []
        
        for column in self.df.columns:
            # Find mapping for this column
            mapping = next(
                (m for m in self.mappings if m.excelColumn == column),
                None
            )
            
            # Infer type
            field_type = self._infer_field_type(self.df[column])
            
            # Get ontology mapping
            ontology_id = None
            if mapping and mapping.pystConcept:
                ontology_id = mapping.pystConcept.id
            
            # Build unit if numeric
            unit = None
            if pd.api.types.is_numeric_dtype(self.df[column]):
                if mapping and mapping.unit:
                    unit = Unit(
                        name=mapping.unit.name if hasattr(mapping.unit, 'name') else str(mapping.unit),
                        long_name=mapping.unit.name if hasattr(mapping.unit, 'name') else None,
                        path=mapping.unit.id if hasattr(mapping.unit, 'id') else None,
                    )
                else:
                    # Default to dimensionless for numeric fields without unit
                    unit = Unit(
                        name="NUM",
                        long_name="dimensionless number",
                        path="https://vocab.sentier.dev/units/unit/NUM",
                    )
            
            # Get description from mapping or use default
            description = mapping.description if mapping and mapping.description else f"Column from {self.sheet_name}"
            
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
        resource_name = self._sanitize_resource_name(
            f"{Path(self.file_name).stem}_{self.sheet_name}"
        )
        
        return Resource(
            name=resource_name,
            path=f"{resource_name}.parquet",
            title=self.general_details.title or self.file_name,
            description=self.general_details.description or f"Data from {self.sheet_name}",
            format="parquet",
            mediatype="application/vnd.apache.parquet",
            encoding="utf-8",
            profile="tabular-data-resource",
            fields=fields,
        )
    
    def build_metadata(self, resource: Resource) -> Dict[str, Any]:
        """Build complete metadata using MetaDataBuilder."""
        builder = MetaDataBuilder()
        
        # Basic info
        builder.set_basic_info(
            name=self.general_details.name,
            title=self.general_details.title,
            description=self.general_details.description,
            version=self.general_details.version,
        )
        
        if self.general_details.profile:
            builder.set_profile(self.general_details.profile)
        
        if self.general_details.keywords:
            builder.set_keywords(self.general_details.keywords)
        
        # Links
        builder.set_links(
            homepage=self.general_details.homepage,
            repository=self.general_details.repository,
        )
        
        # Licenses
        for license_data in self.general_details.licenses:
            builder.add_license(
                name=license_data.name,
                title=license_data.title,
                path=license_data.path,
            )
        
        # Contributors
        for contrib in self.general_details.contributors:
            builder.add_contributor(
                name=contrib.name,
                role=contrib.role,
                email=contrib.email,
                organization=contrib.organization,
            )
        
        # Sources
        for source in self.general_details.sources:
            builder.add_source(
                title=source.title,
                path=source.path,
                description=source.description,
            )
        
        # Timestamps
        if self.general_details.created:
            builder.metadata["created"] = self.general_details.created
        if self.general_details.modified:
            builder.metadata["modified"] = self.general_details.modified
        
        # Add resource
        builder.add_resource(resource)
        
        return builder.build()
    
    def export_to_bytes(self) -> Tuple[bytes, Dict[str, Any], str]:
        """
        Execute full export workflow and return Parquet as bytes.
        
        Returns:
            Tuple of (parquet_bytes, metadata, quality_level)
            - parquet_bytes: Parquet file content as bytes
            - metadata: Complete datapackage metadata
            - quality_level: Validation quality level (placeholder for now)
        
        Raises:
            ValueError: If validation fails
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
        
        # Use Packing class to create Parquet with embedded metadata
        packer = Packing(data=self.df, meta_data=metadata)
        parquet_bytes = packer.write_parquet_to_bytes()
        
        # Quality level - will be determined by validation in the future
        quality_level = "VALID"
        
        return parquet_bytes, metadata, quality_level
    
    def export_to_file(self, output_path: str) -> Tuple[str, Dict[str, Any], str]:
        """
        Execute full export workflow and write Parquet to file.
        
        Args:
            output_path: Path where Parquet file will be written
        
        Returns:
            Tuple of (output_path, metadata, quality_level)
        
        Raises:
            ValueError: If validation fails
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
        
        # Use Packing class to write Parquet with embedded metadata
        packer = Packing(data=self.df, meta_data=metadata)
        packer.write_parquet(output_path)
        
        # Quality level - will be determined by validation in the future
        quality_level = "VALID"
        
        return output_path, metadata, quality_level
    
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
                        sample = non_null_values[non_null_values.apply(type) == t].iloc[0]
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


# Singleton instance
datapackage_exporter_service = DataPackageExporter
