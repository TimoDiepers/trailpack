"""Validation service for data packages using Trailpack standards."""
from typing import Dict, List, Any, Optional
from app.models.schemas import (
    ColumnMapping,
    GeneralDetails,
    ExcelPreview,
    ValidationResult as APIValidationResult
)


class ValidationService:
    """Service for validating data packages against Trailpack standards."""
    
    @staticmethod
    def validate_mappings(
        mappings: List[ColumnMapping],
        general_details: Optional[GeneralDetails],
        excel_preview: Optional[ExcelPreview]
    ) -> APIValidationResult:
        """
        Validate column mappings and metadata against requirements.
        
        Args:
            mappings: List of column mappings
            general_details: Package metadata
            excel_preview: Excel file preview data
            
        Returns:
            ValidationResult with errors, warnings, and quality level
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        # Build column lookup from preview
        column_info = {}
        if excel_preview and excel_preview.columns:
            for col in excel_preview.columns:
                column_info[col.name] = col
        
        # Validate each column mapping
        for mapping in mappings:
            col_info = column_info.get(mapping.excelColumn)
            
            # Check if column has ontology OR description
            has_ontology = mapping.pystConcept is not None
            has_description = mapping.description and len(mapping.description.strip()) > 0
            
            if not has_ontology and not has_description:
                errors.append(
                    f"Column '{mapping.excelColumn}': Must have either an ontology mapping or a description"
                )
            
            # Check numeric columns have units
            if col_info and col_info.isNumeric:
                if not mapping.unit:
                    errors.append(
                        f"Column '{mapping.excelColumn}': Numeric columns must have a unit defined"
                    )
            
            # Warn if no ontology mapping (even with description)
            if not has_ontology and has_description:
                warnings.append(
                    f"Column '{mapping.excelColumn}': Has description but no ontology mapping. "
                    "Consider adding an ontology concept for better interoperability."
                )
        
        # Validate general details if provided
        if general_details:
            # Check required fields
            if not general_details.name:
                errors.append("Package name is required")
            elif not _validate_package_name(general_details.name):
                errors.append(
                    f"Package name '{general_details.name}' is invalid. "
                    "Must contain only lowercase letters, numbers, hyphens, underscores, and dots."
                )
            
            if not general_details.title:
                errors.append("Package title is required")
            
            # Check licenses
            if not general_details.licenses or len(general_details.licenses) == 0:
                errors.append("At least one license is required")
            
            # Check contributors
            if not general_details.contributors or len(general_details.contributors) == 0:
                errors.append("At least one contributor is required")
            
            # Check sources
            if not general_details.sources or len(general_details.sources) == 0:
                errors.append("At least one data source is required")
            
            # Warnings for recommended fields
            if not general_details.description:
                warnings.append("Package description is recommended for better documentation")
            
            if not general_details.version:
                warnings.append("Package version is recommended for version tracking")
            
            if not general_details.keywords or len(general_details.keywords) == 0:
                warnings.append("Keywords are recommended to help others discover your dataset")
        else:
            errors.append("General details (metadata) are required")
        
        # Determine quality level
        is_valid = len(errors) == 0
        
        if len(errors) > 0:
            quality_level = "ERROR"
        elif len(warnings) > 0:
            quality_level = "WARNING"
        else:
            quality_level = "VALID"
        
        return APIValidationResult(
            isValid=is_valid,
            errors=errors,
            warnings=warnings,
            qualityLevel=quality_level
        )
    
    @staticmethod
    def validate_for_export(
        mappings: List[ColumnMapping],
        general_details: GeneralDetails,
        excel_preview: ExcelPreview
    ) -> Dict[str, Any]:
        """
        Comprehensive validation before export.
        
        Returns validation result with additional export-specific checks.
        """
        # Run standard validation
        result = ValidationService.validate_mappings(
            mappings, general_details, excel_preview
        )
        
        # Additional export-specific checks
        additional_warnings = []
        
        # Check for data quality indicators
        if excel_preview.rowCount == 0:
            result.errors.append("Cannot export empty dataset")
        elif excel_preview.rowCount < 10:
            additional_warnings.append(
                f"Dataset has only {excel_preview.rowCount} rows. "
                "Consider adding more data for statistical significance."
            )
        
        # Check for reasonable column count
        if len(mappings) > 100:
            additional_warnings.append(
                f"Dataset has {len(mappings)} columns. "
                "Consider normalizing data into multiple related tables."
            )
        
        # Add additional warnings
        result.warnings.extend(additional_warnings)
        
        # Update quality level if needed
        if additional_warnings and result.qualityLevel == "VALID":
            result.qualityLevel = "WARNING"
        
        return {
            "isValid": result.isValid,
            "errors": result.errors,
            "warnings": result.warnings,
            "qualityLevel": result.qualityLevel,
            "stats": {
                "totalColumns": len(mappings),
                "mappedColumns": len([m for m in mappings if m.pystConcept]),
                "numericColumns": len([
                    m for m in mappings 
                    if any(c.name == m.excelColumn and c.isNumeric 
                          for c in excel_preview.columns)
                ]),
                "withUnits": len([m for m in mappings if m.unit]),
                "withDescriptions": len([m for m in mappings if m.description]),
                "totalRows": excel_preview.rowCount,
            }
        }


def _validate_package_name(name: str) -> bool:
    """Validate package name format."""
    import re
    if not name:
        return False
    if not re.match(r"^[a-z0-9\-_\.]+$", name):
        return False
    if name.startswith(".") or name.endswith("."):
        return False
    return True


# Singleton instance
validation_service = ValidationService()
