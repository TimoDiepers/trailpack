# Trailpack UI

A Panel-based web interface for mapping Excel columns to PyST concepts.

## Features

- **Page 1**: Upload Excel file and select language for PyST concept mapping
- **Page 2**: Select sheet from the uploaded Excel file
- **Page 3**: Map columns to PyST concepts with automatic suggestions

## Running the UI

### Option 1: Using the simple_app module directly

```bash
cd trailpack
python -m trailpack.ui.simple_app
```

The UI will be available at http://localhost:5006

### Option 2: Using Panel serve

```bash
panel serve trailpack/ui/simple_app.py --show
```

### Option 3: From Python code

```python
import panel as pn
from trailpack.ui import create_app

app = create_app()
pn.serve(app, port=5006, show=True)
```

## Requirements

- panel >= 1.0.0
- openpyxl
- httpx
- python-dotenv
- langcodes
- pydantic

## Workflow

1. **Upload File & Select Language**: Upload an Excel file (.xlsx, .xlsm, .xltx, .xltm) and select the language for PyST concept mapping from supported languages (en, de, es, fr, pt, it, da).

2. **Select Sheet**: Choose which sheet from the Excel file you want to process.

3. **Map Columns**: For each column in the selected sheet:
   - View sample values from the column
   - See automatic PyST concept suggestions based on the column name
   - Select the most appropriate PyST concept mapping
   - Generate a JSON view object with all mappings

## Output Format

The UI generates a JSON view object with the following structure:

```json
{
  "sheet_name": "Sheet1",
  "dataset_name": "file_name_Sheet1",
  "columns": {
    "column_name_1": {
      "values": ["value1", "value2", "..."],
      "mapping_to_pyst": {
        "suggestions": [
          {
            "label": "string",
            "id": "string"
          }
        ],
        "selected": {
          "label": "string",
          "id": "string"
        }
      }
    }
  }
}
```

## Configuration

The UI uses the same configuration as the rest of the trailpack package. Make sure to set up your `.env` file with the PyST API credentials:

```
PYST_HOST=https://api.pyst.example.com
PYST_AUTH_TOKEN=your_token_here
```

## Architecture

The UI is built using Panel's FastListTemplate and consists of three main pages:

- `simple_app.py`: Main application with state management and page navigation
- Each page is rendered dynamically based on the current state
- Asynchronous API calls fetch PyST suggestions without blocking the UI
