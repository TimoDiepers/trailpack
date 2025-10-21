# Packing Integration - DataPackage Metadata in Parquet

## Overview

The Trailpack React UI now fully integrates the **Packing** class to embed Frictionless DataPackage metadata directly into Parquet files. This follows the Trailpack standard for data packaging and ensures metadata travels with the data.

## Architecture

### Backend Components

#### 1. Packing Class (`backend/app/packing/packing.py`)

The core class for writing and reading DataFrames with embedded metadata:

```python
from app.packing.packing import Packing

# Create instance with data and metadata
packer = Packing(data=df, meta_data=metadata_dict)

# Write to file
packer.write_parquet("output.parquet")

# Or get bytes
parquet_bytes = packer.write_parquet_to_bytes()

# Read back
df, metadata = read_parquet("output.parquet")
```

**Features:**
- ✅ Embeds JSON metadata in Parquet file using PyArrow schema metadata
- ✅ Supports both file and bytes output
- ✅ Validates input types (DataFrame and dict)
- ✅ Auto-creates directories if needed
- ✅ Preserves all metadata when reading back

#### 2. DataPackageExporter (`backend/app/services/datapackage_export_service.py`)

High-level service that builds complete Frictionless DataPackage metadata:

```python
from app.services.datapackage_export_service import DataPackageExporter

exporter = DataPackageExporter(
    df=dataframe,
    mappings=column_mappings,
    general_details=metadata,
    sheet_name="Sheet1",
    file_name="data.xlsx"
)

# Export to bytes
parquet_bytes, metadata, quality_level = exporter.export_to_bytes()

# Or export to file
path, metadata, quality_level = exporter.export_to_file("output.parquet")
```

**What it does:**
1. **Validates** input data and metadata
2. **Builds Field definitions** from column mappings
   - Infers types (integer, number, string, boolean, datetime)
   - Includes ontology mappings (rdf_type, taxonomy_url)
   - Adds units for numeric fields
   - Includes descriptions
3. **Creates Resource** definition with field schema
4. **Builds complete metadata** using MetaDataBuilder
   - Basic info (name, title, description, version)
   - Licenses, contributors, sources
   - Keywords, homepage, repository
   - Created/modified timestamps
5. **Validates DataFrame** for Parquet compatibility
   - Checks for mixed types in columns
   - Provides detailed error messages
6. **Uses Packing class** to embed metadata and write Parquet

#### 3. MetaDataBuilder (`backend/app/packing/datapackage_schema.py`)

Fluent builder for constructing metadata incrementally:

```python
from app.packing.datapackage_schema import MetaDataBuilder

builder = MetaDataBuilder()
builder.set_basic_info(name="my-dataset", title="My Dataset")
builder.add_license(name="CC-BY-4.0", path="https://...")
builder.add_contributor(name="John Doe", role="author")
builder.add_resource(resource)
metadata = builder.build()
```

**Methods:**
- `set_basic_info()` - name, title, description, version
- `set_profile()` - data package profile
- `set_keywords()` - keyword list
- `set_links()` - homepage, repository
- `add_license()` - license information
- `add_contributor()` - contributor with role
- `add_source()` - data source
- `add_resource()` - data resource with schema
- `build()` - get final metadata dict

### Export Endpoints

#### POST `/api/export/parquet`

Export mapped data to Parquet with embedded metadata.

**Request:**
```json
{
  "fileId": "abc123",
  "sheetName": "Sheet1",
  "mappings": [...],
  "generalDetails": {...},
  "config": {
    "includeMetadata": true,
    "compressionType": "snappy",
    "outputFileName": "output.parquet"
  }
}
```

**Response:**
- Binary Parquet file with embedded DataPackage metadata
- Headers:
  - `Content-Disposition: attachment; filename=output.parquet`
  - `X-Quality-Level: VALID|WARNING|ERROR`

**Process:**
1. Retrieves Excel data from session storage
2. Gets specified sheet DataFrame
3. Creates DataPackageExporter instance
4. Builds complete metadata from mappings + general details
5. Uses Packing class to embed metadata
6. Returns Parquet bytes

#### POST `/api/export/metadata`

Export only the DataPackage metadata as JSON.

**Response:**
- JSON file with complete datapackage.json structure
- Useful for preview or separate download

#### POST `/api/export/config`

Export the mapping configuration as JSON.

**Response:**
- JSON file with mappings, general details, and export config
- Can be used to reload configuration later

### Frontend Integration

#### API Service (`src/services/api.ts`)

```typescript
import api from './services/api';

// Export to Parquet with metadata
const parquetBlob = await api.exportToParquet({
  fileId: wizardState.fileId,
  sheetName: wizardState.selectedSheet,
  mappings: wizardState.mappings,
  generalDetails: wizardState.generalDetails,
  config: {
    includeMetadata: true,
    compressionType: 'snappy',
    outputFileName: 'my-data.parquet'
  }
});

// Download
const url = URL.createObjectURL(parquetBlob);
const a = document.createElement('a');
a.href = url;
a.download = 'my-data.parquet';
a.click();

// Export metadata only
const metadataBlob = await api.exportMetadata({...});

// Export config
const configBlob = await api.exportConfig({...});
```

## Data Flow

```
Excel File Upload
       ↓
Excel Service (extract data)
       ↓
User Mapping (ontology + units + descriptions)
       ↓
General Details Form (licenses, contributors, sources)
       ↓
Validation Step
       ↓
Export Request
       ↓
DataPackageExporter
  ├─ Build Fields (from mappings)
  ├─ Build Resource (with schema)
  ├─ Build Metadata (using MetaDataBuilder)
  └─ Packing Class
         ↓
    Parquet + Metadata
```

## Metadata Structure

The embedded metadata follows Frictionless Data Package standard:

```json
{
  "name": "my-dataset",
  "title": "My Dataset Title",
  "description": "Dataset description",
  "version": "1.0.0",
  "profile": "tabular-data-package",
  "keywords": ["energy", "sustainability"],
  "homepage": "https://example.com",
  "repository": "https://github.com/user/repo",
  "created": "2025-10-17",
  "modified": "2025-10-17",
  "licenses": [
    {
      "name": "CC-BY-4.0",
      "title": "Creative Commons Attribution 4.0",
      "path": "https://spdx.org/licenses/CC-BY-4.0.html"
    }
  ],
  "contributors": [
    {
      "name": "John Doe",
      "role": "author",
      "email": "john@example.com",
      "organization": "Example Org"
    }
  ],
  "sources": [
    {
      "title": "Original Data Source",
      "path": "https://example.com/data",
      "description": "Source description"
    }
  ],
  "resources": [
    {
      "name": "data_sheet1",
      "path": "data_sheet1.parquet",
      "title": "Data from Sheet1",
      "format": "parquet",
      "mediatype": "application/vnd.apache.parquet",
      "encoding": "utf-8",
      "profile": "tabular-data-resource",
      "schema": {
        "fields": [
          {
            "name": "temperature",
            "type": "number",
            "description": "Temperature measurement",
            "unit": {
              "name": "CEL",
              "long_name": "degree Celsius",
              "path": "https://vocab.sentier.dev/units/unit/CEL"
            },
            "rdfType": "https://vocab.sentier.dev/concepts/temperature",
            "taxonomyUrl": "https://vocab.sentier.dev/concepts/temperature"
          },
          {
            "name": "location",
            "type": "string",
            "description": "Measurement location"
          }
        ]
      }
    }
  ]
}
```

## Field Schema Details

Each field includes:

- **name**: Column name
- **type**: Data type (integer, number, string, boolean, datetime)
- **description**: User-provided or default description
- **unit** (numeric fields):
  - `name`: Unit symbol (e.g., "CEL", "M")
  - `long_name`: Full unit name
  - `path`: PyST unit concept IRI
- **rdfType**: PyST ontology concept IRI (if mapped)
- **taxonomyUrl**: Same as rdfType (for compatibility)

## Validation & Quality

The DataPackageExporter validates:

1. ✅ **DataFrame not empty**
2. ✅ **Package name required** and valid format
3. ✅ **No mixed types** in columns (would break Parquet)
4. ✅ **Units for numeric fields** (defaults to dimensionless if missing)
5. ✅ **Ontology OR description** for all columns

Quality levels (future integration with StandardValidator):
- **VALID**: No errors, no warnings
- **WARNING**: No errors, some warnings
- **ERROR**: Has errors (blocks export)

## Dependencies

```bash
# Python packages required
pip install pandas pyarrow pydantic fastapi
```

**Already in `requirements.txt`:**
- pandas>=2.2.3
- pyarrow (add if missing)

## Usage Example (Complete Flow)

### Backend (Export Router)

```python
# 1. User uploads Excel → stored in session
# 2. User maps columns → creates ColumnMapping list
# 3. User fills metadata → creates GeneralDetails
# 4. User clicks Export

# Export router receives:
request = ExportRequest(
    fileId="abc123",
    sheetName="Sheet1",
    mappings=[...],
    generalDetails=GeneralDetails(...),
    config=ExportConfig(...)
)

# 5. Retrieve data
excel_data = excel_service.get_cached_file(request.fileId)
df = pd.DataFrame(excel_data['sheets'][request.sheetName]['data'])

# 6. Create exporter
exporter = DataPackageExporter(
    df=df,
    mappings=request.mappings,
    general_details=request.generalDetails,
    sheet_name=request.sheetName,
    file_name=excel_data['fileName']
)

# 7. Export
parquet_bytes, metadata, quality_level = exporter.export_to_bytes()

# 8. Return
return Response(
    content=parquet_bytes,
    headers={"Content-Disposition": "attachment; filename=data.parquet"}
)
```

### Frontend (ExportStep)

```typescript
const handleExport = async () => {
  try {
    // Call export endpoint
    const blob = await api.exportToParquet({
      fileId: wizardState.fileId,
      sheetName: wizardState.selectedSheet,
      mappings: wizardState.mappings,
      generalDetails: wizardState.generalDetails,
      config: {
        includeMetadata: true,
        compressionType: 'snappy',
        outputFileName: 'dataset.parquet'
      }
    });

    // Download
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'dataset.parquet';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    // Also download metadata separately
    const metadataBlob = await api.exportMetadata({...});
    // ... download metadata.json

    // And mapping config
    const configBlob = await api.exportConfig({...});
    // ... download config.json

  } catch (error) {
    console.error('Export failed:', error);
  }
};
```

## Reading Packed Parquet Files

To read a Parquet file with embedded metadata:

```python
from app.packing.packing import read_parquet

# Read file
df, metadata = read_parquet("dataset.parquet")

# Access data
print(df.head())

# Access metadata
print(metadata['title'])
print(metadata['licenses'])
print(metadata['resources'][0]['schema']['fields'])
```

## Benefits

1. **Metadata travels with data** - No separate files needed
2. **Trailpack standard compliance** - Follows v1.0.0 specification
3. **Frictionless compatibility** - Standard DataPackage format
4. **Complete provenance** - Licenses, contributors, sources included
5. **Ontology integration** - PyST concepts embedded in field schema
6. **Unit information** - Physical units preserved for numeric fields
7. **Self-documenting** - Descriptions and context in the file
8. **Quality assurance** - Validation ensures data integrity

## Testing

To test the integration:

```bash
# 1. Start backend
cd backend
conda run -n hackathon uvicorn app.main:app --reload

# 2. Upload Excel file
# 3. Map columns to ontology + units
# 4. Fill general details form
# 5. Validate
# 6. Export to Parquet

# 7. Read back in Python
from app.packing.packing import read_parquet
df, meta = read_parquet("output.parquet")
print(meta['resources'][0]['schema']['fields'])
```

## Next Steps

1. ✅ Packing class implemented
2. ✅ DataPackageExporter service created
3. ✅ MetaDataBuilder added to schema
4. ✅ Export router updated with 3 endpoints
5. ✅ Frontend API service extended
6. ⏳ Update ExportStep UI to use new endpoints
7. ⏳ Add StandardValidator integration for quality levels
8. ⏳ Test complete workflow
9. ⏳ Add progress indicators during export
10. ⏳ Handle large file exports (streaming)

---

**Status**: Backend Integration Complete ✅  
**Frontend**: Needs ExportStep UI updates  
**Testing**: Ready for end-to-end testing
