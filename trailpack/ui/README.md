# Trailpack UI

A Streamlit-based web interface for mapping Excel columns to PyST concepts.

## Features

- **Page 1**: Upload Excel file and select language for PyST concept mapping
- **Page 2**: Select sheet from the uploaded Excel file with data preview
- **Page 3**: Map columns to PyST concepts with automatic suggestions and dataframe preview
- **Page 4**: Enter general details and metadata for the data package

## Running the UI

### Option 1: Using Streamlit directly

```bash
streamlit run trailpack/ui/streamlit_app.py
```

### Option 2: Using the run script

```bash
python trailpack/ui/run_streamlit.py
```

The UI will be available at http://localhost:8501

## Requirements

- streamlit >= 1.28.0
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
   - View automatic PyST concept suggestions based on the column name
   - Select the most appropriate PyST concept mapping
   - Continue to general details

4. **General Details**: Provide metadata for the data package:
   - Package name (required) - URL-safe identifier
   - Title, description, and version (optional)
   - Profile type, keywords, homepage, and repository (optional)
   - Real-time validation of inputs
   - Finish to complete the workflow

## Features

- **Smooth Page Transitions**: Uses Streamlit's session state for seamless navigation
- **Data Preview**: View the first entries of your dataframe before and during mapping
- **Simplified Column Mapping**: Clean, table-like interface for mapping columns
- **Internal View Object**: Mappings are stored internally in the correct format
- **Progress Indicators**: Visual feedback on current step and completion status

## Output Format

The UI internally generates a view object with the following structure:

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

This view object is stored in `st.session_state.view_object` and can be accessed programmatically.

## Configuration

The UI uses the same configuration as the rest of the trailpack package.

### Local Development

For local development, create a `.env` file in the project root with your PyST API credentials:

```
PYST_HOST=http://localhost:8000/api/v1/
PYST_AUTH_TOKEN=your_token_here
PYST_TIMEOUT=30
```

You can also copy `.env.example` and modify it:

```bash
cp .env.example .env
```

### Streamlit Cloud Deployment

For deploying to Streamlit Community Cloud:

1. **Push your code to GitHub** (excluding secrets)

2. **Configure secrets in Streamlit Cloud**:
   - Go to your app settings in Streamlit Cloud
   - Navigate to "Secrets" section
   - Add the following secrets in TOML format:

   ```toml
   PYST_HOST = "https://vocab.sentier.dev/api/v1/"
   PYST_AUTH_TOKEN = "your_production_token"
   PYST_TIMEOUT = "30"
   ```

3. **Specify the main file**:
   - Main file path: `trailpack/ui/streamlit_app.py`

4. **Requirements**:
   - The `requirements.txt` in the root directory will be automatically used
   - Ensure all dependencies are listed (streamlit, pandas, openpyxl, httpx, etc.)

### Secrets Management

The application reads configuration from:
1. Streamlit secrets (for Streamlit Cloud deployment)
2. Environment variables (for local development)
3. Default values as fallback

The configuration is handled in `trailpack/pyst/api/config.py`:
- Streamlit secrets are checked first (using `st.secrets`)
- Falls back to environment variables if secrets are not available
- Uses sensible defaults if neither is available

## Architecture

The UI is built using Streamlit with the following features:

- `streamlit_app.py`: Main application with session state management
- Smooth page transitions using `st.rerun()`
- Asynchronous API calls for fetching PyST suggestions
- Clean, responsive layout with sidebar navigation
- Data preview on multiple pages
- Internal view object generation (not displayed to user)
