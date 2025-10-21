"""Excel upload and processing endpoints."""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import Optional
from app.models.schemas import ExcelPreview
from app.services.excel_service import excel_service

router = APIRouter(prefix="/excel", tags=["excel"])


@router.post("/upload", response_model=ExcelPreview)
async def upload_excel(
    file: UploadFile = File(...),
    sheet_name: Optional[str] = Query(None, description="Specific sheet name to process")
):
    """
    Upload and process Excel file.
    
    Returns preview data including columns, types, and sample rows.
    Optionally specify sheet_name to process a specific sheet.
    """
    try:
        # Validate file
        excel_service.validate_excel_file(file)
        
        # Process file
        preview = await excel_service.process_excel(file, sheet_name)
        
        return preview
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process Excel file: {str(e)}")
