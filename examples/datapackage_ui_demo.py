#!/usr/bin/env python3
"""
Example showing how to use the DataPackageSchema and MetaDataBuilder classes
for interactive UI-driven metadata creation.

This demonstrates how the classes can be integrated with UI frameworks
to collect user input for creating datapackage metadata.
"""

import sys
import os
import json

# Add the trailpack module to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trailpack.packing.datapackage_schema import (
    DataPackageSchema, 
    MetaDataBuilder,
    License,
    Contributor, 
    Source,
    Resource,
    Field,
    FieldConstraints,
    COMMON_LICENSES,
    FIELD_TEMPLATES
)


def simulate_cli_input():
    """Simulate collecting user input via command line interface."""
    
    print("📋 DataPackage Metadata Creator")
    print("=" * 40)
    
    # Initialize schema and builder
    schema = DataPackageSchema()
    builder = MetaDataBuilder()
    
    print("\n🔧 Step 1: Basic Information")
    print("-" * 30)
    
    # Get basic info with validation
    while True:
        name = input("Package name (URL-safe, e.g., 'my-dataset'): ").strip()
        is_valid, error = schema.validate_package_name(name)
        if is_valid:
            break
        print(f"❌ {error}")
    
    title = input("Title (optional): ").strip() or None
    description = input("Description (optional): ").strip() or None
    
    while True:
        version = input("Version (e.g., '1.0.0', optional): ").strip() or None
        if not version:
            break
        is_valid, error = schema.validate_version(version)
        if is_valid:
            break
        print(f"❌ {error}")
    
    # Set basic info
    builder.set_basic_info(name=name, title=title, description=description, version=version)
    
    print(f"\n✅ Basic info set:")
    print(f"  Name: {name}")
    print(f"  Title: {title or 'Not set'}")
    print(f"  Description: {description or 'Not set'}")
    print(f"  Version: {version or 'Not set'}")
    
    print("\n🏷️ Step 2: Optional Metadata")
    print("-" * 30)
    
    # Keywords
    keywords_input = input("Keywords (comma-separated, optional): ").strip()
    if keywords_input:
        keywords = [k.strip() for k in keywords_input.split(",")]
        builder.set_keywords(keywords)
        print(f"  Keywords: {keywords}")
    
    # Profile
    profile = input("Profile (press Enter for 'tabular-data-package'): ").strip() or "tabular-data-package"
    builder.set_profile(profile)
    print(f"  Profile: {profile}")
    
    print("\n👥 Step 3: Contributors")
    print("-" * 30)
    
    while True:
        add_contributor = input("Add a contributor? (y/n): ").strip().lower()
        if add_contributor != 'y':
            break
        
        contrib_name = input("  Contributor name: ").strip()
        contrib_role = input("  Role (author/contributor/maintainer) [author]: ").strip() or "author"
        contrib_email = input("  Email (optional): ").strip() or None
        
        builder.add_contributor(name=contrib_name, role=contrib_role, email=contrib_email)
        print(f"  ✅ Added: {contrib_name} ({contrib_role})")
    
    print("\n📄 Step 4: License")
    print("-" * 30)
    
    print("Common licenses:")
    for key, lic in COMMON_LICENSES.items():
        print(f"  {key}: {lic['title']}")
    
    license_choice = input("Choose license (e.g., 'CC-BY-4.0') or press Enter to skip: ").strip()
    if license_choice and license_choice in COMMON_LICENSES:
        lic = COMMON_LICENSES[license_choice]
        builder.add_license(name=lic["name"], title=lic["title"], path=lic["path"])
        print(f"  ✅ Added license: {lic['title']}")
    elif license_choice:
        builder.add_license(name=license_choice)
        print(f"  ✅ Added custom license: {license_choice}")
    
    print("\n📦 Step 5: Data Resources")
    print("-" * 30)
    
    while True:
        add_resource = input("Add a data resource/file? (y/n): ").strip().lower()
        if add_resource != 'y':
            break
        
        res_name = input("  Resource name: ").strip()
        res_path = input("  File path: ").strip()
        res_description = input("  Description (optional): ").strip() or None
        res_format = input("  Format (csv/parquet/json) [parquet]: ").strip() or "parquet"
        
        # Create simple resource
        resource = Resource(
            name=res_name,
            path=res_path,
            description=res_description,
            format=res_format,
            mediatype="application/octet-stream" if res_format == "parquet" else f"text/{res_format}"
        )
        
        # Add some sample fields
        add_fields = input("  Add field definitions? (y/n): ").strip().lower()
        if add_fields == 'y':
            while True:
                field_name = input("    Field name (or Enter to stop): ").strip()
                if not field_name:
                    break
                
                field_type = input("    Field type (string/number/integer) [string]: ").strip() or "string"
                field_desc = input("    Field description (optional): ").strip() or None
                
                field = Field(name=field_name, type=field_type, description=field_desc)
                resource.fields.append(field)
                print(f"    ✅ Added field: {field_name} ({field_type})")
        
        builder.add_resource(resource)
        print(f"  ✅ Added resource: {res_name}")
        
        if len(builder.resources) == 0:
            print("  ⚠️  At least one resource is required")
    
    if len(builder.resources) == 0:
        print("❌ No resources added. Adding a default resource...")
        default_resource = Resource(
            name="data",
            path="data.parquet",
            description="Default data file",
            format="parquet"
        )
        builder.add_resource(default_resource)
    
    return builder


def demonstrate_ui_field_definitions():
    """Show how UI frameworks can use the field definitions."""
    
    print("\n🖥️  UI Field Definitions Demo")
    print("=" * 40)
    
    schema = DataPackageSchema()
    
    print("Field definitions that can be used to generate UI forms:")
    print()
    
    for field_name in schema.get_required_fields() + schema.get_recommended_fields():
        field_def = schema.get_field_definition(field_name)
        if field_def:
            print(f"📋 {field_def.get('label', field_name)}:")
            print(f"   Type: {field_def.get('type', 'string')}")
            print(f"   Required: {field_def.get('required', False)}")
            print(f"   Description: {field_def.get('description', 'No description')}")
            if 'placeholder' in field_def:
                print(f"   Placeholder: {field_def['placeholder']}")
            if 'pattern' in field_def:
                print(f"   Validation: {field_def['pattern']}")
            if 'options' in field_def:
                options = [opt['label'] for opt in field_def['options']]
                print(f"   Options: {', '.join(options)}")
            print()


def demonstrate_programmatic_creation():
    """Show how to create metadata programmatically."""
    
    print("\n🤖 Programmatic Creation Demo")
    print("=" * 40)
    
    # Create metadata programmatically
    builder = (MetaDataBuilder()
               .set_basic_info(
                   name="sample-astronomical-catalog",
                   title="Sample Astronomical Catalog",
                   description="A demonstration catalog of astronomical sources",
                   version="1.0.0"
               )
               .set_profile("tabular-data-package")
               .set_keywords(["astronomy", "catalog", "coordinates"])
               .add_license("CC-BY-4.0", "Creative Commons Attribution 4.0", 
                           "https://creativecommons.org/licenses/by/4.0/")
               .add_contributor("Jane Astronomer", "author", "jane@observatory.org")
               .add_source("Hubble Space Telescope", "https://hubblesite.org"))
    
    # Create a resource with astronomical fields
    astro_resource = Resource(
        name="sources",
        path="astronomical_sources.parquet",
        description="Catalog of astronomical sources with coordinates",
        format="parquet",
        mediatype="application/octet-stream"
    )
    
    # Add astronomical fields
    astro_resource.fields = [
        Field(
            name="source_id", 
            type="integer",
            description="Unique source identifier",
            constraints=FieldConstraints(required=True, unique=True)
        ),
        Field(
            name="ra",
            type="number", 
            description="Right Ascension (J2000)",
            unit="deg",
            unit_code="http://qudt.org/vocab/unit/DEG",
            ucd="pos.eq.ra;meta.main",
            constraints=FieldConstraints(minimum=0.0, maximum=360.0)
        ),
        Field(
            name="dec",
            type="number",
            description="Declination (J2000)", 
            unit="deg",
            unit_code="http://qudt.org/vocab/unit/DEG",
            ucd="pos.eq.dec;meta.main",
            constraints=FieldConstraints(minimum=-90.0, maximum=90.0)
        ),
        Field(
            name="magnitude",
            type="number",
            description="Apparent V magnitude",
            unit="mag",
            unit_code="http://qudt.org/vocab/unit/MAG",
            ucd="phot.mag;em.opt.V"
        )
    ]
    
    astro_resource.primary_key = ["source_id"]
    
    builder.add_resource(astro_resource)
    
    # Build the metadata
    metadata = builder.build()
    
    print("Generated metadata:")
    print(json.dumps(metadata, indent=2))
    
    return metadata


def main():
    """Main demonstration function."""
    
    print("🚀 DataPackage Schema Classes Demo")
    print("=" * 50)
    
    # Show UI field definitions
    demonstrate_ui_field_definitions()
    
    # Show programmatic creation
    programmatic_metadata = demonstrate_programmatic_creation()
    
    # Simulate interactive input
    print("\n" + "="*50)
    print("💬 Interactive CLI Simulation")
    print("(This shows how a UI could collect the same information)")
    print("="*50)
    
    # For demo, we'll skip actual input and show structure
    print("In a real UI implementation, you would:")
    print("1. Generate form fields using schema.get_field_definition()")
    print("2. Collect user input through the UI")
    print("3. Validate input using schema validation methods")
    print("4. Build metadata using MetaDataBuilder methods")
    print("5. Export final JSON using builder.build()")
    
    # Show builder state
    builder = MetaDataBuilder()
    print(f"\n📊 Available UI field types:")
    for field_name, field_def in builder.get_ui_fields().items():
        print(f"  • {field_name}: {field_def.get('type', 'string')} ({'required' if field_def.get('required') else 'optional'})")
    
    print(f"\n🎯 Integration Points for UI Frameworks:")
    print(f"  • schema.get_field_definition() - Get field UI configuration")
    print(f"  • schema.validate_*() methods - Validate user input")
    print(f"  • builder.set_*() methods - Set metadata values") 
    print(f"  • builder.build() - Generate final JSON")
    print(f"  • COMMON_LICENSES - Predefined license options")
    print(f"  • FIELD_TEMPLATES - Common field patterns")


if __name__ == "__main__":
    main()