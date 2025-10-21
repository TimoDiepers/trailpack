"""Validation router for data package validation."""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from app.models.schemas import (
    ColumnMapping,
    GeneralDetails,
    ExcelPreview,
    ValidationResult as ValidationResultSchema
)
from app.services.validation_service import validation_service
from pydantic import BaseModel


class ValidationRequest(BaseModel):
    """Request for validation."""
    mappings: List[ColumnMapping]
    generalDetails: Optional[GeneralDetails] = None
    excelPreview: Optional[ExcelPreview] = None


router = APIRouter(prefix="/validation", tags=["validation"])


@router.post("/validate", response_model=Dict[str, Any])
async def validate_package(request: ValidationRequest):
    """
    Validate data package mappings and metadata.
    
    Checks:
    - All columns have ontology OR description
    - Numeric columns have units
    - Required metadata fields are present
    - Package name format is valid
    - Licenses, contributors, sources are defined
    
    Returns validation result with errors, warnings, and quality level.
    """
    try:
        result = validation_service.validate_mappings(
            mappings=request.mappings,
            general_details=request.generalDetails,
            excel_preview=request.excelPreview
        )
        return {
            "isValid": result.isValid,
            "errors": result.errors,
            "warnings": result.warnings,
            "qualityLevel": result.qualityLevel
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate-for-export")
async def validate_for_export_endpoint(request: ValidationRequest):
    """
    Comprehensive validation before export.
    
    Includes standard validation plus export-specific checks:
    - Data quality indicators
    - Dataset size checks
    - Column count recommendations
    
    Returns extended validation result with statistics.
    """
    try:
        if not request.generalDetails:
            raise HTTPException(
                status_code=400,
                detail="General details are required for export validation"
            )
        
        if not request.excelPreview:
            raise HTTPException(
                status_code=400,
                detail="Excel preview is required for export validation"
            )
        
        result = validation_service.validate_for_export(
            mappings=request.mappings,
            general_details=request.generalDetails,
            excel_preview=request.excelPreview
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

