# trailpack

[![PyPI](https://img.shields.io/pypi/v/trailpack.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/trailpack.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/trailpack)][pypi status]
[![License](https://img.shields.io/pypi/l/trailpack)][license]

[![Read the documentation at https://trailpaack.readthedocs.io/](https://img.shields.io/readthedocs/trailpack/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/TimoDiepers/trailpack/actions/workflows/python-test.yml/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/TimoDiepers/trailpack/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi status]: https://pypi.org/project/trailpaack/
[read the docs]: https://trailpack.readthedocs.io/
[tests]: https://github.com/TimoDiepers/trailpack/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/TimoDiepers/trailpack
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

## Installation

You can install _trailpack_ via [pip] from [PyPI]:

```console
$ pip install trailpack
```

## Usage

### Web UI

Trailpack includes a Streamlit-based web UI for mapping Excel columns to PyST concepts:

```bash
# Run the UI
streamlit run trailpack/ui/streamlit_app.py
```

Or using the run script:

```bash
python trailpack/ui/run_streamlit.py
```

The UI provides a 3-step workflow with smooth transitions:
1. **Upload File & Select Language**: Upload an Excel file and select language for PyST mapping
2. **Select Sheet**: Choose which sheet to process with data preview
3. **Map Columns**: Map each column to PyST concepts with automatic suggestions and dataframe preview

The view object is stored internally for further processing.

For more details, see [trailpack/ui/README.md](trailpack/ui/README.md).

**Deploying to Streamlit Cloud?** See [STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md) for complete deployment instructions.

### Python API

You can also use trailpack programmatically:

```python
from trailpack.excel import ExcelReader
from trailpack.pyst.api.client import get_suggest_client

# Read Excel structure
reader = ExcelReader("data.xlsx")
sheets = reader.sheets()
columns = reader.columns("Sheet1")

# Get PyST suggestions
client = get_suggest_client()
suggestions = await client.suggest("carbon footprint", "en")
```
## ✨ New: UI-Ready DataPackage Schema Classes

This project now includes comprehensive schema classes for building data package metadata through user interfaces:

### Key Features
- **`DataPackageSchema`**: Defines field types, validation rules, and UI configuration
- **`MetaDataBuilder`**: Fluent interface for creating metadata programmatically
- **Field validation**: Built-in validation for package names, versions, URLs
- **UI integration ready**: Field definitions include labels, placeholders, patterns
- **Standards compliant**: Follows Frictionless Data Package specification

### Quick Example
```python
from trailpack.datapackage_schema import MetaDataBuilder, Resource, Field

# Create metadata with fluent interface
metadata = (MetaDataBuilder()
    .set_basic_info(name="my-dataset", title="My Dataset")
    .add_license("CC-BY-4.0")
    .add_contributor("Your Name", "author")
    .add_resource(Resource(name="data", path="data.parquet"))
    .build())

# Use with existing Packing class
from trailpack.packing import Packing
packer = Packing(df, metadata)
packer.write_parquet("output.parquet")
```

### UI Integration
The schema classes provide everything needed for UI frameworks:
- Field definitions with types, labels, validation patterns
- Enumerated options for dropdowns (licenses, profiles, etc.)
- Built-in validation methods
- Error messages for invalid input

See `examples/datapackage_ui_demo.py` for detailed usage examples.

## 🔍 Validation System

Trailpack includes a comprehensive validation system to ensure data quality and standards compliance:

### Features
- ✅ **Metadata validation**: Required fields, naming conventions, license checking
- ✅ **Data quality checks**: Missing values, duplicates, type consistency
- ✅ **Schema matching**: Validates data types match field definitions
- ✅ **Unit requirements**: All numeric fields must have units (including dimensionless)
- ✅ **Compliance levels**: STRICT, STANDARD, BASIC, or NON-COMPLIANT

### Quick Example
```python
from trailpack.validation import StandardValidator

# Create validator
validator = StandardValidator("1.0.0")

# Validate everything
result = validator.validate_all(
    metadata=metadata_dict,
    df=dataframe,
    schema=schema_dict
)

# Check results
if result.is_valid:
    print(f"{result.level}")  # e.g., "✅ STRICT COMPLIANCE"
else:
    print(result)  # Shows all errors and warnings
```

### Unit Requirements
All numeric fields must specify units, even for dimensionless quantities:
- **Measurements**: Use SI or domain units (kg, m, °C)
- **IDs/Counts**: Use dimensionless unit (`http://qudt.org/vocab/unit/NUM`)
- **Percentages**: Use percent or dimensionless

See [trailpack/validation/README.md](trailpack/validation/README.md) for complete documentation.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide][Contributor Guide].

## License

Distributed under the terms of the [MIT license][License],
_trailpack_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue][Issue Tracker] along with a detailed description.


<!-- github-only -->

[command-line reference]: https://trailpaack.readthedocs.io/en/latest/usage.html
[License]: https://github.com/TimoDiepers/trailpaack/blob/main/LICENSE
[Contributor Guide]: https://github.com/TimoDiepers/trailpaack/blob/main/CONTRIBUTING.md
[Issue Tracker]: https://github.com/TimoDiepers/trailpaack/issues


## Building the Documentation

You can build the documentation locally by installing the documentation Conda environment:

```bash
conda env create -f docs/environment.yml
```

activating the environment

```bash
conda activate sphinx_trailpaack
```

and [running the build command](https://www.sphinx-doc.org/en/master/man/sphinx-build.html#sphinx-build):

```bash
sphinx-build docs _build/html --builder=html --jobs=auto --write-all; open _build/html/index.html
```
