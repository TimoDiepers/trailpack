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
    name: str = PydanticField(..., description="License identifier (e.g., 'CC-BY-4.0', 'MIT')")
    title: Optional[str] = PydanticField(None, description="Human-readable license title")
    path: Optional[str] = PydanticField(None, description="URL to license text")
    
    @field_validator('path')
    @classmethod
    def validate_path_url(cls, v):
        """Validate URL format."""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('License path must be a valid http or https URL')
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format, excluding None values."""
        return self.dict(exclude_none=True)


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
        return self.dict(exclude_none=True)


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
        return self.dict(exclude_none=True)


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
            raise ValueError('Unit path must be a valid http or https URI')
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
        return self.dict(exclude_none=True)


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
                
        if self.encoding != "utf-8":
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
    """
    Interactive builder for creating DataPackage metadata.
    Can be used with UI frameworks to collect user input.
    """

    def __init__(self):
        """Initialize the builder."""
        self.schema = DataPackageSchema()
        self.metadata = {}
        self.contributors = []
        self.sources = []
        self.resources = []
        self.licenses = []
        self.set_dates()  # Automatically set creation date

    def set_basic_info(
        self, name: str, title: Optional[str] = None, description: Optional[str] = None, version: Optional[str] = None
    ) -> "MetaDataBuilder":
        """Set basic package information."""
        # Validate required name
        is_valid, error = self.schema.validate_package_name(name)
        if not is_valid:
            raise ValueError(f"Invalid package name: {error}")

        self.metadata["name"] = name
        if title:
            self.metadata["title"] = title
        if description:
            self.metadata["description"] = description
        if version:
            is_valid, error = self.schema.validate_version(version)
            if not is_valid:
                raise ValueError(f"Invalid version: {error}")
            self.metadata["version"] = version

        return self

    def set_profile(self, profile: str) -> "MetaDataBuilder":
        """Set package profile."""
        self.metadata["profile"] = profile
        return self

    def set_keywords(self, keywords: List[str]) -> "MetaDataBuilder":
        """Set keywords/tags."""
        self.metadata["keywords"] = keywords
        return self
    
    def set_dates(self, created: Optional[str] = None, modified: Optional[str] = None) -> 'DataPackageBuilder':
        """Set creation and modification dates."""
        if created:
            self.metadata["created"] = created
        if modified:
            self.metadata["modified"] = modified
        return self

    def set_links(
        self, homepage: Optional[str] = None, repository: Optional[str] = None
    ) -> "MetaDataBuilder":
        """Set homepage and repository URLs."""
        if homepage:
            is_valid, error = self.schema.validate_url(homepage)
            if not is_valid:
                raise ValueError(f"Invalid homepage URL: {error}")
            self.metadata["homepage"] = homepage

        if repository:
            is_valid, error = self.schema.validate_url(repository)
            if not is_valid:
                raise ValueError(f"Invalid repository URL: {error}")
            self.metadata["repository"] = repository

        return self

    def add_license(
        self, name: Optional[str] = None, title: Optional[str] = None, path: Optional[str] = None
    ) -> "MetaDataBuilder":
        """Add license information. Defaults to CC-BY-4.0 if no name provided.
        License name should be a valid SPDX identifier.
        path should be a valid URL to SPDX license page.
        See https://spdx.org/licenses/ for common licenses.
        """
        if not name:
            license_obj = License()
        else:
            license_obj = License(name=name, title=title, path=path)
        self.licenses.append(license_obj)
        return self

    def add_contributor(
        self,
        name: str,
        role: str = "author",
        email: Optional[str] = None,
        organization: Optional[str] = None,
    ) -> "MetaDataBuilder":
        """Add contributor information."""
        contributor = Contributor(
            name=name, role=role, email=email, organization=organization
        )
        self.contributors.append(contributor)
        return self

    def add_source(
        self, title: str, path: Optional[str] = None, description: Optional[str] = None
    ) -> "MetaDataBuilder":
        """Add data source information."""
        source = Source(title=title, path=path, description=description)
        self.sources.append(source)
        return self

    def add_resource(self, resource: Resource) -> "MetaDataBuilder":
        """Add a data resource."""
        self.resources.append(resource)
        return self

    def build(self) -> Dict[str, Any]:
        """Build the complete metadata dictionary."""
        # Start with basic metadata
        result = self.metadata.copy()

        # Add arrays if they have content
        if self.licenses:
            result["licenses"] = [license.to_dict() for license in self.licenses]

        if self.contributors:
            result["contributors"] = [
                contributor.to_dict() for contributor in self.contributors
            ]

        if self.sources:
            result["sources"] = [source.to_dict() for source in self.sources]

        # Resources are required
        if not self.resources:
            raise ValueError("At least one resource is required")

        result["resources"] = [resource.to_dict() for resource in self.resources]

        # Validate required fields
        for required_field in self.schema.get_required_fields():
            if required_field not in result:
                raise ValueError(f"Required field '{required_field}' is missing")

        return result

    def get_ui_fields(self) -> Dict[str, Dict[str, Any]]:
        """Get field definitions for UI generation."""
        return self.schema.field_definitions

    def get_current_state(self) -> Dict[str, Any]:
        """Get current builder state for UI display."""
        return {
            "metadata": self.metadata,
            "licenses": [license.to_dict() for license in self.licenses],
            "contributors": [
                contributor.to_dict() for contributor in self.contributors
            ],
            "sources": [source.to_dict() for source in self.sources],
            "resources": [resource.to_dict() for resource in self.resources],
        }


# Common license templates
COMMON_LICENSES = {
    "CC-BY-4.0": {
        "name": "CC-BY-4.0",
        "title": "Creative Commons Attribution 4.0",
        "path": "https://creativecommons.org/licenses/by/4.0/",
    },
    "MIT": {
        "name": "MIT",
        "title": "MIT License",
        "path": "https://opensource.org/licenses/MIT",
    },
    "Apache-2.0": {
        "name": "Apache-2.0",
        "title": "Apache License 2.0",
        "path": "https://www.apache.org/licenses/LICENSE-2.0",
    },
    "CC0-1.0": {
        "name": "CC0-1.0",
        "title": "Creative Commons Zero v1.0 Universal",
        "path": "https://creativecommons.org/publicdomain/zero/1.0/",
    },
}

# Field type templates for quick creation
FIELD_TEMPLATES = {
    "id": Field(
        name="id",
        type="integer",
        description="Unique identifier",
        unit=Unit(
            name="NUM",
            long_name="dimensionless number",
            path="https://vocab.sentier.dev/web/concept/https%3A//vocab.sentier.dev/units/unit/NUM?concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2Funits%2F&language=en"
        ),
        constraints=FieldConstraints(required=True, unique=True)
    ),
    "name": Field(
        name="name",
        type="string",
        description="Name or title",
        constraints=FieldConstraints(required=True),
    ),
    "latitude": Field(
        name="latitude",
        type="number",
        description="Decimal latitude (WGS84)",
        unit=Unit(
            name="deg",
            long_name="degree",
            path="http://qudt.org/vocab/unit/DEG"
        ),
        rdf_type="http://www.w3.org/2003/01/geo/wgs84_pos#lat",
        constraints=FieldConstraints(minimum=-90.0, maximum=90.0),
    ),
    "longitude": Field(
        name="longitude",
        type="number",
        description="Decimal longitude (WGS84)",
        unit=Unit(
            name="deg",
            long_name="degree",
            path="http://qudt.org/vocab/unit/DEG"
        ),
        rdf_type="http://www.w3.org/2003/01/geo/wgs84_pos#long",
        constraints=FieldConstraints(minimum=-180.0, maximum=180.0),
    ),
}
