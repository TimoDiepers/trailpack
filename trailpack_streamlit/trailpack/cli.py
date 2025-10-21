"""Command-line interface for Trailpack.

Provides commands for data processing, validation, and project management.
"""

from pathlib import Path
from typing import Optional
import sys

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

# Create Typer app
app = typer.Typer(
    name="trailpack",
    help="Trailpack - Dataset standardization tool for LCA and sustainability data",
    add_completion=False,
)

# Rich console for pretty output
console = Console()


@app.command()
def ui(
    port: int = typer.Option(8501, "--port", "-p", help="Port to run Streamlit on"),
    host: str = typer.Option("localhost", "--host", help="Host to bind to"),
):
    """
    Launch the Streamlit UI for interactive data mapping.

    Opens a browser at localhost:8501 with the full interactive interface
    for mapping columns to ontologies and exporting data packages.

    Example:
        trailpack ui
        trailpack ui --port 8080
    """
    import subprocess
    from pathlib import Path

    # Get the path to streamlit_app.py
    app_path = Path(__file__).parent / "ui" / "streamlit_app.py"

    if not app_path.exists():
        console.print(f"[red]Error: Could not find streamlit_app.py at {app_path}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Starting Streamlit UI on {host}:{port}...[/green]")

    try:
        subprocess.run(
            [
                "streamlit",
                "run",
                str(app_path),
                f"--server.port={port}",
                f"--server.address={host}",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error launching Streamlit: {e}[/red]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Streamlit UI stopped[/yellow]")


@app.command()
def process(
    data: Path = typer.Option(..., "--data", "-d", help="Path to data file (Excel, CSV)"),
    sheet: str = typer.Option(None, "--sheet", "-s", help="Sheet name (for Excel files)"),
    mapping: Path = typer.Option(..., "--mapping", "-m", help="Path to mapping config JSON"),
    metadata: Path = typer.Option(..., "--metadata", "-M", help="Path to metadata config JSON"),
    output: Path = typer.Option(..., "--output", "-o", help="Output Parquet file path"),
    validate_standard: bool = typer.Option(True, "--validate/--no-validate", help="Validate against Trailpack standard"),
):
    """
    Process data file with configs to create a Frictionless Data Package.

    Reads data, applies column mappings, validates against standard,
    and exports to Parquet format with embedded metadata.

    Example:
        trailpack process \\
            --data inventory.xlsx \\
            --sheet "Sheet1" \\
            --mapping mapping.json \\
            --metadata metadata.json \\
            --output clean-data.parquet
    """
    from trailpack.io.smart_reader import SmartDataReader
    from trailpack.config import load_configs, extract_column_mappings, extract_general_details
    from trailpack.packing.export_service import DataPackageExporter

    console.print(Panel.fit(
        "[bold cyan]Trailpack Process[/bold cyan]\n"
        f"Data: {data}\n"
        f"Sheet: {sheet or 'N/A'}\n"
        f"Mapping: {mapping}\n"
        f"Metadata: {metadata}\n"
        f"Output: {output}",
        title="Configuration"
    ))

    try:
        # 1. Validate inputs
        if not data.exists():
            console.print(f"[red]Error: Data file not found: {data}[/red]")
            raise typer.Exit(1)

        # 2. Load configs
        console.print("[cyan]Loading configurations...[/cyan]")
        mapping_config, metadata_config = load_configs(
            mapping_path=mapping,
            metadata_path=metadata
        )

        # 3. Read data with SmartDataReader
        console.print(f"[cyan]Reading data file with SmartDataReader...[/cyan]")
        reader = SmartDataReader(data)
        console.print(f"  Engine: {reader.engine}")
        console.print(f"  Estimated memory: {reader.estimate_memory()}")

        df = reader.read(sheet_name=sheet)
        console.print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")

        # 4. Extract mappings and metadata
        column_mappings = extract_column_mappings(mapping_config)
        general_details = extract_general_details(metadata_config)

        console.print(f"[cyan]Applying {len(column_mappings)} column mappings...[/cyan]")

        # 5. Create exporter and export
        console.print("[cyan]Creating data package...[/cyan]")
        exporter = DataPackageExporter(
            dataframe=df,
            column_mappings=column_mappings,
            general_details=general_details,
            language="en"
        )

        output_path, quality_level, validation_result = exporter.export(
            str(output),
            validate_standard=validate_standard
        )

        # 6. Display results
        console.print(f"[green]✓ Data package created: {output_path}[/green]")

        if quality_level:
            quality_colors = {
                "STRICT": "green",
                "STANDARD": "cyan",
                "BASIC": "yellow",
                "INVALID": "red"
            }
            color = quality_colors.get(quality_level, "white")
            console.print(f"  Quality Level: [{color}]{quality_level}[/{color}]")

        if validation_result:
            if validation_result.errors:
                console.print(f"  [red]Errors: {len(validation_result.errors)}[/red]")
            if validation_result.warnings:
                console.print(f"  [yellow]Warnings: {len(validation_result.warnings)}[/yellow]")
            if validation_result.info:
                console.print(f"  [cyan]Info: {len(validation_result.info)}[/cyan]")

        console.print("[green]✓ Process completed successfully[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def validate(
    data: Path = typer.Option(..., "--data", "-d", help="Path to data file (Excel, CSV)"),
    sheet: str = typer.Option(None, "--sheet", "-s", help="Sheet name (for Excel files)"),
    mapping: Path = typer.Option(..., "--mapping", "-m", help="Path to mapping config JSON"),
    metadata: Path = typer.Option(..., "--metadata", "-M", help="Path to metadata config JSON"),
):
    """
    Validate data and configs without creating output (dry-run).

    Checks data quality, type consistency, and standard compliance
    without writing any files.

    Example:
        trailpack validate \\
            --data inventory.xlsx \\
            --mapping mapping.json \\
            --metadata metadata.json
    """
    from trailpack.io.smart_reader import SmartDataReader
    from trailpack.config import load_configs, extract_column_mappings, extract_general_details
    from trailpack.packing.export_service import DataPackageExporter
    from trailpack.packing.metadata_builder import MetadataBuilder
    from trailpack.validation.standard_validator import StandardValidator

    console.print(Panel.fit(
        "[bold cyan]Trailpack Validate[/bold cyan]\n"
        f"Data: {data}\n"
        f"Sheet: {sheet or 'N/A'}\n"
        f"Mapping: {mapping}\n"
        f"Metadata: {metadata}",
        title="Validation Configuration"
    ))

    try:
        # 1. Validate inputs
        if not data.exists():
            console.print(f"[red]Error: Data file not found: {data}[/red]")
            raise typer.Exit(1)

        # 2. Load configs
        console.print("[cyan]Loading configurations...[/cyan]")
        mapping_config, metadata_config = load_configs(
            mapping_path=mapping,
            metadata_path=metadata
        )

        # 3. Read data
        console.print(f"[cyan]Reading data file...[/cyan]")
        reader = SmartDataReader(data)
        console.print(f"  Engine: {reader.engine}")
        df = reader.read(sheet_name=sheet)
        console.print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")

        # 4. Extract mappings and metadata
        column_mappings = extract_column_mappings(mapping_config)
        general_details = extract_general_details(metadata_config)

        # 5. Build metadata
        console.print("[cyan]Building metadata...[/cyan]")
        metadata_builder = MetadataBuilder(
            dataframe=df,
            column_mappings=column_mappings,
            general_details=general_details,
            language="en"
        )
        package_metadata = metadata_builder.build()

        # 6. Validate
        console.print("[cyan]Validating against Trailpack standard...[/cyan]")
        validator = StandardValidator()
        validation_result = validator.validate(df, package_metadata)
        quality_level = validator.determine_quality_level(validation_result)

        # 7. Display results
        console.print("\n" + "=" * 60)
        console.print("[bold]Validation Results[/bold]")
        console.print("=" * 60 + "\n")

        # Quality level
        quality_colors = {
            "STRICT": "green",
            "STANDARD": "cyan",
            "BASIC": "yellow",
            "INVALID": "red"
        }
        color = quality_colors.get(quality_level, "white")
        console.print(f"Quality Level: [{color}bold]{quality_level}[/{color}bold]\n")

        # Errors
        if validation_result.errors:
            console.print(f"[red bold]Errors ({len(validation_result.errors)}):[/red bold]")
            for error in validation_result.errors:
                console.print(f"  [red]✗[/red] {error}")
            console.print()
        else:
            console.print("[green]✓ No errors[/green]\n")

        # Warnings
        if validation_result.warnings:
            console.print(f"[yellow bold]Warnings ({len(validation_result.warnings)}):[/yellow bold]")
            for warning in validation_result.warnings:
                console.print(f"  [yellow]⚠[/yellow] {warning}")
            console.print()
        else:
            console.print("[green]✓ No warnings[/green]\n")

        # Info
        if validation_result.info:
            console.print(f"[cyan bold]Info ({len(validation_result.info)}):[/cyan bold]")
            for info in validation_result.info:
                console.print(f"  [cyan]ℹ[/cyan] {info}")
            console.print()

        # Summary
        if quality_level == "INVALID":
            console.print("[red]✗ Validation failed - please fix errors before export[/red]")
            raise typer.Exit(1)
        else:
            console.print("[green]✓ Validation passed - ready for export[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def check(
    parquet_file: Path = typer.Argument(..., help="Path to Parquet file to check"),
):
    """
    Check existing Parquet file for standard compliance.

    Reads the Parquet file, extracts metadata, validates against
    Trailpack standard, and displays quality level.

    Example:
        trailpack check my-dataset.parquet
    """
    import pandas as pd
    from trailpack.validation.standard_validator import StandardValidator

    console.print(Panel.fit(
        f"[bold cyan]Checking:[/bold cyan] {parquet_file}",
        title="Trailpack Check"
    ))

    if not parquet_file.exists():
        console.print(f"[red]Error: File not found: {parquet_file}[/red]")
        raise typer.Exit(1)

    try:
        # 1. Read Parquet file
        console.print("[cyan]Reading Parquet file...[/cyan]")
        df = pd.read_parquet(parquet_file)
        console.print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")

        # 2. Extract metadata from Parquet
        console.print("[cyan]Extracting metadata...[/cyan]")
        parquet_file_obj = pd.io.parquet.read_parquet(parquet_file, engine='pyarrow')

        # Try to get metadata from Parquet schema
        import pyarrow.parquet as pq
        parquet_table = pq.read_table(parquet_file)

        # Extract custom metadata if available
        package_metadata = {}
        if parquet_table.schema.metadata:
            metadata_bytes = parquet_table.schema.metadata.get(b'trailpack_metadata')
            if metadata_bytes:
                import json
                package_metadata = json.loads(metadata_bytes.decode('utf-8'))
                console.print(f"  Found Trailpack metadata")
            else:
                console.print("[yellow]  Warning: No Trailpack metadata found in file[/yellow]")
        else:
            console.print("[yellow]  Warning: No metadata found in Parquet file[/yellow]")

        # 3. Validate
        console.print("[cyan]Validating against Trailpack standard...[/cyan]")
        validator = StandardValidator()
        validation_result = validator.validate(df, package_metadata)
        quality_level = validator.determine_quality_level(validation_result)

        # 4. Display results
        console.print("\n" + "=" * 60)
        console.print("[bold]Validation Results[/bold]")
        console.print("=" * 60 + "\n")

        # File info
        file_size = parquet_file.stat().st_size
        console.print(f"File: {parquet_file}")
        console.print(f"Size: {file_size / (1024*1024):.2f} MB")
        console.print(f"Rows: {len(df)}, Columns: {len(df.columns)}\n")

        # Quality level
        quality_colors = {
            "STRICT": "green",
            "STANDARD": "cyan",
            "BASIC": "yellow",
            "INVALID": "red"
        }
        color = quality_colors.get(quality_level, "white")
        console.print(f"Quality Level: [{color}bold]{quality_level}[/{color}bold]\n")

        # Errors
        if validation_result.errors:
            console.print(f"[red bold]Errors ({len(validation_result.errors)}):[/red bold]")
            for error in validation_result.errors:
                console.print(f"  [red]✗[/red] {error}")
            console.print()
        else:
            console.print("[green]✓ No errors[/green]\n")

        # Warnings
        if validation_result.warnings:
            console.print(f"[yellow bold]Warnings ({len(validation_result.warnings)}):[/yellow bold]")
            for warning in validation_result.warnings:
                console.print(f"  [yellow]⚠[/yellow] {warning}")
            console.print()
        else:
            console.print("[green]✓ No warnings[/green]\n")

        # Info
        if validation_result.info:
            console.print(f"[cyan bold]Info ({len(validation_result.info)}):[/cyan bold]")
            for info in validation_result.info:
                console.print(f"  [cyan]ℹ[/cyan] {info}")
            console.print()

        # Summary
        if quality_level == "INVALID":
            console.print("[red]✗ File does not meet Trailpack standards[/red]")
            raise typer.Exit(1)
        else:
            console.print("[green]✓ File meets Trailpack standards[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def init(
    project_name: str = typer.Argument(..., help="Name of the project to initialize"),
    directory: Optional[Path] = typer.Option(None, "--dir", "-d", help="Directory to create project in (default: current)"),
):
    """
    Initialize a new Trailpack project structure.

    Creates a directory with example configs, data folder,
    and README with instructions.

    Example:
        trailpack init my-dataset
        trailpack init my-dataset --dir ~/projects
    """
    if directory is None:
        directory = Path.cwd()

    project_path = directory / project_name

    console.print(Panel.fit(
        f"[bold cyan]Creating project:[/bold cyan] {project_name}\n"
        f"[bold cyan]Location:[/bold cyan] {project_path}",
        title="Trailpack Init"
    ))

    try:
        # 1. Create directory structure
        if project_path.exists():
            console.print(f"[red]Error: Directory already exists: {project_path}[/red]")
            raise typer.Exit(1)

        console.print("[cyan]Creating directory structure...[/cyan]")
        project_path.mkdir(parents=True)
        (project_path / "data").mkdir()
        (project_path / "configs").mkdir()
        (project_path / "output").mkdir()

        # 2. Create README
        console.print("[cyan]Creating README.md...[/cyan]")
        readme_content = f"""# {project_name}

A Trailpack dataset standardization project.

## Directory Structure

- `data/` - Place your raw data files here (Excel, CSV)
- `configs/` - Store your mapping and metadata configuration files
- `output/` - Generated Parquet data packages will be saved here

## Quick Start

### 1. Add Your Data

Place your data file in the `data/` directory:
```bash
cp your-data.xlsx data/
```

### 2. Create Configs with UI

Launch the interactive UI to map your data:
```bash
trailpack ui
```

- Upload your data file
- Map columns to ontology terms
- Add metadata
- Download configuration files to `configs/`

### 3. Process Data

Use the CLI to process your data with the configs:
```bash
trailpack process \\
    --data data/your-data.xlsx \\
    --sheet "Sheet1" \\
    --mapping configs/mapping_config.json \\
    --metadata configs/metadata_config.json \\
    --output output/clean-data.parquet
```

### 4. Validate (Optional)

Validate your data without creating output:
```bash
trailpack validate \\
    --data data/your-data.xlsx \\
    --mapping configs/mapping_config.json \\
    --metadata configs/metadata_config.json
```

### 5. Check Output

Check an existing Parquet file:
```bash
trailpack check output/clean-data.parquet
```

## Configuration Files

### Mapping Config (`mapping_config.json`)

Maps your columns to ontology terms:
```json
{{
  "version": "1.0.0",
  "config_type": "mapping",
  "language": "en",
  "column_mappings": {{
    "Product": "https://vocab.sentier.dev/products/product/Product",
    "CO2_emissions": "https://vocab.sentier.dev/model-terms/generic-terms/Emission"
  }}
}}
```

### Metadata Config (`metadata_config.json`)

Defines package metadata:
```json
{{
  "version": "1.0.0",
  "config_type": "metadata",
  "package": {{
    "name": "{project_name}",
    "title": "Your Dataset Title",
    "description": "Description of your dataset"
  }}
}}
```

## Learn More

- [Trailpack Documentation](https://github.com/TimoDiepers/trailpaack)
- [Frictionless Data Standard](https://specs.frictionlessdata.io/)
"""

        readme_path = project_path / "README.md"
        readme_path.write_text(readme_content)

        # 3. Create example mapping config
        console.print("[cyan]Creating example configs...[/cyan]")
        example_mapping = {
            "version": "1.0.0",
            "config_type": "mapping",
            "language": "en",
            "file_info": {
                "original_file": "your-data.xlsx",
                "sheet_name": "Sheet1"
            },
            "column_mappings": {
                "product_name": "https://vocab.sentier.dev/products/product/Product",
                "emissions": "https://vocab.sentier.dev/model-terms/generic-terms/Emission"
            }
        }

        import json
        mapping_path = project_path / "configs" / "example_mapping_config.json"
        mapping_path.write_text(json.dumps(example_mapping, indent=2, ensure_ascii=False))

        # 4. Create example metadata config
        example_metadata = {
            "version": "1.0.0",
            "config_type": "metadata",
            "package": {
                "name": project_name,
                "title": f"{project_name.replace('-', ' ').title()} Dataset",
                "description": "Add your dataset description here",
                "version": "0.1.0",
                "keywords": ["lca", "sustainability"],
                "homepage": "https://example.com"
            },
            "licenses": [
                {
                    "name": "CC-BY-4.0",
                    "path": "https://creativecommons.org/licenses/by/4.0/",
                    "title": "Creative Commons Attribution 4.0"
                }
            ],
            "contributors": [
                {
                    "title": "Your Name",
                    "role": "author"
                }
            ]
        }

        metadata_path = project_path / "configs" / "example_metadata_config.json"
        metadata_path.write_text(json.dumps(example_metadata, indent=2, ensure_ascii=False))

        # 5. Create .gitignore
        gitignore_content = """# Data files
data/*.xlsx
data/*.xls
data/*.csv

# Output files
output/*.parquet

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/

# IDE
.vscode/
.idea/
*.swp
"""
        gitignore_path = project_path / ".gitignore"
        gitignore_path.write_text(gitignore_content)

        # Success message
        console.print(f"\n[green]✓ Project created successfully![/green]")
        console.print(f"\n[cyan]Next steps:[/cyan]")
        console.print(f"  1. cd {project_path}")
        console.print(f"  2. Place your data in data/")
        console.print(f"  3. Run: trailpack ui")
        console.print(f"\n[cyan]Files created:[/cyan]")
        console.print(f"  ✓ README.md")
        console.print(f"  ✓ configs/example_mapping_config.json")
        console.print(f"  ✓ configs/example_metadata_config.json")
        console.print(f"  ✓ .gitignore")
        console.print(f"  ✓ data/ (empty)")
        console.print(f"  ✓ output/ (empty)")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        from trailpack import __version__
        console.print(f"[cyan]Trailpack version:[/cyan] {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """
    Trailpack - Dataset standardization tool.

    Interactive UI for mapping data to ontologies and creating
    Frictionless Data Packages for LCA and sustainability research.
    """
    pass


if __name__ == "__main__":
    app()
