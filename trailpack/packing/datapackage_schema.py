"""
DataPackage metadata schema and interactive builder classes.
Provides structured definitions and UI-friendly methods for creating
Frictionless Data Package metadata.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import re
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


@dataclass
class License:
    """License information."""
    name: str
    title: Optional[str] = None
    path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {"name": self.name}
        if self.title:
            result["title"] = self.title
        if self.path:
            result["path"] = self.path
        return result


@dataclass
class Contributor:
    """Contributor information."""
    name: str
    role: str = "author"
    email: Optional[str] = None
    organization: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {"name": self.name, "role": self.role}
        if self.email:
            result["email"] = self.email
        if self.organization:
            result["organization"] = self.organization
        return result


@dataclass
class Source:
    """Data source information."""
    title: str
    path: Optional[str] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {"title": self.title}
        if self.path:
            result["path"] = self.path
        if self.description:
            result["description"] = self.description
        return result


@dataclass
class FieldConstraints:
    """Field validation constraints."""
    required: Optional[bool] = None
    unique: Optional[bool] = None
    minimum: Optional[Union[int, float]] = None
    maximum: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    enum: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                result[key] = value
        return result


@dataclass
class Field:
    """Data field schema definition."""
    name: str
    type: str
    description: Optional[str] = None
    unit: Optional[str] = None
    unit_code: Optional[str] = None
    rdf_type: Optional[str] = None
    taxonomy_url: Optional[str] = None
    constraints: Optional[FieldConstraints] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {"name": self.name, "type": self.type}
        
        if self.description:
            result["description"] = self.description
        if self.unit:
            result["unit"] = self.unit
        if self.unit_code:
            result["unitCode"] = self.unit_code
        if self.rdf_type:
            result["rdfType"] = self.rdf_type
        if self.taxonomy_url:
            result["taxonomyUrl"] = self.taxonomy_url
        if self.constraints:
            constraints_dict = self.constraints.to_dict()
            if constraints_dict:
                result["constraints"] = constraints_dict
        
        return result


@dataclass
class Resource:
    """Data resource (file) definition."""
    name: str
    path: str
    title: Optional[str] = None
    description: Optional[str] = None
    format: Optional[str] = None
    mediatype: Optional[str] = None
    encoding: str = "utf-8"
    profile: Optional[str] = None
    fields: List[Field] = field(default_factory=list)
    primary_key: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {"name": self.name, "path": self.path}
        
        if self.title:
            result["title"] = self.title
        if self.description:
            result["description"] = self.description
        if self.format:
            result["format"] = self.format
        if self.mediatype:
            result["mediatype"] = self.mediatype
        if self.encoding != "utf-8":
            result["encoding"] = self.encoding
        if self.profile:
            result["profile"] = self.profile
        
        if self.fields:
            schema = {
                "fields": [field.to_dict() for field in self.fields]
            }
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
    REQUIRED_FIELDS = ["name", "resources"]
    
    # Recommended fields  
    RECOMMENDED_FIELDS = ["title", "description", "version", "licenses"]
    
    # Optional fields
    OPTIONAL_FIELDS = [
        "profile", "contributors", "sources", "keywords", "created", "modified",
        "homepage", "repository", "image", "id"
    ]
    
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
                "help": "Use lowercase letters, numbers, hyphens, and dots only"
            },
            "title": {
                "type": "string", 
                "required": False,
                "label": "Title",
                "description": "Human-readable title for the dataset",
                "placeholder": "My Dataset Title"
            },
            "description": {
                "type": "text",
                "required": False,
                "label": "Description", 
                "description": "Longer description explaining what the dataset contains",
                "placeholder": "This dataset contains..."
            },
            "version": {
                "type": "string",
                "required": False,
                "label": "Version",
                "description": "Version number using semantic versioning",
                "placeholder": "1.0.0",
                "pattern": r"^\d+\.\d+\.\d+(-[a-zA-Z0-9\-\.]+)?$"
            },
            "profile": {
                "type": "select",
                "required": False,
                "label": "Profile",
                "description": "Type of data package",
                "options": [
                    {"value": "tabular-data-package", "label": "Tabular Data Package"},
                    {"value": "data-package", "label": "Data Package"},
                    {"value": "fiscal-data-package", "label": "Fiscal Data Package"}
                ],
                "default": "tabular-data-package"
            },
            "keywords": {
                "type": "tags",
                "required": False,
                "label": "Keywords",
                "description": "Tags to help others discover your dataset",
                "placeholder": "astronomy, catalog, coordinates"
            },
            "homepage": {
                "type": "url",
                "required": False,
                "label": "Homepage",
                "description": "Project or dataset homepage URL",
                "placeholder": "https://example.com/my-project"
            },
            "repository": {
                "type": "url", 
                "required": False,
                "label": "Repository",
                "description": "Code repository URL",
                "placeholder": "https://github.com/user/repo"
            },
            "created": {
                "type": "date",
                "required": False,
                "label": "Created Date",
                "description": "When the dataset was created",
                "default": datetime.now().isoformat()[:10]
            },
            "modified": {
                "type": "date",
                "required": False, 
                "label": "Modified Date",
                "description": "When the dataset was last modified"
            }
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
            return False, "Package name can only contain lowercase letters, numbers, hyphens, underscores, and dots"
        
        if name.startswith('.') or name.endswith('.'):
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


class DataPackageBuilder:
    """
    Interactive builder for creating DataPackage metadata.
    Can be used with UI frameworks to collect user input.
    """
    
    def __init__(self):
        """Initialize the builder."""
        self.schema = DataPackageSchema()
        self.metadata = {}
        self.licenses = []
        self.contributors = []
        self.sources = []
        self.resources = []
    
    def set_basic_info(self, name: str, title: str = None, description: str = None, 
                      version: str = None) -> 'DataPackageBuilder':
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
    
    def set_profile(self, profile: str) -> 'DataPackageBuilder':
        """Set package profile."""
        self.metadata["profile"] = profile
        return self
    
    def set_keywords(self, keywords: List[str]) -> 'DataPackageBuilder':
        """Set keywords/tags."""
        self.metadata["keywords"] = keywords
        return self
    
    def set_dates(self, created: str = None, modified: str = None) -> 'DataPackageBuilder':
        """Set creation and modification dates."""
        if created:
            self.metadata["created"] = created
        if modified:
            self.metadata["modified"] = modified
        return self
    
    def set_links(self, homepage: str = None, repository: str = None) -> 'DataPackageBuilder':
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
    
    def add_license(self, name: str, title: str = None, path: str = None) -> 'DataPackageBuilder':
        """Add license information."""
        license_obj = License(name=name, title=title, path=path)
        self.licenses.append(license_obj)
        return self
    
    def add_contributor(self, name: str, role: str = "author", email: str = None, 
                       organization: str = None) -> 'DataPackageBuilder':
        """Add contributor information."""
        contributor = Contributor(name=name, role=role, email=email, organization=organization)
        self.contributors.append(contributor)
        return self
    
    def add_source(self, title: str, path: str = None, description: str = None) -> 'DataPackageBuilder':
        """Add data source information."""
        source = Source(title=title, path=path, description=description)
        self.sources.append(source)
        return self
    
    def add_resource(self, resource: Resource) -> 'DataPackageBuilder':
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
            result["contributors"] = [contributor.to_dict() for contributor in self.contributors]
        
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
            "contributors": [contributor.to_dict() for contributor in self.contributors], 
            "sources": [source.to_dict() for source in self.sources],
            "resources": [resource.to_dict() for resource in self.resources]
        }


# Common license templates
COMMON_LICENSES = {
    "CC-BY-4.0": {
        "name": "CC-BY-4.0",
        "title": "Creative Commons Attribution 4.0",
        "path": "https://creativecommons.org/licenses/by/4.0/"
    },
    "MIT": {
        "name": "MIT", 
        "title": "MIT License",
        "path": "https://opensource.org/licenses/MIT"
    },
    "Apache-2.0": {
        "name": "Apache-2.0",
        "title": "Apache License 2.0", 
        "path": "https://www.apache.org/licenses/LICENSE-2.0"
    },
    "CC0-1.0": {
        "name": "CC0-1.0",
        "title": "Creative Commons Zero v1.0 Universal",
        "path": "https://creativecommons.org/publicdomain/zero/1.0/"
    }
}

# Field type templates for quick creation
FIELD_TEMPLATES = {
    "id": Field(
        name="id", 
        type="integer",
        description="Unique identifier",
        constraints=FieldConstraints(required=True, unique=True)
    ),
    "name": Field(
        name="name",
        type="string", 
        description="Name or title",
        constraints=FieldConstraints(required=True)
    ),
    "latitude": Field(
        name="latitude",
        type="number",
        description="Decimal latitude (WGS84)",
        unit="deg",
        unit_code="http://qudt.org/vocab/unit/DEG",
        rdf_type="http://www.w3.org/2003/01/geo/wgs84_pos#lat",
        constraints=FieldConstraints(minimum=-90.0, maximum=90.0)
    ),
    "longitude": Field(
        name="longitude", 
        type="number",
        description="Decimal longitude (WGS84)",
        unit="deg",
        unit_code="http://qudt.org/vocab/unit/DEG", 
        rdf_type="http://www.w3.org/2003/01/geo/wgs84_pos#long",
        constraints=FieldConstraints(minimum=-180.0, maximum=180.0)
    )
}