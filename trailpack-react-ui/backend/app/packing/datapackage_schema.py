"""
DataPackage metadata schema and interactive builder classes using Pydantic.
Provides structured definitions and UI-friendly methods for creating
Frictionless Data Package metadata with automatic validation.
"""

from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field as PydanticField, field_validator, model_validator
from enum import Enum
import re
import codecs
from datetime import datetime


class FieldType(Enum):
    """Supported field types in data packages."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"
    TIME = "time"
    DURATION = "duration"


class ContributorRole(Enum):
    """Standard contributor roles."""

    AUTHOR = "author"
    CONTRIBUTOR = "contributor"
    MAINTAINER = "maintainer"
    PUBLISHER = "publisher"
    WRANGLER = "wrangler"


class License(BaseModel):
    """License information with automatic validation."""
    name: str = PydanticField('CC-BY-4.0', description="License identifier (e.g., 'CC-BY-4.0', 'MIT')")
    title: Optional[str] = PydanticField('Creative Commons Attribution 4.0 International', description="Human-readable license title")
    path: Optional[str] = PydanticField('https://spdx.org/licenses/CC-BY-4.0.html', description="URL to license text")
    
    @field_validator('path')
    @classmethod
    def validate_path_url(cls, v):
        """Validate URL format."""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('License path must be a valid http or https URL')
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format, excluding None values."""
        return self.model_dump(exclude_none=True)


class Contributor(BaseModel):
    """Contributor information with validation."""
    name: str = PydanticField(..., description="Contributor name")
    role: str = PydanticField("author", description="Contributor role")
    email: Optional[str] = PydanticField(None, description="Contact email address")
    organization: Optional[str] = PydanticField(None, description="Organization or affiliation")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Basic email validation."""
        if v and '@' not in v:
            raise ValueError('Email must contain @ symbol')
        return v
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        """Validate role is from accepted list."""
        valid_roles = ["author", "contributor", "maintainer", "publisher", "wrangler"]
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format, excluding None values."""
        return self.model_dump(exclude_none=True)


class Source(BaseModel):
    """Data source information with validation."""
    title: str = PydanticField(..., description="Source title")
    path: Optional[str] = PydanticField(None, description="Path to source data")
    description: Optional[str] = PydanticField(None, description="Source description")
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v):
        """Basic path validation."""
        if v and not (v.startswith(('http://', 'https://', 'file://')) or v.startswith('./')):
            # Allow relative paths, URLs, and file:// schemes
            pass
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format, excluding None values."""
        return self.model_dump(exclude_none=True)


class Unit(BaseModel):
    """Unit of measurement with QUDT vocabulary support."""
    name: str = PydanticField(..., description="Short unit name (e.g., 'kg', 'm', 'celsius')")
    long_name: Optional[str] = PydanticField(None, description="Full unit name (e.g., 'kilogram', 'meter', 'degree Celsius')")
    path: Optional[str] = PydanticField(None, description="QUDT or other vocabulary URI")
    
    @field_validator('path')
    @classmethod
    def validate_path_url(cls, v):
        """Validate URI format."""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('path must be a valid URL')
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for metadata."""
        result = {"name": self.name}
        if self.long_name:
            result["longName"] = self.long_name
        if self.path:
            result["path"] = self.path
        return result


class FieldConstraints(BaseModel):
    """Field validation constraints with validation."""
    required: Optional[bool] = PydanticField(None, description="Field is required")
    unique: Optional[bool] = PydanticField(None, description="Field values must be unique")
    minimum: Optional[Union[int, float]] = PydanticField(None, description="Minimum value")
    maximum: Optional[Union[int, float]] = PydanticField(None, description="Maximum value")
    pattern: Optional[str] = PydanticField(None, description="Regular expression pattern")
    enum: Optional[List[str]] = PydanticField(None, description="Allowed values")
    
    @field_validator('minimum', 'maximum')
    @classmethod
    def validate_numeric_constraints(cls, v, info):
        """Validate numeric constraints."""
        if v is not None and info.field_name == 'maximum':
            # Note: We can't access 'minimum' here in v2, so we'll skip cross-field validation
            # Use model_validator for cross-field validation if needed
            pass
        return v
    
    @field_validator('pattern')
    @classmethod
    def validate_pattern(cls, v):
        """Validate regex pattern."""
        if v:
            try:
                re.compile(v)
            except re.error as e:
                raise ValueError(f'Invalid regex pattern: {e}') from e
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format, excluding None values."""
        return self.model_dump(exclude_none=True)


class Field(BaseModel):
    """Data field schema definition with validation."""
    name: str = PydanticField(..., description="Field name")
    type: str = PydanticField(..., description="Field type")
    description: Optional[str] = PydanticField(None, description="Field description")
    unit: Optional[Unit] = PydanticField(None, description="Unit of measurement")
    rdf_type: Optional[str] = PydanticField(None, description="RDF type URI")
    taxonomy_url: Optional[str] = PydanticField(None, description="Taxonomy URL")
    constraints: Optional[FieldConstraints] = PydanticField(None, description="Field constraints")
    
    @field_validator('type')
    @classmethod
    def validate_field_type(cls, v):
        """Validate field type is from accepted list."""
        valid_types = ["string", "number", "integer", "boolean", "date", "datetime", "time", "duration", "geopoint", "geojson", "object", "array", "any"]
        if v not in valid_types:
            raise ValueError(f'Field type must be one of: {", ".join(valid_types)}')
        return v
    
    @model_validator(mode='after')
    def validate_numeric_has_unit(self):
        """Validate that numeric fields have a unit."""
        if self.type in ['number', 'integer'] and self.unit is None:
            raise ValueError(f'Field "{self.name}" has numeric type "{self.type}" but no unit specified. Numeric fields must have a unit.')
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {"name": self.name, "type": self.type}
        
        # Add optional fields
        if self.description:
            result['description'] = self.description
        if self.unit:
            result['unit'] = self.unit.to_dict()
        if self.rdf_type:
            result['rdfType'] = self.rdf_type
        if self.taxonomy_url:
            result['taxonomyUrl'] = self.taxonomy_url
                
        if self.constraints:
            constraints_dict = self.constraints.to_dict()
            if constraints_dict:
                result["constraints"] = constraints_dict

        return result


class Resource(BaseModel):
    """Data resource (file) definition with validation."""
    name: str = PydanticField(..., description="Resource name")
    path: str = PydanticField(..., description="Path to resource")
    title: Optional[str] = PydanticField(None, description="Resource title")
    description: Optional[str] = PydanticField(None, description="Resource description")
    format: Optional[str] = PydanticField(None, description="File format")
    mediatype: Optional[str] = PydanticField(None, description="Media type")
    encoding: str = PydanticField("utf-8", description="Text encoding")
    profile: Optional[str] = PydanticField(None, description="Resource profile")
    fields: List[Field] = PydanticField(default_factory=list, description="Field definitions")
    primary_key: List[str] = PydanticField(default_factory=list, description="Primary key fields")
    
    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        """Validate format is recognized."""
        # Allow any format - validation can be extended as needed
        return v
    
    @field_validator('encoding')
    @classmethod  
    def validate_encoding(cls, v):
        """Validate encoding is valid."""
        try:
            codecs.lookup(v)
        except LookupError as exc:
            raise ValueError(f'Invalid encoding: {v}') from exc
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result: Dict[str, Any] = {"name": self.name, "path": self.path}
        
        # Add optional fields
        optional_fields = {
            'title': self.title,
            'description': self.description,
            'format': self.format,
            'mediatype': self.mediatype,
            'profile': self.profile
        }
        
        for key, value in optional_fields.items():
            if value:
                result[key] = value
        
        # Always include encoding field (recommended in Trailpack standard v1.0.0)
        result["encoding"] = self.encoding

        if self.fields:
            schema: Dict[str, Any] = {"fields": [field.to_dict() for field in self.fields]}
            if self.primary_key:
                schema["primaryKey"] = self.primary_key
            result["schema"] = schema

        return result


class DataPackageSchema:
    """
    DataPackage metadata schema definition with UI-friendly methods.
    Provides structure and validation for Frictionless Data Package metadata.
    """

    # Required fields
    REQUIRED_FIELDS = [
        "name",
        "title",
        "resources",
        "licenses",
        "created",
        "contributors",
        "sources",
    ]

    # Recommended fields
    RECOMMENDED_FIELDS = ["description", "version"]

    # Optional fields
    OPTIONAL_FIELDS = ["profile", "keywords", "homepage", "repository", "image", "id"]

    def __init__(self):
        """Initialize the schema definition."""
        self.field_definitions = self._create_field_definitions()

    def _create_field_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Create field definitions for UI generation."""
        return {
            "name": {
                "type": "string",
                "required": True,
                "label": "Package Name",
                "description": "URL-safe identifier for the package (lowercase, no spaces)",
                "placeholder": "my-dataset",
                "pattern": r"^[a-z0-9\-_\.]+$",
                "help": "Use lowercase letters, numbers, hyphens, and dots only",
            },
            "title": {
                "type": "string",
                "required": False,
                "label": "Title",
                "description": "Human-readable title for the dataset",
                "placeholder": "My Dataset Title",
            },
            "description": {
                "type": "text",
                "required": False,
                "label": "Description",
                "description": "Longer description explaining what the dataset contains",
                "placeholder": "This dataset contains...",
            },
            "version": {
                "type": "string",
                "required": False,
                "label": "Version",
                "description": "Version number using semantic versioning",
                "placeholder": "1.0.0",
                "pattern": r"^\d+\.\d+\.\d+(-[a-zA-Z0-9\-\.]+)?$",
            },
            "profile": {
                "type": "select",
                "required": False,
                "label": "Profile",
                "description": "Type of data package",
                "options": [
                    {"value": "tabular-data-package", "label": "Tabular Data Package"},
                    {"value": "data-package", "label": "Data Package"},
                    {"value": "fiscal-data-package", "label": "Fiscal Data Package"},
                ],
                "default": "tabular-data-package",
            },
            "keywords": {
                "type": "tags",
                "required": False,
                "label": "Keywords",
                "description": "Tags to help others discover your dataset",
                "placeholder": "astronomy, catalog, coordinates",
            },
            "homepage": {
                "type": "url",
                "required": False,
                "label": "Homepage",
                "description": "Project or dataset homepage URL",
                "placeholder": "https://example.com/my-project",
            },
            "repository": {
                "type": "url",
                "required": False,
                "label": "Repository",
                "description": "Code repository URL",
                "placeholder": "https://github.com/user/repo",
            },
            "created": {
                "type": "date",
                "required": False,
                "label": "Created Date",
                "description": "When the dataset was created",
                "default": datetime.now().isoformat()[:10],
            },
            "modified": {
                "type": "date",
                "required": False,
                "label": "Modified Date",
                "description": "When the dataset was last modified",
            },
        }

    def get_field_definition(self, field_name: str) -> Dict[str, Any]:
        """Get UI field definition for a specific field."""
        return self.field_definitions.get(field_name, {})

    def get_required_fields(self) -> List[str]:
        """Get list of required field names."""
        return self.REQUIRED_FIELDS.copy()

    def get_recommended_fields(self) -> List[str]:
        """Get list of recommended field names."""
        return self.RECOMMENDED_FIELDS.copy()

    def get_all_fields(self) -> List[str]:
        """Get list of all possible field names."""
        return self.REQUIRED_FIELDS + self.RECOMMENDED_FIELDS + self.OPTIONAL_FIELDS

    def validate_package_name(self, name: str) -> tuple[bool, str]:
        """Validate package name format."""
        if not name:
            return False, "Package name is required"

        if not re.match(r"^[a-z0-9\-_\.]+$", name):
            return (
                False,
                "Package name can only contain lowercase letters, numbers, hyphens, underscores, and dots",
            )

        if name.startswith(".") or name.endswith("."):
            return False, "Package name cannot start or end with a dot"

        return True, ""

    def validate_version(self, version: str) -> tuple[bool, str]:
        """Validate semantic version format."""
        if not version:
            return True, ""  # Version is optional

        if not re.match(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9\-\.]+)?$", version):
            return False, "Version must follow semantic versioning (e.g., 1.0.0)"

        return True, ""

    def validate_url(self, url: str) -> tuple[bool, str]:
        """Validate URL format."""
        if not url:
            return True, ""  # URLs are optional

        if not re.match(r"^https?://", url):
            return False, "URL must start with http:// or https://"

        return True, ""


class MetaDataBuilder:
    """Builder class for constructing DataPackage metadata incrementally."""
    
    def __init__(self):
        """Initialize empty metadata dictionary."""
        self.metadata: Dict[str, Any] = {}
    
    def set_basic_info(
        self,
        name: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        version: Optional[str] = None
    ) -> 'MetaDataBuilder':
        """Set basic package information."""
        self.metadata['name'] = name
        if title:
            self.metadata['title'] = title
        if description:
            self.metadata['description'] = description
        if version:
            self.metadata['version'] = version
        return self
    
    def set_profile(self, profile: str) -> 'MetaDataBuilder':
        """Set package profile."""
        self.metadata['profile'] = profile
        return self
    
    def set_keywords(self, keywords: List[str]) -> 'MetaDataBuilder':
        """Set package keywords."""
        if keywords:
            self.metadata['keywords'] = keywords
        return self
    
    def set_links(
        self,
        homepage: Optional[str] = None,
        repository: Optional[str] = None
    ) -> 'MetaDataBuilder':
        """Set homepage and repository links."""
        if homepage:
            self.metadata['homepage'] = homepage
        if repository:
            self.metadata['repository'] = repository
        return self
    
    def add_license(
        self,
        name: str,
        title: Optional[str] = None,
        path: Optional[str] = None
    ) -> 'MetaDataBuilder':
        """Add a license to the package."""
        if 'licenses' not in self.metadata:
            self.metadata['licenses'] = []
        
        license_dict = {'name': name}
        if title:
            license_dict['title'] = title
        if path:
            license_dict['path'] = path
        
        self.metadata['licenses'].append(license_dict)
        return self
    
    def add_contributor(
        self,
        name: str,
        role: str = "author",
        email: Optional[str] = None,
        organization: Optional[str] = None
    ) -> 'MetaDataBuilder':
        """Add a contributor to the package."""
        if 'contributors' not in self.metadata:
            self.metadata['contributors'] = []
        
        contributor_dict = {'name': name, 'role': role}
        if email:
            contributor_dict['email'] = email
        if organization:
            contributor_dict['organization'] = organization
        
        self.metadata['contributors'].append(contributor_dict)
        return self
    
    def add_source(
        self,
        title: str,
        path: Optional[str] = None,
        description: Optional[str] = None
    ) -> 'MetaDataBuilder':
        """Add a data source to the package."""
        if 'sources' not in self.metadata:
            self.metadata['sources'] = []
        
        source_dict = {'title': title}
        if path:
            source_dict['path'] = path
        if description:
            source_dict['description'] = description
        
        self.metadata['sources'].append(source_dict)
        return self
    
    def add_resource(self, resource: Resource) -> 'MetaDataBuilder':
        """Add a resource to the package."""
        if 'resources' not in self.metadata:
            self.metadata['resources'] = []
        
        self.metadata['resources'].append(resource.to_dict())
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build and return the complete metadata dictionary."""
        return self.metadata.copy()


# Common license templates
COMMON_LICENSES = {
    "CC-BY-4.0": {
        "name": "CC-BY-4.0",
        "title": "Creative Commons Attribution 4.0",
        "path": "https://spdx.org/licenses/CC-BY-4.0.html",
    },
    "MIT": {
        "name": "MIT",
        "title": "MIT License",
        "path": "https://spdx.org/licenses/MIT.html",
    },
    "Apache-2.0": {
        "name": "Apache-2.0",
        "title": "Apache License 2.0",
        "path": "https://spdx.org/licenses/Apache-2.0.html",
    },
    "CC0-1.0": {
        "name": "CC0-1.0",
        "title": "Creative Commons Zero v1.0 Universal",
        "path": "https://spdx.org/licenses/CC0-1.0.html",
    },
}
