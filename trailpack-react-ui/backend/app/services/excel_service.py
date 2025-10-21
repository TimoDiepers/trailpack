"""Excel processing service."""
import pandas as pd
import io
import uuid
from typing import List, Dict, Any, Optional
from fastapi import UploadFile
from app.models.schemas import ExcelPreview, ExcelColumn


class ExcelService:
    """Service for processing Excel files."""
    
    def __init__(self):
        """Initialize with file cache."""
        self.file_cache: Dict[str, Dict[str, Any]] = {}
    
    async def process_excel(self, file: UploadFile, sheet_name: Optional[str] = None) -> ExcelPreview:
        """
        Process uploaded Excel file and extract preview data.
        
        Args:
            file: Uploaded Excel file
            sheet_name: Optional specific sheet to read
            
        Returns:
            ExcelPreview with column metadata and sample rows
        """
        # Read Excel file
        contents = await file.read()
        
        # Generate file ID for caching
        file_id = str(uuid.uuid4())
        
        # Get all sheet names
        excel_file = pd.ExcelFile(io.BytesIO(contents))
        available_sheets = excel_file.sheet_names
        
        # Use specified sheet or first sheet
        if sheet_name and sheet_name in available_sheets:
            selected_sheet = sheet_name
        else:
            selected_sheet = available_sheets[0] if available_sheets else None
        
        if not selected_sheet:
            raise ValueError("No sheets found in Excel file")
        
        # Cache file data for all sheets
        sheets_data = {}
        for sheet in available_sheets:
            df_sheet = pd.read_excel(io.BytesIO(contents), sheet_name=sheet)
            sheets_data[sheet] = {
                'data': df_sheet.to_dict('records'),
                'columns': list(df_sheet.columns),
                'rowCount': len(df_sheet)
            }
        
        self.file_cache[file_id] = {
            'fileName': file.filename,
            'sheets': sheets_data,
            'availableSheets': available_sheets
        }
        
        # Read the selected sheet for preview
        df = pd.read_excel(io.BytesIO(contents), sheet_name=selected_sheet)
        
        # Extract column information
        columns = []
        for col_name in df.columns:
            col_data = df[col_name]
            
            # Determine data type
            dtype_str = str(col_data.dtype)
            is_numeric = False
            if 'int' in dtype_str:
                col_type = 'number'
                is_numeric = True
            elif 'float' in dtype_str:
                col_type = 'number'
                is_numeric = True
            elif 'datetime' in dtype_str:
                col_type = 'datetime'
            elif 'bool' in dtype_str:
                col_type = 'boolean'
            else:
                col_type = 'string'
            
            # Get sample data (first 3 non-null values)
            sample_data = col_data.dropna().head(3).astype(str).tolist()
            
            columns.append(ExcelColumn(
                name=col_name,
                type=col_type,
                sampleData=sample_data,
                isNumeric=is_numeric
            ))
        
        # Get preview rows (first 10 rows)
        preview_rows = df.head(10).fillna('').to_dict('records')
        
        return ExcelPreview(
            columns=columns,
            rowCount=len(df),
            previewRows=preview_rows,
            availableSheets=available_sheets,
            selectedSheet=selected_sheet,
            fileId=file_id  # Include file ID in response
        )
    
    def get_cached_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached Excel file data by ID.
        
        Args:
            file_id: File identifier from upload
            
        Returns:
            Cached file data or None if not found
        """
        return self.file_cache.get(file_id)
    
    def clear_cache(self, file_id: Optional[str] = None) -> None:
        """
        Clear file cache.
        
        Args:
            file_id: Optional specific file ID to clear. If None, clears all.
        """
        if file_id:
            self.file_cache.pop(file_id, None)
        else:
            self.file_cache.clear()
    
    @staticmethod
    def validate_excel_file(file: UploadFile) -> None:
        """Validate uploaded Excel file."""
        if not file.filename:
            raise ValueError("No filename provided")
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise ValueError("File must be .xlsx or .xls format")
        
        if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
            raise ValueError("File size must be less than 10MB")


# Singleton instance
excel_service = ExcelService()
