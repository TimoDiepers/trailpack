"""Export endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response, JSONResponse
from typing import Dict, Any
import pandas as pd
import json

from app.models.schemas import ExportRequest
from app.services.datapackage_export_service import DataPackageExporter
from app.services.excel_service import excel_service

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/parquet")
async def export_to_parquet(request: ExportRequest):
    """
    Export mapped data to Parquet format with embedded DataPackage metadata.
    
    This endpoint:
    1. Retrieves the Excel data from session storage
    2. Builds complete Frictionless DataPackage metadata
    3. Uses the Packing class to embed metadata in Parquet
    4. Returns the Parquet file for download
    """
    try:
        # Retrieve Excel data from session
        excel_data = excel_service.get_cached_file(request.fileId)
        if not excel_data:
            raise HTTPException(
                status_code=404,
                detail=f"Excel file not found in session: {request.fileId}"
            )
        
        # Get the specific sheet
        if request.sheetName not in excel_data['sheets']:
            raise HTTPException(
                status_code=404,
                detail=f"Sheet '{request.sheetName}' not found in file"
            )
        
        sheet_data = excel_data['sheets'][request.sheetName]
        
        # Convert to DataFrame
        df = pd.DataFrame(sheet_data['data'])
        
        # Create exporter instance
        exporter = DataPackageExporter(
            df=df,
            mappings=request.mappings,
            general_details=request.generalDetails,
            sheet_name=request.sheetName,
            file_name=excel_data.get('fileName', 'data.xlsx')
        )
        
        # Export to bytes
        parquet_bytes, metadata, quality_level = exporter.export_to_bytes()
        
        # Determine filename
        output_filename = request.config.outputFileName
        if not output_filename.endswith('.parquet'):
            output_filename += '.parquet'
        
        # Return as downloadable file
        return Response(
            content=parquet_bytes,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={output_filename}",
                "X-Quality-Level": quality_level,
            }
        )
        
    except ValueError as ve:
        # Validation or data quality errors
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export data: {str(e)}"
        )


@router.post("/metadata")
async def export_metadata(request: ExportRequest):
    """
    Export only the DataPackage metadata as JSON.
    
    Useful for previewing metadata or downloading separately.
    """
    try:
        # Retrieve Excel data from session
        excel_data = excel_service.get_cached_file(request.fileId)
        if not excel_data:
            raise HTTPException(
                status_code=404,
                detail=f"Excel file not found in session: {request.fileId}"
            )
        
        # Get the specific sheet
        if request.sheetName not in excel_data['sheets']:
            raise HTTPException(
                status_code=404,
                detail=f"Sheet '{request.sheetName}' not found in file"
            )
        
        sheet_data = excel_data['sheets'][request.sheetName]
        
        # Convert to DataFrame
        df = pd.DataFrame(sheet_data['data'])
        
        # Create exporter instance
        exporter = DataPackageExporter(
            df=df,
            mappings=request.mappings,
            general_details=request.generalDetails,
            sheet_name=request.sheetName,
            file_name=excel_data.get('fileName', 'data.xlsx')
        )
        
        # Build metadata only
        fields = exporter.build_fields()
        resource = exporter.build_resource(fields)
        metadata = exporter.build_metadata(resource)
        
        # Return as JSON
        return JSONResponse(
            content=metadata,
            headers={
                "Content-Disposition": f"attachment; filename=datapackage.json"
            }
        )
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build metadata: {str(e)}"
        )


@router.post("/config")
async def export_config(request: ExportRequest):
    """
    Export the mapping configuration as JSON.
    
    Useful for saving and loading mapping configurations.
    """
    try:
        config_data = {
            "fileId": request.fileId,
            "sheetName": request.sheetName,
            "mappings": [m.model_dump() for m in request.mappings],
            "generalDetails": request.generalDetails.model_dump(),
            "exportConfig": request.config.model_dump()
        }
        
        # Return as JSON
        return JSONResponse(
            content=config_data,
            headers={
                "Content-Disposition": f"attachment; filename=mapping-config.json"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export config: {str(e)}"
        )
