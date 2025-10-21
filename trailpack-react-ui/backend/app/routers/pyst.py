"""PyST ontology search endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.models.schemas import PystConcept
from app.services.pyst_service import pyst_service

router = APIRouter(prefix="/pyst", tags=["pyst"])


@router.get("/search", response_model=List[PystConcept])
async def search_concepts(q: str = Query(..., min_length=1)):
    """
    Search PyST ontology concepts.
    
    Args:
        q: Search query string
        
    Returns:
        List of matching PyST concepts
    """
    try:
        concepts = await pyst_service.search_concepts(q)
        return concepts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search concepts: {str(e)}")


@router.get("/concept/{concept_id}", response_model=PystConcept)
async def get_concept(concept_id: str):
    """Get specific concept by ID."""
    try:
        concept = await pyst_service.get_concept_by_id(concept_id)
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")
        return concept
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get concept: {str(e)}")
