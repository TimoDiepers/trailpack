"""Pydantic models for API request/response validation."""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class ExcelColumn(BaseModel):
    """Excel column metadata."""
    name: str
    type: str
    sampleData: List[str] = Field(default_factory=list)
    isNumeric: Optional[bool] = False


class ExcelPreview(BaseModel):
    """Excel file preview data."""
    columns: List[ExcelColumn]
    rowCount: int
    previewRows: List[Dict[str, Any]]
    availableSheets: Optional[List[str]] = None
    selectedSheet: Optional[str] = None
    fileId: Optional[str] = None  # Session file ID for later retrieval


class PystConcept(BaseModel):
    """PyST ontology concept."""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    uri: Optional[str] = None
    iri: Optional[str] = None
    label: Optional[str] = None


class ColumnMapping(BaseModel):
    """Mapping between Excel column and PyST concept."""
    excelColumn: str
    pystConcept: Optional[PystConcept] = None
    unit: Optional[PystConcept] = None  # Unit for numeric columns
    description: Optional[str] = None  # Custom description or comment
    confidence: Optional[float] = None


class License(BaseModel):
    """License information."""
    name: str
    title: str
    path: Optional[str] = None


class Contributor(BaseModel):
    """Contributor information."""
    name: str
    role: str  # author, contributor, maintainer, publisher, wrangler
    email: Optional[str] = None
    organization: Optional[str] = None


class Source(BaseModel):
    """Source information."""
    title: str
    path: Optional[str] = None
    description: Optional[str] = None


class GeneralDetails(BaseModel):
    """General package metadata."""
    name: str  # Package name (required)
    title: str  # Package title (required)
    description: Optional[str] = None
    version: Optional[str] = None
    profile: Optional[str] = "tabular-data-package"
    keywords: Optional[List[str]] = Field(default_factory=list)
    homepage: Optional[str] = None
    repository: Optional[str] = None
    created: Optional[str] = None  # ISO date
    modified: Optional[str] = None  # ISO date
    licenses: List[License]  # Required, at least one
    contributors: List[Contributor]  # Required, at least one
    sources: List[Source]  # Required, at least one
    resourceName: Optional[str] = None  # Resource name for the data file


class MappingResult(BaseModel):
    """Auto-mapping results."""
    mappings: List[ColumnMapping]
    unmappedColumns: List[str]


class AutoMappingRequest(BaseModel):
    """Request for auto-mapping."""
    columns: List[str]


class ValidationResult(BaseModel):
    """Mapping validation result."""
    isValid: bool
    errors: List[str]
    warnings: List[str]


class ValidationRequest(BaseModel):
    """Request for validation."""
    mappings: List[ColumnMapping]


class ExportConfig(BaseModel):
    """Export configuration."""
    includeMetadata: bool = True
    compressionType: str = "snappy"
    outputFileName: str = "output.parquet"


class ExportRequest(BaseModel):
    """Request for export."""
    fileId: str  # Session file ID to retrieve Excel data
    sheetName: str  # Sheet name to export
    mappings: List[ColumnMapping]
    generalDetails: GeneralDetails
    config: ExportConfig

