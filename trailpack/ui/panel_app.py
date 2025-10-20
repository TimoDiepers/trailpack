"""Panel UI application for trailpack - Excel to PyST mapper."""

import sys
from pathlib import Path

# Add parent directory to path for deployment
_current_dir = Path(__file__).resolve().parent
_repo_root = _current_dir.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

# Load .env file before importing any trailpack modules
try:
    from dotenv import load_dotenv

    env_path = _repo_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded .env from: {env_path}")
except ImportError:
    print("python-dotenv not installed, skipping .env loading")

import asyncio
import base64
import tempfile
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import quote

import panel as pn
import pandas as pd
import openpyxl

from trailpack.excel import ExcelReader
from trailpack.io.smart_reader import SmartDataReader
from trailpack.pyst.api.requests.suggest import SUPPORTED_LANGUAGES
from trailpack.pyst.api.client import get_suggest_client
from trailpack.packing.datapackage_schema import DataPackageSchema, COMMON_LICENSES
from trailpack.validation import StandardValidator
from trailpack.config import (
    build_mapping_config,
    build_metadata_config,
    export_mapping_json,
    export_metadata_json,
    generate_config_filename,
)

# Initialize Panel extension
pn.extension('tabulator', sizing_mode="stretch_width")

ICON_PATH = Path(__file__).parent / "icon.svg"
PAGE_ICON = str(ICON_PATH) if ICON_PATH.is_file() else "📦"
LOGO_BASE64 = (
    base64.b64encode(ICON_PATH.read_bytes()).decode("utf-8")
    if ICON_PATH.is_file()
    else None
)


def iri_to_web_url(iri: str, language: str = "en") -> str:
    """
    Convert an IRI to a vocab.sentier.dev web page URL.

    Args:
        iri: The IRI (e.g., "https://vocab.sentier.dev/Geonames/A")
        language: Language code (default: "en")

    Returns:
        Web page URL
    """
    parts = iri.split("/")
    if len(parts) >= 5 and parts[2] == "vocab.sentier.dev":
        concept_scheme = "/".join(parts[:4]) + "/"
    else:
        concept_scheme = "/".join(parts[:3]) + "/" if len(parts) >= 3 else iri

    encoded_iri = quote(iri, safe="")
    encoded_scheme = quote(concept_scheme, safe="")
    web_url = f"https://vocab.sentier.dev/web/concept/{encoded_iri}"

    return web_url


def sanitize_search_query(query: str) -> str:
    """
    Sanitize search query for safe API calls.
    """
    import re
    sanitized = re.sub(r"[^\w\s\-.]", " ", query)
    sanitized = re.sub(r"\s+", " ", sanitized)
    sanitized = sanitized.strip()
    return sanitized


def extract_first_word(query: str) -> str:
    """
    Extract the first word from a string, stopping at the first space.
    """
    if not query:
        return ""
    parts = query.split(" ", 1)
    return parts[0] if parts else ""


async def fetch_suggestions_async(
    client, column_name: str, language: str
) -> List[Dict[str, str]]:
    """Fetch PyST suggestions for a column name."""
    try:
        sanitized_query = sanitize_search_query(column_name)
        if not sanitized_query:
            return []

        suggestions = await client.suggest(sanitized_query, language)
        return suggestions[:5]
    except Exception as e:
        print(f"Could not fetch suggestions for '{column_name}': {e}")
        return []


async def fetch_concept_async(client, iri: str, language: str) -> Optional[str]:
    """Fetch concept definition from PyST API."""
    try:
        concept = await client.get_concept(iri)

        definitions = concept.get("http://www.w3.org/2004/02/skos/core#definition", [])

        if not definitions:
            return None

        for definition in definitions:
            if isinstance(definition, dict) and definition.get("@language") == language:
                return definition.get("@value")

        if definitions and isinstance(definitions[0], dict):
            return definitions[0].get("@value")

        return None
    except Exception as e:
        print(f"Error fetching concept {iri}: {e}")
        return None


def load_excel_data(file_path: Path, sheet_name: str) -> pd.DataFrame:
    """Load Excel data into a pandas DataFrame using SmartDataReader."""
    try:
        smart_reader = SmartDataReader(file_path)
        df = smart_reader.read(sheet_name=sheet_name)
        return df
    except Exception as e:
        print(f"Error loading Excel data: {e}")
        return None


class TrailpackApp:
    """Panel-based UI for Trailpack Excel to PyST mapper."""

    def __init__(self):
        self.page = 1
        self.file_bytes = None
        self.file_name = None
        self.language = "en"
        self.temp_path = None
        self.reader = None
        self.selected_sheet = None
        self.df = None
        self.column_mappings = {}
        self.column_descriptions = {}
        self.concept_definitions = {}
        self.suggestions_cache = {}
        self.general_details = {}
        self.resource_name = None
        self.resource_name_confirmed = False
        self.resource_name_accepted = False
        
        # Create PyST client once for reuse
        self.pyst_client = get_suggest_client()
        
        # Create main layout
        self.main_panel = pn.Column(sizing_mode="stretch_both")
        self.update_view()

    def update_view(self):
        """Update the main panel based on current page."""
        self.main_panel.clear()
        
        if self.page == 1:
            self.main_panel.append(self.page_1_upload())
        elif self.page == 2:
            self.main_panel.append(self.page_2_select_sheet())
        elif self.page == 3:
            self.main_panel.append(self.page_3_map_columns())
        elif self.page == 4:
            self.main_panel.append(self.page_4_general_details())
        elif self.page == 5:
            self.main_panel.append(self.page_5_review())

    def navigate_to(self, page: int):
        """Navigate to a specific page."""
        self.page = page
        self.update_view()

    def page_1_upload(self):
        """Page 1: File Upload and Language Selection."""
        title = pn.pane.Markdown("# Step 1: Upload File and Select Language")
        description = pn.pane.Markdown(
            "Upload an Excel file and select the language for PyST concept mapping."
        )

        file_input = pn.widgets.FileInput(accept=".xlsx,.xlsm,.xltx,.xltm", name="Upload Excel File")
        
        language_select = pn.widgets.Select(
            name="Select Language",
            options=sorted(list(SUPPORTED_LANGUAGES)),
            value="en"
        )

        def handle_upload(event):
            if event.new is not None:
                self.file_bytes = event.new
                self.file_name = file_input.filename
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                    tmp.write(self.file_bytes)
                    self.temp_path = Path(tmp.name)
                
                # Load Excel reader
                try:
                    self.reader = ExcelReader(self.temp_path)
                except Exception as e:
                    print(f"Error loading Excel file: {e}")

        file_input.param.watch(handle_upload, 'value')
        
        def handle_language_change(event):
            self.language = event.new

        language_select.param.watch(handle_language_change, 'value')

        next_button = pn.widgets.Button(name="Next →", button_type="primary")
        
        def on_next(event):
            if self.file_name:
                self.navigate_to(2)
        
        next_button.on_click(on_next)

        return pn.Column(
            title,
            description,
            file_input,
            language_select,
            pn.Row(pn.Spacer(), next_button),
            sizing_mode="stretch_width"
        )

    def page_2_select_sheet(self):
        """Page 2: Sheet Selection."""
        title = pn.pane.Markdown(f"# Step 2: Select Sheet\n**File:** {self.file_name}")

        if not self.reader:
            return pn.Column(title, pn.pane.Markdown("No file loaded"))

        sheets = self.reader.sheets()
        sheet_select = pn.widgets.RadioButtonGroup(
            name="Available Sheets",
            options=sheets,
            value=self.selected_sheet or sheets[0]
        )

        preview_pane = pn.Column()

        def update_preview(event):
            self.selected_sheet = event.new
            df = load_excel_data(self.temp_path, self.selected_sheet)
            if df is not None:
                self.df = df
                preview_pane.clear()
                preview_pane.append(pn.pane.Markdown("### Data Preview"))
                preview_pane.append(pn.pane.DataFrame(df.head(10), sizing_mode="stretch_width"))

        sheet_select.param.watch(update_preview, 'value')
        
        # Trigger initial preview
        if self.selected_sheet is None and sheets:
            self.selected_sheet = sheets[0]
            df = load_excel_data(self.temp_path, self.selected_sheet)
            if df is not None:
                self.df = df
                preview_pane.append(pn.pane.Markdown("### Data Preview"))
                preview_pane.append(pn.pane.DataFrame(df.head(10), sizing_mode="stretch_width"))

        back_button = pn.widgets.Button(name="← Back", button_type="default")
        next_button = pn.widgets.Button(name="Next →", button_type="primary")
        
        def on_back(event):
            self.navigate_to(1)
        
        def on_next(event):
            if self.selected_sheet:
                self.navigate_to(3)
        
        back_button.on_click(on_back)
        next_button.on_click(on_next)

        return pn.Column(
            title,
            sheet_select,
            preview_pane,
            pn.Row(back_button, pn.Spacer(), next_button),
            sizing_mode="stretch_width"
        )

    def page_3_map_columns(self):
        """Page 3: Column Mapping."""
        title = pn.pane.Markdown(
            f"# Step 3: Map Columns to PyST Concepts\n"
            f"**File:** {self.file_name} | **Sheet:** {self.selected_sheet}"
        )

        if self.df is None:
            return pn.Column(title, pn.pane.Markdown("No data loaded"))

        columns = self.reader.columns(self.selected_sheet)
        
        mapping_widgets = []
        
        for column in columns:
            column_pane = pn.Column(
                pn.pane.Markdown(f"**{column}**"),
                sizing_mode="stretch_width"
            )
            
            # Sample values
            sample_values = self.df[column].dropna().head(3).astype(str).tolist()
            if sample_values:
                column_pane.append(pn.pane.Markdown(f"*Sample: {', '.join(sample_values[:3])}*"))
            
            # Check if column is numeric
            is_numeric = pd.api.types.is_numeric_dtype(self.df[column])
            
            # Create AutocompleteInput for ontology search
            autocomplete_input = pn.widgets.AutocompleteInput(
                name="Search for ontology",
                placeholder="Type to search PyST concepts...",
                options=[],
                case_sensitive=False,
                min_characters=2,
                value=""
            )
            
            # Create info pane for displaying selected concept
            info_pane = pn.pane.Markdown("", sizing_mode="stretch_width")
            
            # Pre-populate with initial suggestions based on column name
            initial_query = sanitize_search_query(column)
            if initial_query and len(initial_query) >= 2:
                async def fetch_and_populate_initial(col=column, widget=autocomplete_input, info=info_pane):
                    """Fetch initial suggestions and populate widget."""
                    first_word = extract_first_word(initial_query)
                    suggestions = await fetch_suggestions_async(
                        self.pyst_client, 
                        first_word, 
                        self.language
                    )
                    
                    valid_suggestions = []
                    labels = []
                    for s in suggestions:
                        try:
                            if isinstance(s, dict):
                                s_id = s.get("id") or s.get("id_") or s.get("uri")
                                s_label = s.get("label") or s.get("name") or s.get("title")
                            else:
                                s_id = getattr(s, "id", None) or getattr(s, "id_", None)
                                s_label = getattr(s, "label", None) or getattr(s, "name", None)
                            
                            if s_id and s_label:
                                labels.append(s_label)
                                valid_suggestions.append({"id": s_id, "label": s_label})
                        except Exception:
                            continue
                    
                    # Update widget options and set initial value to first suggestion
                    widget.options = labels[:10]
                    if valid_suggestions:
                        # Set the value to the first suggestion
                        widget.value = valid_suggestions[0]["label"]
                        # Store the mapping
                        self.column_mappings[col] = valid_suggestions[0]["id"]
                        
                        # Fetch and display concept definition
                        definition = await fetch_concept_async(
                            self.pyst_client,
                            valid_suggestions[0]["id"],
                            self.language
                        )
                        web_url = iri_to_web_url(valid_suggestions[0]["id"], self.language)
                        if definition:
                            info.object = (
                                f"**Selected:** {valid_suggestions[0]['label']}\n\n"
                                f"**Description:** {definition}\n\n"
                                f"[🔗 View on vocab.sentier.dev]({web_url})"
                            )
                        else:
                            info.object = (
                                f"**Selected:** {valid_suggestions[0]['label']}\n\n"
                                f"[🔗 View on vocab.sentier.dev]({web_url})"
                            )
                    
                    # Store suggestions in cache
                    if valid_suggestions:
                        cache_key = f"{col}_{first_word}"
                        self.suggestions_cache[cache_key] = suggestions
                
                # Let Panel handle the async call
                pn.state.execute(fetch_and_populate_initial)
            
            # Update suggestions and info as user types
            def make_value_handler(col, widget, info):
                async def handler(event):
                    search_value = event.new
                    if search_value and len(search_value) >= 2:
                        # Fetch new suggestions
                        sanitized_query = sanitize_search_query(search_value)
                        if sanitized_query:
                            suggestions = await fetch_suggestions_async(
                                self.pyst_client, 
                                sanitized_query, 
                                self.language
                            )
                            
                            # Extract valid suggestions
                            valid_suggestions = []
                            labels = []
                            for s in suggestions:
                                try:
                                    if isinstance(s, dict):
                                        s_id = s.get("id") or s.get("id_") or s.get("uri")
                                        s_label = s.get("label") or s.get("name") or s.get("title")
                                    else:
                                        s_id = getattr(s, "id", None) or getattr(s, "id_", None)
                                        s_label = getattr(s, "label", None) or getattr(s, "name", None)
                                    
                                    if s_id and s_label:
                                        labels.append(s_label)
                                        valid_suggestions.append({"id": s_id, "label": s_label})
                                except Exception:
                                    continue
                            
                            # Update widget options
                            widget.options = labels[:10]
                            
                            # Store suggestions in cache
                            if valid_suggestions:
                                cache_key = f"{col}_{search_value}"
                                self.suggestions_cache[cache_key] = suggestions
                            
                            # Check if the current value matches a suggestion and update info
                            for suggestion in valid_suggestions:
                                if suggestion["label"] == search_value:
                                    self.column_mappings[col] = suggestion["id"]
                                    
                                    # Fetch and display concept definition
                                    definition = await fetch_concept_async(
                                        self.pyst_client,
                                        suggestion["id"],
                                        self.language
                                    )
                                    web_url = iri_to_web_url(suggestion["id"], self.language)
                                    if definition:
                                        info.object = (
                                            f"**Selected:** {suggestion['label']}\n\n"
                                            f"**Description:** {definition}\n\n"
                                            f"[🔗 View on vocab.sentier.dev]({web_url})"
                                        )
                                    else:
                                        info.object = (
                                            f"**Selected:** {suggestion['label']}\n\n"
                                            f"[🔗 View on vocab.sentier.dev]({web_url})"
                                        )
                                    break
                    
                return handler
            
            autocomplete_input.param.watch(
                make_value_handler(column, autocomplete_input, info_pane), 
                'value'
            )
            column_pane.append(autocomplete_input)
            column_pane.append(info_pane)
            
            # Description field
            description_input = pn.widgets.TextAreaInput(
                name="Column Description (optional)" if column in self.column_mappings else "Column Description *",
                placeholder="Describe what this column represents..." if column not in self.column_mappings else "Add optional comments or notes...",
                value=self.column_descriptions.get(column, ""),
                height=80
            )
            column_pane.append(description_input)
            
            def make_description_handler(col):
                def handler(event):
                    if event.new:
                        self.column_descriptions[col] = event.new
                    else:
                        self.column_descriptions.pop(col, None)
                return handler
            
            description_input.param.watch(make_description_handler(column), 'value')
            
            # If numeric, add unit search field
            if is_numeric:
                unit_autocomplete = pn.widgets.AutocompleteInput(
                    name="Search for unit *",
                    placeholder="Type to search for unit (required for numeric columns)...",
                    options=[],
                    case_sensitive=False,
                    min_characters=2,
                    value=""
                )
                
                unit_info_pane = pn.pane.Markdown("", sizing_mode="stretch_width")
                
                # Update unit suggestions and info as user types
                def make_unit_handler(col, widget, info):
                    async def handler(event):
                        search_value = event.new
                        if search_value and len(search_value) >= 2:
                            # Fetch unit suggestions
                            sanitized_query = sanitize_search_query(search_value)
                            if sanitized_query:
                                suggestions = await fetch_suggestions_async(
                                    self.pyst_client, 
                                    sanitized_query, 
                                    self.language
                                )
                                
                                # Extract valid suggestions
                                valid_suggestions = []
                                labels = []
                                for s in suggestions:
                                    try:
                                        if isinstance(s, dict):
                                            s_id = s.get("id") or s.get("id_") or s.get("uri")
                                            s_label = s.get("label") or s.get("name") or s.get("title")
                                        else:
                                            s_id = getattr(s, "id", None) or getattr(s, "id_", None)
                                            s_label = getattr(s, "label", None) or getattr(s, "name", None)
                                        
                                        if s_id and s_label:
                                            labels.append(s_label)
                                            valid_suggestions.append({"id": s_id, "label": s_label})
                                    except Exception:
                                        continue
                                
                                # Update widget options
                                widget.options = labels[:10]
                                
                                # Store suggestions in cache
                                if valid_suggestions:
                                    cache_key = f"{col}_unit_{search_value}"
                                    self.suggestions_cache[cache_key] = suggestions
                                
                                # Check if the current value matches a suggestion and update info
                                for suggestion in valid_suggestions:
                                    if suggestion["label"] == search_value:
                                        self.column_mappings[f"{col}_unit"] = suggestion["id"]
                                        
                                        # Fetch and display unit concept definition
                                        definition = await fetch_concept_async(
                                            self.pyst_client,
                                            suggestion["id"],
                                            self.language
                                        )
                                        web_url = iri_to_web_url(suggestion["id"], self.language)
                                        if definition:
                                            info.object = (
                                                f"**Selected unit:** {suggestion['label']}\n\n"
                                                f"**Description:** {definition}\n\n"
                                                f"[🔗 View on vocab.sentier.dev]({web_url})"
                                            )
                                        else:
                                            info.object = (
                                                f"**Selected unit:** {suggestion['label']}\n\n"
                                                f"[🔗 View on vocab.sentier.dev]({web_url})"
                                            )
                                        break
                        
                    return handler
                
                unit_autocomplete.param.watch(
                    make_unit_handler(column, unit_autocomplete, unit_info_pane), 
                    'value'
                )
                column_pane.append(unit_autocomplete)
                column_pane.append(unit_info_pane)
            
            mapping_widgets.append(column_pane)
            mapping_widgets.append(pn.layout.Divider())

        back_button = pn.widgets.Button(name="← Back", button_type="default")
        next_button = pn.widgets.Button(name="Next →", button_type="primary")
        
        def on_back(event):
            self.navigate_to(2)
        
        def on_next(event):
            self.navigate_to(4)
        
        back_button.on_click(on_back)
        next_button.on_click(on_next)

        return pn.Column(
            title,
            *mapping_widgets,
            pn.Row(back_button, pn.Spacer(), next_button),
            sizing_mode="stretch_width",
            scroll=True
        )

    def page_4_general_details(self):
        """Page 4: General Details."""
        title = pn.pane.Markdown("# Step 4: General Details")
        
        schema = DataPackageSchema()
        field_defs = schema.field_definitions

        name_input = pn.widgets.TextInput(
            name="Package Name *",
            placeholder="my-data-package",
            value=self.general_details.get("name", "")
        )
        
        title_input = pn.widgets.TextInput(
            name="Title *",
            placeholder="My Data Package",
            value=self.general_details.get("title", "")
        )
        
        description_input = pn.widgets.TextAreaInput(
            name="Description",
            placeholder="Describe your data package...",
            value=self.general_details.get("description", ""),
            height=100
        )
        
        def make_handler(key, widget):
            def handler(event):
                if event.new:
                    self.general_details[key] = event.new
                else:
                    self.general_details.pop(key, None)
            return handler
        
        name_input.param.watch(make_handler("name", name_input), 'value')
        title_input.param.watch(make_handler("title", title_input), 'value')
        description_input.param.watch(make_handler("description", description_input), 'value')

        back_button = pn.widgets.Button(name="← Back", button_type="default")
        generate_button = pn.widgets.Button(name="📦 Generate Parquet File", button_type="primary")
        
        def on_back(event):
            self.navigate_to(3)
        
        def on_generate(event):
            if self.general_details.get("name") and self.general_details.get("title"):
                # Set default values for required fields
                if "licenses" not in self.general_details:
                    self.general_details["licenses"] = [{"name": "CC-BY-4.0", "title": "Creative Commons Attribution 4.0"}]
                if "contributors" not in self.general_details:
                    self.general_details["contributors"] = [{"name": "User", "role": "author"}]
                if "sources" not in self.general_details:
                    self.general_details["sources"] = [{"title": "Original Data"}]
                if "created" not in self.general_details:
                    self.general_details["created"] = datetime.now().strftime("%Y-%m-%d")
                
                try:
                    from trailpack.packing.export_service import DataPackageExporter
                    
                    exporter = DataPackageExporter(
                        df=self.df,
                        column_mappings=self.column_mappings,
                        general_details=self.general_details,
                        sheet_name=self.selected_sheet,
                        file_name=self.file_name,
                        suggestions_cache=self.suggestions_cache,
                        column_descriptions=self.column_descriptions,
                    )
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".parquet") as tmp:
                        output_path, quality_level, validation_result = exporter.export(tmp.name)
                        self.output_path = output_path
                        self.quality_level = quality_level
                        self.validation_result = validation_result
                        self.exporter = exporter
                    
                    self.navigate_to(5)
                except Exception as e:
                    print(f"Export failed: {e}")
        
        back_button.on_click(on_back)
        generate_button.on_click(on_generate)

        return pn.Column(
            title,
            pn.pane.Markdown("### Basic Information"),
            name_input,
            title_input,
            description_input,
            pn.Row(back_button, pn.Spacer(), generate_button),
            sizing_mode="stretch_width"
        )

    def page_5_review(self):
        """Page 5: Review Parquet File."""
        title = pn.pane.Markdown("# Step 5: Review Parquet File")
        
        if not hasattr(self, 'output_path'):
            return pn.Column(
                title,
                pn.pane.Markdown("No parquet file has been generated yet."),
                sizing_mode="stretch_width"
            )
        
        from trailpack.packing.packing import read_parquet
        
        exported_df, exported_metadata = read_parquet(self.output_path)
        
        success_msg = pn.pane.Alert(
            f"✅ Data package created successfully!\n\n**Validation Level:** {getattr(self, 'quality_level', 'VALID')}",
            alert_type="success"
        )
        
        metadata_pane = pn.pane.JSON(exported_metadata, depth=3)
        data_pane = pn.pane.DataFrame(exported_df.head(10), sizing_mode="stretch_width")
        
        back_button = pn.widgets.Button(name="← Back", button_type="default")
        
        def on_back(event):
            self.navigate_to(4)
        
        back_button.on_click(on_back)

        return pn.Column(
            title,
            success_msg,
            pn.pane.Markdown("### Embedded Metadata"),
            metadata_pane,
            pn.pane.Markdown("### 📊 Data Sample (first 10 rows)"),
            data_pane,
            pn.Row(back_button),
            sizing_mode="stretch_width"
        )

    def view(self):
        """Return the main panel view."""
        template = pn.template.FastListTemplate(
            title="Trailpack - Excel to PyST Mapper",
            sidebar=[
                pn.pane.Markdown("## Trailpack"),
                pn.pane.Markdown("Excel to PyST Mapper"),
                pn.layout.Divider(),
                pn.pane.Markdown("### Steps:"),
                pn.pane.Markdown("1. Upload & Select Language"),
                pn.pane.Markdown("2. Select Sheet"),
                pn.pane.Markdown("3. Map Columns"),
                pn.pane.Markdown("4. General Details"),
                pn.pane.Markdown("5. Review Parquet File"),
            ],
            main=[self.main_panel],
            header_background="#1f77b4"
        )
        return template


# Create and serve the app
app = TrailpackApp()


def create_panel_app():
    """Create and return the Panel app."""
    return app.view()


if __name__ == "__main__":
    pn.serve(create_panel_app, port=5006, show=True)
