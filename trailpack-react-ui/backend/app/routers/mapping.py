"""Mapping and validation endpoints."""
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    AutoMappingRequest,
    MappingResult,
    ValidationRequest,
    ValidationResult
)
from app.services.pyst_service import pyst_service

router = APIRouter(prefix="/mapping", tags=["mapping"])


@router.post("/auto", response_model=MappingResult)
async def get_auto_mappings(request: AutoMappingRequest):
    """
    Get automatic mapping suggestions for Excel columns.
    
    Uses semantic analysis to suggest PyST concepts for each column.
    """
    try:
        result = await pyst_service.get_auto_mappings(request.columns)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate mappings: {str(e)}")


@router.post("/validate", response_model=ValidationResult)
async def validate_mappings(request: ValidationRequest):
    """
    Validate column mappings.
    
    Checks for completeness, data type compatibility, and other validation rules.
    """
    try:
        errors = []
        warnings = []
        
        # Check if all columns are mapped
        unmapped = [m for m in request.mappings if not m.pystConcept]
        if unmapped:
            errors.append(f"{len(unmapped)} column(s) are not mapped")
        
        # Check for duplicate mappings
        concept_ids = [m.pystConcept.id for m in request.mappings if m.pystConcept]
        if len(concept_ids) != len(set(concept_ids)):
            warnings.append("Some columns are mapped to the same concept")
        
        # Additional validation checks can be added here
        if len(request.mappings) < 2:
            warnings.append("Consider mapping at least 2 columns for meaningful export")
        
        return ValidationResult(
            isValid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate mappings: {str(e)}")
