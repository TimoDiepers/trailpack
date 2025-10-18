# Trailpack UI

A Panel-based web interface for mapping Excel columns to PyST concepts.

## Features

- **Page 1**: Upload Excel file and select language for PyST concept mapping
- **Page 2**: Select sheet from the uploaded Excel file with data preview
- **Page 3**: Map columns to PyST concepts with automatic suggestions and dataframe preview
- **Page 4**: Enter general details and metadata for the data package
- **Page 5**: Review and download the generated Parquet file

## Running the UI

### Option 1: Using the CLI command

```bash
trailpack ui
```

### Option 2: Using Panel directly

```bash
panel serve trailpack/ui/panel_app.py --show
```

### Option 3: Using the run script

```bash
python trailpack/ui/run_panel.py
```

The UI will be available at http://localhost:5006

## Requirements

- panel >= 1.3.0
- pandas >= 2.0.0
- openpyxl
- httpx
- python-dotenv
- langcodes
- pydantic

## Workflow

1. **Upload File & Select Language**: Upload an Excel file (.xlsx, .xlsm, .xltx, .xltm) and select the language for PyST concept mapping from supported languages (en, de, es, fr, pt, it, da).

2. **Select Sheet**: Choose which sheet from the Excel file you want to process. Preview the data to ensure it's the correct sheet.

3. **Map Columns**: For each column in the selected sheet:
   - View the dataframe preview at the top
   - See sample values from each column
   - Search for PyST concept mappings
   - Add column descriptions
   - Continue to general details

4. **General Details**: Provide metadata for the data package:
   - Package name (required) - URL-safe identifier
   - Title, description, and version (optional)
   - Profile type, keywords, homepage, and repository (optional)
   - Real-time validation of inputs
   - Generate the Parquet file

5. **Review**: Review the generated Parquet file with embedded metadata and download it.

## Features

- **Interactive Navigation**: Uses Panel's reactive programming for seamless page transitions
- **Data Preview**: View the first entries of your dataframe before and during mapping
- **Simplified Column Mapping**: Clean interface for mapping columns
- **Progress Indicators**: Visual feedback on current step and completion status
- **Modern UI**: Built with Panel's FastListTemplate for a professional look

## Configuration

The UI uses the same configuration as the rest of the trailpack package. 

### Local Development

For local development, set up your `.env` file with the PyST API credentials:

```
PYST_HOST=https://api.pyst.example.com
PYST_AUTH_TOKEN=your_token_here
```

### Cloud Deployment

For deployment options, see [PANEL_DEPLOYMENT.md](../../PANEL_DEPLOYMENT.md).

The configuration system automatically loads from:
1. Environment variables (set via `.env` file or system)
2. Deployment platform secrets/configuration

## Architecture

The UI is built using Panel with the following features:

- `panel_app.py`: Main application with reactive state management
- `TrailpackApp` class: Encapsulates all UI logic and state
- Page-based navigation system
- Asynchronous API calls for fetching PyST suggestions
- Responsive layout with sidebar navigation
- Data preview on multiple pages

## Why Panel?

Panel was chosen over Streamlit for better maintainability:

1. **More flexible architecture**: Panel apps can be served standalone or embedded
2. **Better integration**: Works seamlessly with the HoloViz ecosystem
3. **More deployment options**: Greater flexibility in how and where to deploy
4. **Greater control**: More programmatic control over UI components
5. **Better performance**: More efficient WebSocket handling and rendering
