"""Streamlit UI application for trailpack - Excel to PyST mapper."""

import sys
from pathlib import Path

# Add parent directory to path for Streamlit Cloud deployment
# This ensures that trailpack modules can be imported even when the package isn't installed
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

import streamlit as st
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
        Web page URL (e.g., "https://vocab.sentier.dev/web/concept/...?concept_scheme=...&language=en")

    Example:
        >>> iri_to_web_url("https://vocab.sentier.dev/Geonames/A", "en")
        'https://vocab.sentier.dev/web/concept/https%3A%2F%2Fvocab.sentier.dev%2FGeonames%2FA?concept_scheme=https%3A%2F%2Fvocab.sentier.dev%2FGeonames&language=en'
    """
    # Extract the concept scheme from the IRI
    # For IRIs like "https://vocab.sentier.dev/{namespace}/{concept}",
    # the scheme is "https://vocab.sentier.dev/{namespace}/"
    # For IRIs like "https://vocab.sentier.dev/{namespace}/{type}/{term}",
    # the scheme is still "https://vocab.sentier.dev/{namespace}/"
    parts = iri.split("/")
    if len(parts) >= 5 and parts[2] == "vocab.sentier.dev":
        # Scheme is base_url + namespace (first path segment) + trailing slash
        concept_scheme = "/".join(parts[:4]) + "/"
    else:
        # Fallback: use base URL as concept scheme for non-standard IRIs
        concept_scheme = "/".join(parts[:3]) + "/" if len(parts) >= 3 else iri

    # URL encode the IRI and concept scheme
    encoded_iri = quote(iri, safe="")
    encoded_scheme = quote(concept_scheme, safe="")

    # Construct the web URL
    web_url = f"https://vocab.sentier.dev/web/concept/{encoded_iri}"

    return web_url


# Page configuration

st.set_page_config(
    page_title="Trailpack - Excel to PyST Mapper",
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for consistent typography
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

    /* Apply Montserrat to all text, but exclude Material Icons */
    html, body, [class*="css"], [class*="st-"],
    h1, h2, h3, h4, h5, h6, p, label, input, textarea, select,
    .stMarkdown, .stText, .stButton, .stTextInput, .stSelectbox, .stTextArea,
    .stRadio, .stCheckbox, .stMetric, .stDataFrame, .stCaption {
        font-family: 'Montserrat', sans-serif !important;
    }
    
    /* Ensure Material Icons elements use the correct font */
    span[data-testid*="stIcon"],
    button span[class*="material"],
    [class*="material-icons"],
    [data-testid*="collapsedControl"] span,
    [data-testid="baseButton-header"] span {
        font-family: 'Material Symbols Outlined' !important;
    }

    </style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = 1
if "file_bytes" not in st.session_state:
    st.session_state.file_bytes = None
if "file_name" not in st.session_state:
    st.session_state.file_name = None
if "language" not in st.session_state:
    st.session_state.language = "en"
if "temp_path" not in st.session_state:
    st.session_state.temp_path = None
if "reader" not in st.session_state:
    st.session_state.reader = None
if "selected_sheet" not in st.session_state:
    st.session_state.selected_sheet = None
if "df" not in st.session_state:
    st.session_state.df = None
if "column_mappings" not in st.session_state:
    st.session_state.column_mappings = {}
if "column_descriptions" not in st.session_state:
    st.session_state.column_descriptions = {}
if "concept_definitions" not in st.session_state:
    st.session_state.concept_definitions = {}
if "suggestions_cache" not in st.session_state:
    st.session_state.suggestions_cache = {}
if "view_object" not in st.session_state:
    st.session_state.view_object = {}
if "general_details" not in st.session_state:
    st.session_state.general_details = {}
if "resource_name" not in st.session_state:
    st.session_state.resource_name = None
if "resource_name_confirmed" not in st.session_state:
    st.session_state.resource_name_confirmed = False
if "resource_name_accepted" not in st.session_state:
    st.session_state.resource_name_accepted = False
if "resource_name_editing" not in st.session_state:
    st.session_state.resource_name_editing = False


def render_sidebar_header():
    """Render the Trailpack branding block in the sidebar."""
    if LOGO_BASE64:
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1.5rem;">
                <img src="data:image/svg+xml;base64,{LOGO_BASE64}" alt="Trailpack logo"
                     style="width:56px;height:auto;" />
                <div style="display:flex;flex-direction:column;">
                    <span style="font-size:1.3rem;font-weight:600;line-height:1;">Trailpack</span>
                    <span style="font-size:0.95rem;color:#6b7280;line-height:1.2;">
                        Excel to PyST Mapper
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.title("Trailpack")
        st.markdown("### Excel to PyST Mapper")


def navigate_to(page: int):
    """Navigate to a specific page."""
    st.session_state.page = page
    st.session_state.scroll_to_top = True
    st.rerun()


def on_sheet_change():
    """Callback when sheet selection changes. Clears cached data."""
    # This runs BEFORE the page renders, so sidebar will show updated sheet name
    selected = st.session_state.get("sheet_radio")
    if selected and selected != st.session_state.selected_sheet:
        st.session_state.selected_sheet = selected
        st.session_state.suggestions_cache = {}
        st.session_state.column_mappings = {}
        st.session_state.view_object = {}


def load_excel_data(sheet_name: str) -> pd.DataFrame:
    """Load Excel data into a pandas DataFrame using SmartDataReader."""
    if st.session_state.temp_path is None:
        return None

    try:
        # Use SmartDataReader for optimized reading
        smart_reader = SmartDataReader(st.session_state.temp_path)

        # Store engine info in session state for display
        st.session_state.reader_engine = smart_reader.engine
        st.session_state.estimated_memory = smart_reader.estimate_memory()

        # Read data with optimal engine
        df = smart_reader.read(sheet_name=sheet_name)
        return df
    except Exception as e:
        st.error(f"Error loading Excel data: {e}")
        return None


async def fetch_suggestions_async(
    column_name: str, language: str
) -> List[Dict[str, str]]:
    """Fetch PyST suggestions for a column name."""
    try:
        client = get_suggest_client()
        suggestions = await client.suggest(column_name, language)

        # Debug: Log first suggestion structure to understand response format
        if suggestions and len(suggestions) > 0:
            import sys

            print(
                f"DEBUG - First suggestion keys: {suggestions[0].keys() if isinstance(suggestions[0], dict) else dir(suggestions[0])}",
                file=sys.stderr,
            )
            print(f"DEBUG - First suggestion: {suggestions[0]}", file=sys.stderr)

        return suggestions[:5]  # Limit to top 5
    except Exception as e:
        st.warning(f"Could not fetch suggestions for '{column_name}': {e}")
        return []


def fetch_suggestions_sync(column_name: str, language: str) -> List[Dict[str, str]]:
    """
    Synchronous wrapper for fetching suggestions.

    Handles event loop management for Streamlit compatibility.
    Creates a new event loop if needed to avoid "Event loop is closed" errors.
    """
    try:
        # Try to get the current event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                # Loop is closed, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            # No event loop exists, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run the async function
        return loop.run_until_complete(fetch_suggestions_async(column_name, language))

    except Exception as e:
        st.warning(f"Could not fetch suggestions for '{column_name}': {e}")
        return []


async def fetch_concept_async(iri: str, language: str) -> Optional[str]:
    """Fetch concept definition from PyST API."""
    try:
        client = get_suggest_client()
        concept = await client.get_concept(iri)
        
        # Extract SKOS definition
        # The response format is: "http://www.w3.org/2004/02/skos/core#definition": [{"@language": "en", "@value": "..."}]
        definitions = concept.get("http://www.w3.org/2004/02/skos/core#definition", [])
        
        if not definitions:
            return None
        
        # Try to find definition in the requested language
        for definition in definitions:
            if isinstance(definition, dict) and definition.get("@language") == language:
                return definition.get("@value")
        
        # Fallback: return first available definition
        if definitions and isinstance(definitions[0], dict):
            return definitions[0].get("@value")
        
        return None
    except Exception as e:
        import sys
        print(f"DEBUG - Error fetching concept {iri}: {e}", file=sys.stderr)
        return None


def fetch_concept_sync(iri: str, language: str) -> Optional[str]:
    """
    Synchronous wrapper for fetching concept definition.

    Handles event loop management for Streamlit compatibility.
    """
    try:
        # Try to get the current event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                # Loop is closed, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            # No event loop exists, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run the async function
        return loop.run_until_complete(fetch_concept_async(iri, language))

    except Exception as e:
        import sys
        print(f"DEBUG - Error in fetch_concept_sync for {iri}: {e}", file=sys.stderr)
        return None


def generate_view_object() -> Dict[str, Any]:
    """Generate the internal view object with all mappings."""
    if not st.session_state.selected_sheet or st.session_state.df is None:
        return {}

    # Create dataset name
    dataset_name = f"{Path(st.session_state.file_name).stem}_{st.session_state.selected_sheet.replace(' ', '_')}"

    # Build columns dict
    columns_dict = {}

    # Get column names from ExcelReader (source of truth)
    columns = st.session_state.reader.columns(st.session_state.selected_sheet)

    for column in columns:
        # Get sample values (first 10 non-null values)
        sample_values = (
            st.session_state.df[column].dropna().head(10).astype(str).tolist()
        )

        # Get suggestions from cache
        suggestions = st.session_state.suggestions_cache.get(column, [])

        # Normalize suggestions to ensure they have id and label keys
        normalized_suggestions = []
        for s in suggestions:
            try:
                if isinstance(s, dict):
                    s_id = (
                        s.get("id")
                        or s.get("id_")
                        or s.get("uri")
                        or s.get("concept_id")
                    )
                    s_label = s.get("label") or s.get("name") or s.get("title")
                else:
                    s_id = (
                        getattr(s, "id", None)
                        or getattr(s, "id_", None)
                        or getattr(s, "uri", None)
                    )
                    s_label = getattr(s, "label", None) or getattr(s, "name", None)

                if s_id and s_label:
                    normalized_suggestions.append(
                        {"id": str(s_id), "label": str(s_label)}
                    )
            except Exception:
                continue

        # Get selected mapping
        selected_id = st.session_state.column_mappings.get(column)
        selected_suggestion = None

        if selected_id:
            for s in normalized_suggestions:
                if s["id"] == selected_id:
                    selected_suggestion = {"label": s["label"], "id": s["id"]}
                    break

        columns_dict[column] = {
            "values": sample_values,
            "mapping_to_pyst": {
                "suggestions": normalized_suggestions,
                "selected": selected_suggestion if selected_suggestion else selected_id,
            },
        }

    # Build final view object
    view_object = {
        "sheet_name": st.session_state.selected_sheet,
        "dataset_name": dataset_name,
        "columns": columns_dict,
    }

    return view_object


# ===== SIDEBAR =====
with st.sidebar:
    render_sidebar_header()
    st.markdown("---")

    st.markdown("### Steps:")

    # Step indicators with icons
    if st.session_state.page >= 1:
        st.markdown(
            "**1. Upload & Select Language**"
            if st.session_state.page > 1
            else "> **1. Upload & Select Language**"
        )
    else:
        st.markdown("1. Upload & Select Language")

    if st.session_state.page >= 2:
        st.markdown(
            "**2. Select Sheet**"
            if st.session_state.page > 2
            else "> **2. Select Sheet**"
        )
    else:
        st.markdown("2. Select Sheet")

    if st.session_state.page >= 3:
        st.markdown(
            "**3. Map Columns**"
            if st.session_state.page > 3
            else "> **3. Map Columns**"
        )
    else:
        st.markdown("3. Map Columns")

    if st.session_state.page >= 4:
        st.markdown(
            "**4. General Details**"
            if st.session_state.page > 4
            else "> **4. General Details**"
        )
    else:
        st.markdown("4. General Details")

    if st.session_state.page >= 5:
        st.markdown("> **5. Review Parquet File**")
    else:
        st.markdown("5. Review Parquet File")

    st.markdown("---")

    # Show current file info if available
    if st.session_state.file_name:
        st.markdown("### Current File")
        st.info(f" {st.session_state.file_name}")
        if st.session_state.selected_sheet:
            st.info(f"****{st.session_state.selected_sheet}")


# ===== MAIN CONTENT =====

# Handle scroll to top after navigation
if st.session_state.get("scroll_to_top", False):
    st.markdown(
        """
        <script>
            // Scroll to top of the page
            var mainContent = window.parent.document.querySelector('section.main');
            if (mainContent) {
                mainContent.scrollTo(0, 0);
            }
            // Fallback: scroll the entire window
            window.parent.scrollTo(0, 0);
        </script>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.scroll_to_top = False

# Page 1: File Upload and Language Selection
if st.session_state.page == 1:
    st.title("Step 1: Upload File and Select Language")
    st.markdown(
        "Upload an Excel file and select the language for PyST concept mapping."
    )

    # Show current file if already uploaded
    if st.session_state.file_name:
        st.success(f"Current file: **{st.session_state.file_name}**")
        change_file = st.checkbox("Upload a different file", value=False)
    else:
        change_file = True

    # File upload
    uploaded_file = None
    if change_file or not st.session_state.file_name:
        uploaded_file = st.file_uploader(
            "Choose an Excel file",
            type=["xlsx", "xlsm", "xltx", "xltm"],
            help="Upload an Excel file to map its columns to PyST concepts",
        )

    # Language selection
    language = st.selectbox(
        "Select Language",
        options=sorted(list(SUPPORTED_LANGUAGES)),
        index=(
            sorted(list(SUPPORTED_LANGUAGES)).index("en")
            if "en" in SUPPORTED_LANGUAGES
            else 0
        ),
        help="Select the language for PyST concept suggestions",
    )

    st.session_state.language = language

    # Show file info if file exists
    if st.session_state.temp_path and st.session_state.temp_path.exists():
        file_size_mb = st.session_state.temp_path.stat().st_size / (1024 * 1024)
        st.info(
            f"**File:** {st.session_state.file_name} | **Size:** {file_size_mb:.2f} MB"
        )

    # Navigation
    col1, col2, col3 = st.columns([1, 1, 1])

    with col3:
        # Enable Next button if file exists
        has_file = uploaded_file is not None or st.session_state.file_name is not None

        if has_file:
            if st.button("Next ", type="primary", use_container_width=True):
                # Save file only if newly uploaded
                if uploaded_file is not None:
                    st.session_state.file_bytes = uploaded_file.getvalue()
                    st.session_state.file_name = uploaded_file.name

                    # Save to temp file
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".xlsx"
                    ) as tmp:
                        tmp.write(st.session_state.file_bytes)
                        st.session_state.temp_path = Path(tmp.name)

                    # Load Excel reader
                    try:
                        st.session_state.reader = ExcelReader(
                            st.session_state.temp_path
                        )
                    except Exception as e:
                        st.error(f"Error loading Excel file: {e}")
                        st.stop()

                navigate_to(2)
        else:
            st.button("Next ", type="primary", disabled=True, use_container_width=True, help="Please upload a file first")


# Page 2: Sheet Selection
elif st.session_state.page == 2:
    st.title("Step 2: Select Sheet")
    st.markdown(f"**File:** {st.session_state.file_name}")

    if st.session_state.reader:
        sheets = st.session_state.reader.sheets()

        st.markdown("Select the sheet you want to process:")

        # Get current index for default selection
        current_sheet = st.session_state.selected_sheet
        default_index = 0
        if current_sheet and current_sheet in sheets:
            default_index = sheets.index(current_sheet)

        selected_sheet = st.radio(
            "Available Sheets",
            options=sheets,
            index=default_index,
            key="sheet_radio",
            on_change=on_sheet_change,
            label_visibility="collapsed",
        )

        # Update session state if not already updated by callback
        if st.session_state.selected_sheet != selected_sheet:
            st.session_state.selected_sheet = selected_sheet

        # Show preview of the selected sheet
        if selected_sheet:
            st.markdown("### Data Preview")

            with st.spinner("Loading data preview..."):
                df = load_excel_data(selected_sheet)

                if df is not None:
                    st.session_state.df = df

                    # Show basic info
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Rows", len(df))
                    with col2:
                        # Use ExcelReader for column count (consistent source)
                        column_count = len(
                            st.session_state.reader.columns(selected_sheet)
                        )
                        st.metric("Columns", column_count)
                    with col3:
                        st.metric("Non-empty cells", df.notna().sum().sum())

                    # Show SmartDataReader engine info
                    if hasattr(st.session_state, "reader_engine") and hasattr(
                        st.session_state, "estimated_memory"
                    ):
                        st.caption(
                            f"**Engine:** {st.session_state.reader_engine} | "
                            f"**Est. Memory:** {st.session_state.estimated_memory}"
                        )

                    # Show first few rows
                    st.markdown("**First 10 rows:**")
                    st.dataframe(df.head(10), use_container_width=True)

    # Navigation
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("Back", use_container_width=True):
            navigate_to(1)

    with col3:
        if st.session_state.selected_sheet:
            if st.button("Next ", type="primary", use_container_width=True):
                navigate_to(3)
        else:
            st.button("Next ", type="primary", disabled=True, use_container_width=True)


# Page 3: Column Mapping
elif st.session_state.page == 3:
    st.title("Step 3: Map Columns to PyST Concepts")
    st.markdown(
        f"**File:** {st.session_state.file_name} | **Sheet:** {st.session_state.selected_sheet}"
    )

    if st.session_state.df is not None:
        # Show data preview at the top
        with st.expander("📊 View Data Preview", expanded=False):
            st.dataframe(st.session_state.df.head(20), use_container_width=True)

        st.markdown("### Column Mappings")
        st.markdown("Select a PyST concept for each column.")

        # Get column names from ExcelReader (consistent with sheet selection on Page 2)
        columns = st.session_state.reader.columns(st.session_state.selected_sheet)

        # Display column mappings in a clean table-like format
        st.markdown("---")

        for column in columns:
            with st.container():
                col1, col2 = st.columns([1, 2])

                with col1:
                    st.markdown(f"**{column}**")
                    # Show sample values
                    sample_values = (
                        st.session_state.df[column]
                        .dropna()
                        .head(3)
                        .astype(str)
                        .tolist()
                    )
                    if sample_values:
                        st.caption(f"Sample: {', '.join(sample_values[:3])}")

                with col2:
                    # Check if column is numeric
                    is_numeric = pd.api.types.is_numeric_dtype(
                        st.session_state.df[column]
                    )

                    # Ontology search field (for all columns)
                    search_query = st.text_input(
                        "Search for ontology",
                        key=f"search_{column}",
                        placeholder="Type and press Enter to search...",
                        label_visibility="visible",
                    )

                    # Fetch and display ontology suggestions
                    if search_query and len(search_query) >= 2:
                        cache_key = f"{column}_{search_query}"
                        if cache_key not in st.session_state.suggestions_cache:
                            suggestions = fetch_suggestions_sync(
                                search_query, st.session_state.language
                            )
                            st.session_state.suggestions_cache[cache_key] = suggestions[
                                :5
                            ]  # Limit to 5

                        # Show suggestions dropdown
                        suggestions = st.session_state.suggestions_cache.get(
                            cache_key, []
                        )
                        if suggestions:
                            valid_suggestions = []
                            for s in suggestions:
                                try:
                                    if isinstance(s, dict):
                                        s_id = (
                                            s.get("id")
                                            or s.get("id_")
                                            or s.get("uri")
                                            or s.get("concept_id")
                                        )
                                        s_label = (
                                            s.get("label")
                                            or s.get("name")
                                            or s.get("title")
                                        )
                                    else:
                                        s_id = (
                                            getattr(s, "id", None)
                                            or getattr(s, "id_", None)
                                            or getattr(s, "uri", None)
                                        )
                                        s_label = getattr(s, "label", None) or getattr(
                                            s, "name", None
                                        )
                                    if s_id and s_label:
                                        valid_suggestions.append(
                                            {"id": s_id, "label": s_label}
                                        )
                                except Exception:
                                    continue

                            if valid_suggestions:
                                options = [s["label"] for s in valid_suggestions]
                                option_ids = [s["id"] for s in valid_suggestions]

                                # Get current selection index
                                current_mapping = st.session_state.column_mappings.get(
                                    column
                                )
                                default_idx = 0
                                if current_mapping in option_ids:
                                    default_idx = option_ids.index(current_mapping)

                                selected = st.selectbox(
                                    "Select from results",
                                    options=options,
                                    index=default_idx,
                                    key=f"select_{column}",
                                    label_visibility="visible",
                                )

                                # Store selection
                                selected_idx = options.index(selected)
                                selected_id = option_ids[selected_idx]
                                selected_label = options[selected_idx]
                                st.session_state.column_mappings[column] = selected_id

                                # Fetch concept definition from API if not already cached
                                concept_cache_key = f"concept_{selected_id}"
                                if concept_cache_key not in st.session_state.concept_definitions:
                                    concept_definition = fetch_concept_sync(
                                        selected_id, st.session_state.language
                                    )
                                    if concept_definition:
                                        st.session_state.concept_definitions[concept_cache_key] = concept_definition

                                # Display selected concept with clickable link to web page
                                web_url = iri_to_web_url(
                                    selected_id, st.session_state.language
                                )
                                
                                # Get the definition to display
                                concept_definition = st.session_state.concept_definitions.get(concept_cache_key)
                                
                                col_info, col_clear = st.columns([4, 1])
                                with col_info:
                                    if concept_definition:
                                        st.info(
                                            f"**Selected:** {selected_label}\n\n"
                                            f"**Description:** {concept_definition}\n\n"
                                            f"[🔗 View on vocab.sentier.dev]({web_url})"
                                        )
                                    else:
                                        st.info(
                                            f"**Selected:** {selected_label}\n\n[🔗 View on vocab.sentier.dev]({web_url})"
                                        )
                                with col_clear:
                                    if st.button("Clear", key=f"clear_{column}", help="Remove ontology selection"):
                                        # Clear the ontology mapping
                                        st.session_state.column_mappings.pop(column, None)
                                        # Clear concept definition cache
                                        st.session_state.concept_definitions.pop(concept_cache_key, None)
                                        # Clear search field text by deleting the widget state
                                        search_key = f"search_{column}"
                                        if search_key in st.session_state:
                                            del st.session_state[search_key]
                                        # Clear all suggestions cache entries for this column
                                        cache_keys_to_remove = [k for k in st.session_state.suggestions_cache.keys() if k.startswith(f"{column}_")]
                                        for cache_key in cache_keys_to_remove:
                                            st.session_state.suggestions_cache.pop(cache_key, None)
                                        st.rerun()

                    # If numeric, show unit search field below ontology
                    if is_numeric:
                        # Unit search field
                        unit_search_query = st.text_input(
                            "Search for unit",
                            key=f"search_unit_{column}",
                            placeholder="Type and press Enter to search...",
                            label_visibility="visible",
                        )

                        # Fetch and display unit suggestions
                        if unit_search_query and len(unit_search_query) >= 2:
                            cache_key = f"{column}_unit_{unit_search_query}"
                            if cache_key not in st.session_state.suggestions_cache:
                                suggestions = fetch_suggestions_sync(
                                    unit_search_query, st.session_state.language
                                )
                                st.session_state.suggestions_cache[cache_key] = (
                                    suggestions[:5]
                                )

                            # Show unit suggestions dropdown
                            suggestions = st.session_state.suggestions_cache.get(
                                cache_key, []
                            )
                            if suggestions:
                                valid_suggestions = []
                                for s in suggestions:
                                    try:
                                        if isinstance(s, dict):
                                            s_id = (
                                                s.get("id")
                                                or s.get("id_")
                                                or s.get("uri")
                                                or s.get("concept_id")
                                            )
                                            s_label = (
                                                s.get("label")
                                                or s.get("name")
                                                or s.get("title")
                                            )
                                        else:
                                            s_id = (
                                                getattr(s, "id", None)
                                                or getattr(s, "id_", None)
                                                or getattr(s, "uri", None)
                                            )
                                            s_label = getattr(
                                                s, "label", None
                                            ) or getattr(s, "name", None)
                                        if s_id and s_label:
                                            valid_suggestions.append(
                                                {"id": s_id, "label": s_label}
                                            )
                                    except Exception:
                                        continue

                                if valid_suggestions:
                                    options = [s["label"] for s in valid_suggestions]
                                    option_ids = [s["id"] for s in valid_suggestions]

                                    # Get current selection index for unit
                                    current_unit_mapping = (
                                        st.session_state.column_mappings.get(
                                            f"{column}_unit"
                                        )
                                    )
                                    default_idx = 0
                                    if current_unit_mapping in option_ids:
                                        default_idx = option_ids.index(
                                            current_unit_mapping
                                        )

                                    selected = st.selectbox(
                                        "Select unit from results",
                                        options=options,
                                        index=default_idx,
                                        key=f"select_unit_{column}",
                                        label_visibility="visible",
                                    )

                                    # Store unit selection
                                    selected_idx = options.index(selected)
                                    selected_unit_id = option_ids[selected_idx]
                                    selected_unit_label = options[selected_idx]
                                    st.session_state.column_mappings[
                                        f"{column}_unit"
                                    ] = selected_unit_id

                                    # Fetch concept definition for unit from API if not already cached
                                    unit_concept_cache_key = f"concept_{selected_unit_id}"
                                    if unit_concept_cache_key not in st.session_state.concept_definitions:
                                        unit_concept_definition = fetch_concept_sync(
                                            selected_unit_id, st.session_state.language
                                        )
                                        if unit_concept_definition:
                                            st.session_state.concept_definitions[unit_concept_cache_key] = unit_concept_definition

                                    # Display selected unit with clickable link to web page
                                    web_url = iri_to_web_url(
                                        selected_unit_id, st.session_state.language
                                    )
                                    
                                    # Get the definition to display
                                    unit_concept_definition = st.session_state.concept_definitions.get(unit_concept_cache_key)
                                    
                                    col_unit_info, col_unit_clear = st.columns([4, 1])
                                    with col_unit_info:
                                        if unit_concept_definition:
                                            st.info(
                                                f"**Selected unit:** {selected_unit_label}\n\n"
                                                f"**Description:** {unit_concept_definition}\n\n"
                                                f"[🔗 View on vocab.sentier.dev]({web_url})"
                                            )
                                        else:
                                            st.info(
                                                f"**Selected unit:** {selected_unit_label}\n\n[🔗 View on vocab.sentier.dev]({web_url})"
                                            )
                                    with col_unit_clear:
                                        if st.button("Clear", key=f"clear_unit_{column}", help="Remove unit selection"):
                                            # Clear the unit mapping
                                            st.session_state.column_mappings.pop(f"{column}_unit", None)
                                            # Clear concept definition cache
                                            st.session_state.concept_definitions.pop(unit_concept_cache_key, None)
                                            # Clear unit search field text by deleting the widget state
                                            unit_search_key = f"search_unit_{column}"
                                            if unit_search_key in st.session_state:
                                                del st.session_state[unit_search_key]
                                            # Clear all unit suggestions cache entries for this column
                                            unit_cache_keys_to_remove = [k for k in st.session_state.suggestions_cache.keys() if k.startswith(f"{column}_unit_")]
                                            for cache_key in unit_cache_keys_to_remove:
                                                st.session_state.suggestions_cache.pop(cache_key, None)
                                            st.rerun()
                    
                    # Description field - show for all columns but with different requirements
                    has_ontology = st.session_state.column_mappings.get(column) is not None
                    
                    # Check if we have a concept definition from the API
                    concept_cache_key = f"concept_{st.session_state.column_mappings.get(column)}" if has_ontology else None
                    concept_definition = st.session_state.concept_definitions.get(concept_cache_key) if concept_cache_key else None
                    
                    # Show text area unless ontology has a description
                    if not (has_ontology and concept_definition):
                        # Determine if description is required or optional
                        if has_ontology and not concept_definition:
                            # Ontology selected but no API definition - description is optional
                            description_label = "Column Description (optional)"
                            description_help = "Optional: Add a custom description for this column. The selected ontology has no description available from the API."
                            is_required = False
                        else:
                            # No ontology selected - description is required
                            description_label = "Column Description *"
                            description_help = "Required: No ontology mapping selected. Please provide a description for this column."
                            is_required = True
                        
                        column_description = st.text_area(
                            description_label,
                            value=st.session_state.column_descriptions.get(column, ""),
                            placeholder="Describe what this column represents...",
                            help=description_help,
                            key=f"description_{column}",
                            height=80
                        )
                        
                        # Store description in session state
                        if column_description:
                            st.session_state.column_descriptions[column] = column_description
                        else:
                            st.session_state.column_descriptions.pop(column, None)
                        
                        # Show warning only if description is required and missing
                        if is_required and not column_description:
                            st.warning("Please provide either an ontology mapping or a description for this column.")

                st.markdown("---")

        # Generate view object internally (not displayed)
        st.session_state.view_object = generate_view_object()

        # Navigation and actions
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("Back", use_container_width=True):
                navigate_to(2)

        with col3:
            # Check if all columns have either ontology or description
            columns = st.session_state.reader.columns(st.session_state.selected_sheet)
            missing_info = []
            for column in columns:
                has_ontology = st.session_state.column_mappings.get(column) is not None
                has_description = bool(st.session_state.column_descriptions.get(column))
                
                # Check if we have a concept definition from the API
                concept_cache_key = f"concept_{st.session_state.column_mappings.get(column)}" if has_ontology else None
                has_concept_definition = bool(st.session_state.concept_definitions.get(concept_cache_key)) if concept_cache_key else False
                
                # Column is valid if:
                # 1. Has ontology with API definition (description not needed), OR
                # 2. Has ontology without API definition (description optional per requirements), OR
                # 3. Has no ontology but has manual description
                # Only invalid if missing BOTH ontology AND description
                if not has_ontology and not has_description:
                    # Missing both ontology and description
                    missing_info.append(column)
            
            can_proceed = len(missing_info) == 0
            
            if can_proceed:
                if st.button("Next ", type="primary", use_container_width=True):
                    # Generate view object internally (not displayed)
                    st.session_state.view_object = generate_view_object()
                    navigate_to(4)
            else:
                st.button("Next ", type="primary", disabled=True, use_container_width=True)
                st.error(f"The following columns need either an ontology mapping or a description: {', '.join(missing_info)}")


# Page 4: General Details
elif st.session_state.page == 4:
    st.title("Step 4: General Details")
    st.markdown("Provide metadata for your data package.")

    # Initialize schema
    schema = DataPackageSchema()

    # Get field definitions for the form
    field_defs = schema.field_definitions

    st.markdown("### Basic Information")

    # Package Name (required)
    name_field = field_defs.get("name", {})
    package_name = st.text_input(
        name_field.get("label", "Package Name") + " *",
        value=st.session_state.general_details.get("name", ""),
        placeholder=name_field.get("placeholder", ""),
        help=name_field.get("help", name_field.get("description", "")),
        key="input_name",
    )

    # Validate package name in real-time if not empty
    if package_name:
        is_valid, error_msg = schema.validate_package_name(package_name)
        if not is_valid:
            st.error(f"{error_msg}")
        else:
            st.session_state.general_details["name"] = package_name
    elif package_name == "":
        # Clear from session state if empty
        st.session_state.general_details.pop("name", None)

    # Title (required)
    title_field = field_defs.get("title", {})
    title = st.text_input(
        title_field.get("label", "Title") + " *",
        value=st.session_state.general_details.get("title", ""),
        placeholder=title_field.get("placeholder", ""),
        help=title_field.get("description", "") + " (Required)",
        key="input_title",
    )
    if title:
        st.session_state.general_details["title"] = title
    elif title == "":
        st.session_state.general_details.pop("title", None)

    # Description (optional)
    desc_field = field_defs.get("description", {})
    description = st.text_area(
        desc_field.get("label", "Description"),
        value=st.session_state.general_details.get("description", ""),
        placeholder=desc_field.get("placeholder", ""),
        help=desc_field.get("description", ""),
        key="input_description",
    )
    if description:
        st.session_state.general_details["description"] = description
    elif description == "":
        st.session_state.general_details.pop("description", None)

    # Version (optional)
    version_field = field_defs.get("version", {})
    version = st.text_input(
        version_field.get("label", "Version"),
        value=st.session_state.general_details.get("version", ""),
        placeholder=version_field.get("placeholder", ""),
        help=version_field.get("description", ""),
        key="input_version",
    )

    # Validate version if not empty
    if version:
        is_valid, error_msg = schema.validate_version(version)
        if not is_valid:
            st.error(f"{error_msg}")
        else:
            st.session_state.general_details["version"] = version
    elif version == "":
        st.session_state.general_details.pop("version", None)

    st.markdown("---")
    st.markdown("### 📝 Resource Name Configuration")
    st.markdown("""
The resource name identifies your data file in the package. It must follow specific naming rules:
- Only **lowercase letters** (a-z)
- **Numbers** (0-9)
- **Hyphens** (-), **underscores** (_), and **dots** (.)
- No spaces or special characters

**Example:** `solar-panel-data`, `emissions_2024`, `my.dataset.v1`
    """)
    
    # Initialize validator
    validator = StandardValidator()
    
    # Get original filename + sheet name and check validity
    if st.session_state.file_name and st.session_state.selected_sheet:
        # Combine filename and sheet name
        file_stem = Path(st.session_state.file_name).stem
        sheet_name = st.session_state.selected_sheet.replace(' ', '_')
        original_name = f"{file_stem}_{sheet_name}"
        is_valid_original, _, suggested_name = validator.validate_and_sanitize_resource_name(original_name)
        
        # Only show the error/suggestion if not yet accepted
        if not st.session_state.resource_name_accepted:
            # Show source file and sheet info
            st.info(f" **Source:** `{file_stem}` (file) + `{st.session_state.selected_sheet}` (sheet)")
            
            # Show original combined name with validation status
            if is_valid_original:
                st.success(f"**Combined name is valid:** `{original_name}`")
                # If valid and not set, use it
                if not st.session_state.resource_name:
                    st.session_state.resource_name = original_name
                    st.session_state.resource_name_accepted = True
            else:
                # Show the problem prominently
                st.error(f"**Combined name has issues:** `{original_name}`")
                
                st.warning("""
**Issues found:**
- Uppercase letters → converted to lowercase
- Spaces → replaced with underscores
- Special characters → removed
                """)
                
                # Check if we're in edit mode or display mode
                if not st.session_state.resource_name_editing:
                    # Display mode: show suggestion with Accept/buttons
                    st.markdown(f"**Suggested sanitized name:** `{suggested_name}`")
                    
                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        if st.button("Accept", use_container_width=True, type="primary", key="btn_accept_suggestion"):
                            st.session_state.resource_name = suggested_name
                            st.session_state.resource_name_confirmed = True
                            st.session_state.resource_name_accepted = True
                            st.session_state.resource_name_editing = False
                            st.session_state.general_details["resource_name"] = suggested_name
                            st.rerun()
                    with col2:
                        if st.button("Edit", use_container_width=True, key="btn_edit_suggestion"):
                            st.session_state.resource_name = suggested_name
                            st.session_state.resource_name_editing = True
                            st.rerun()
                else:
                    # mode: show text input with validation
                    resource_name_edit = st.text_input(
                        "Resource Name",
                        value=st.session_state.resource_name or suggested_name,
                        placeholder="my-data-resource",
                        help="the resource name. Must contain only lowercase letters, numbers, hyphens, underscores, and dots.",
                        key="resource_name_edit_suggestion"
                    )
                    
                    if resource_name_edit:
                        is_valid_edit, _, suggestion_edit = validator.validate_and_sanitize_resource_name(resource_name_edit)
                        
                        if is_valid_edit:
                            st.success(f"**`{resource_name_edit}`** is valid!")
                        else:
                            st.error(f"**`{resource_name_edit}`** contains invalid characters.")
                            st.markdown(f"**Suggested fix:** `{suggestion_edit}`")
                        
                        # Show buttons for editing
                        col1, col2, col3 = st.columns([1, 1, 2])
                        with col1:
                            if st.button("Accept", use_container_width=True, type="primary", key="btn_accept_edit", disabled=not is_valid_edit):
                                st.session_state.resource_name = resource_name_edit
                                st.session_state.resource_name_confirmed = True
                                st.session_state.resource_name_accepted = True
                                st.session_state.resource_name_editing = False
                                st.session_state.general_details["resource_name"] = resource_name_edit
                                st.rerun()
                        with col2:
                            if st.button("Cancel", use_container_width=True, key="btn_cancel_edit"):
                                st.session_state.resource_name_editing = False
                                st.rerun()
    
    # Show resource name input (either already accepted or for manual editing)
    # Only show input section if name has been accepted or is being manually entered
    if st.session_state.resource_name_accepted or st.session_state.resource_name:
        st.markdown("---")
        
        # If accepted, show as info with option to edit
        if st.session_state.resource_name_accepted and st.session_state.resource_name_confirmed:
            st.success(f"**Resource name:** `{st.session_state.resource_name}`")
            if st.button("Resource Name", key="btn_edit_resource_name"):
                st.session_state.resource_name_accepted = False
                st.session_state.resource_name_editing = False  # Reset editing flag
                st.rerun()
        else:
            # Resource name input with real-time validation
            resource_name_input = st.text_input(
                "Resource Name *",
                value=st.session_state.resource_name or "",
                placeholder="my-data-resource",
                help="Enter or edit the resource name. Must follow the naming rules above. (Required)",
                key="resource_name_input_meta"
            )
            
            # Validate the entered/edited name in real-time
            if resource_name_input:
                is_valid_input, _, suggestion = validator.validate_and_sanitize_resource_name(resource_name_input)
                
                if is_valid_input:
                    st.success(f"**`{resource_name_input}`** is a valid resource name!")
                    # Show accept button for valid name
                    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
                    with col_btn1:
                        if st.button("Accept", use_container_width=True, type="primary", key="btn_accept_manual"):
                            st.session_state.resource_name = resource_name_input
                            st.session_state.resource_name_confirmed = True
                            st.session_state.resource_name_accepted = True
                            st.session_state.general_details["resource_name"] = resource_name_input
                            st.rerun()
                    with col_btn2:
                        if st.button("Reset", help="Reset to sanitized filename + sheet", use_container_width=True, key="btn_reset"):
                            if st.session_state.file_name and st.session_state.selected_sheet:
                                file_stem = Path(st.session_state.file_name).stem
                                sheet_name = st.session_state.selected_sheet.replace(' ', '_')
                                original_name = f"{file_stem}_{sheet_name}"
                                st.session_state.resource_name = validator.sanitize_resource_name(original_name)
                                st.session_state.resource_name_accepted = False
                                st.rerun()
                else:
                    st.error(f"**`{resource_name_input}`** contains invalid characters.")
                    st.markdown(f"**Suggested fix:** `{suggestion}`")
                    
                    # Show buttons for invalid name
                    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
                    with col_btn1:
                        if st.button("Use Suggestion", use_container_width=True, type="primary", key="btn_use_suggestion"):
                            st.session_state.resource_name = suggestion
                            st.session_state.resource_name_accepted = True
                            st.session_state.resource_name_confirmed = True
                            st.session_state.general_details["resource_name"] = suggestion
                            st.rerun()
                    with col_btn2:
                        if st.button("Reset", help="Reset to sanitized filename + sheet", use_container_width=True, key="btn_reset_invalid"):
                            if st.session_state.file_name and st.session_state.selected_sheet:
                                file_stem = Path(st.session_state.file_name).stem
                                sheet_name = st.session_state.selected_sheet.replace(' ', '_')
                                original_name = f"{file_stem}_{sheet_name}"
                                st.session_state.resource_name = validator.sanitize_resource_name(original_name)
                                st.session_state.resource_name_accepted = False
                                st.rerun()
                    
                    st.session_state.resource_name_confirmed = False
                    st.session_state.general_details.pop("resource_name", None)
            else:
                st.session_state.resource_name_confirmed = False
                st.session_state.general_details.pop("resource_name", None)

    st.markdown("### Additional Information")

    # Profile (optional)
    profile_field = field_defs.get("profile", {})
    profile_options = profile_field.get("options", [])
    profile_labels = [opt["label"] for opt in profile_options]
    profile_values = [opt["value"] for opt in profile_options]

    current_profile = st.session_state.general_details.get(
        "profile", profile_field.get("default", "")
    )
    default_index = 0
    if current_profile in profile_values:
        default_index = profile_values.index(current_profile)

    profile_label = st.selectbox(
        profile_field.get("label", "Profile"),
        options=profile_labels,
        index=default_index,
        help=profile_field.get("description", ""),
        key="input_profile",
    )

    profile = profile_values[profile_labels.index(profile_label)]
    st.session_state.general_details["profile"] = profile

    # Keywords (optional)
    keywords_field = field_defs.get("keywords", {})
    keywords_str = st.text_input(
        keywords_field.get("label", "Keywords"),
        value=", ".join(st.session_state.general_details.get("keywords", [])),
        placeholder=keywords_field.get("placeholder", ""),
        help=(keywords_field.get("description") or "") + " (comma-separated)",
        key="input_keywords",
    )
    if keywords_str:
        keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
        st.session_state.general_details["keywords"] = keywords
    elif keywords_str == "":
        st.session_state.general_details.pop("keywords", None)

    # Homepage (optional)
    homepage_field = field_defs.get("homepage", {})
    homepage = st.text_input(
        homepage_field.get("label", "Homepage"),
        value=st.session_state.general_details.get("homepage", ""),
        placeholder=homepage_field.get("placeholder", ""),
        help=homepage_field.get("description", ""),
        key="input_homepage",
    )

    # Validate homepage if not empty
    if homepage:
        is_valid, error_msg = schema.validate_url(homepage)
        if not is_valid:
            st.error(f"{error_msg}")
        else:
            st.session_state.general_details["homepage"] = homepage
    elif homepage == "":
        st.session_state.general_details.pop("homepage", None)

    # Repository (optional)
    repository_field = field_defs.get("repository", {})
    repository = st.text_input(
        repository_field.get("label", "Repository"),
        value=st.session_state.general_details.get("repository", ""),
        placeholder=repository_field.get("placeholder", ""),
        help=repository_field.get("description", ""),
        key="input_repository",
    )

    # Validate repository if not empty
    if repository:
        is_valid, error_msg = schema.validate_url(repository)
        if not is_valid:
            st.error(f"{error_msg}")
        else:
            st.session_state.general_details["repository"] = repository
    elif repository == "":
        st.session_state.general_details.pop("repository", None)

    # Created date (optional, pre-filled with current date)
    created_field = field_defs.get("created", {})
    default_created = st.session_state.general_details.get(
        "created", datetime.now().strftime("%Y-%m-%d")
    )
    created = st.date_input(
        created_field.get("label", "Created Date"),
        value=(
            datetime.strptime(default_created, "%Y-%m-%d").date()
            if default_created
            else datetime.now().date()
        ),
        help=created_field.get("description", ""),
        key="input_created",
    )
    if created:
        st.session_state.general_details["created"] = created.strftime("%Y-%m-%d")

    # Modified date (optional)
    modified_field = field_defs.get("modified", {})
    # Get the stored value or None
    stored_modified = st.session_state.general_details.get("modified")
    modified_value = None
    if stored_modified:
        try:
            modified_value = datetime.strptime(stored_modified, "%Y-%m-%d").date()
        except:
            modified_value = None

    modified = st.date_input(
        modified_field.get("label", "Modified Date"),
        value=modified_value,
        help=modified_field.get("description", ""),
        key="input_modified",
    )
    if modified:
        st.session_state.general_details["modified"] = modified.strftime("%Y-%m-%d")
    elif not modified:
        st.session_state.general_details.pop("modified", None)

    st.markdown("### Licenses *")
    st.caption("At least one license is required")

    # License selection
    license_options = ["None"] + list(COMMON_LICENSES.keys()) + ["Custom"]
    current_licenses = st.session_state.general_details.get("licenses", [])

    # Display existing licenses
    if current_licenses:
        st.markdown("**Current Licenses:**")
        for idx, lic in enumerate(current_licenses):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text(
                    f"{lic.get('name', 'Unknown')} - {lic.get('title', 'No title')}"
                )
            with col2:
                if st.button("🗑️", key=f"delete_license_{idx}"):
                    current_licenses.pop(idx)
                    st.session_state.general_details["licenses"] = current_licenses
                    st.rerun()

    # Add new license
    st.markdown("**Add License:**")
    license_choice = st.selectbox(
        "Select a license",
        options=license_options,
        key="license_select",
        label_visibility="collapsed",
    )

    if license_choice != "None":
        if license_choice == "Custom":
            col1, col2 = st.columns(2)
            with col1:
                custom_license_name = st.text_input(
                    "License Name", key="custom_license_name", placeholder="MIT"
                )
            with col2:
                custom_license_title = st.text_input(
                    "License Title",
                    key="custom_license_title",
                    placeholder="MIT License",
                )
            custom_license_url = st.text_input(
                "License URL",
                key="custom_license_url",
                placeholder="https://opensource.org/licenses/MIT",
            )

            if st.button("Add Custom License"):
                if custom_license_name:
                    new_license = {
                        "name": custom_license_name,
                        "title": (
                            custom_license_title
                            if custom_license_title
                            else custom_license_name
                        ),
                        "path": custom_license_url if custom_license_url else None,
                    }
                    if "licenses" not in st.session_state.general_details:
                        st.session_state.general_details["licenses"] = []
                    st.session_state.general_details["licenses"].append(new_license)
                    st.rerun()
        else:
            if st.button(f"Add {license_choice}"):
                license_info = COMMON_LICENSES[license_choice]
                if "licenses" not in st.session_state.general_details:
                    st.session_state.general_details["licenses"] = []
                st.session_state.general_details["licenses"].append(license_info.copy())
                st.rerun()

    st.markdown("### Contributors *")
    st.caption("At least one contributor is required")

    # Display existing contributors
    current_contributors = st.session_state.general_details.get("contributors", [])
    if current_contributors:
        st.markdown("**Current Contributors:**")
        for idx, contrib in enumerate(current_contributors):
            col1, col2 = st.columns([4, 1])
            with col1:
                contrib_text = f"{contrib.get('name', 'Unknown')} ({contrib.get('role', 'contributor')})"
                if contrib.get("email"):
                    contrib_text += f" - {contrib['email']}"
                st.text(contrib_text)
            with col2:
                if st.button("🗑️", key=f"delete_contributor_{idx}"):
                    current_contributors.pop(idx)
                    st.session_state.general_details["contributors"] = (
                        current_contributors
                    )
                    st.rerun()

    # Add new contributor
    st.markdown("**Add Contributor:**")
    col1, col2 = st.columns(2)
    with col1:
        contrib_name = st.text_input("Name", key="contrib_name", placeholder="Jane Doe")
    with col2:
        contrib_role = st.selectbox(
            "Role",
            options=["author", "contributor", "maintainer", "publisher", "wrangler"],
            key="contrib_role",
        )

    col1, col2 = st.columns(2)
    with col1:
        contrib_email = st.text_input(
            "Email (optional)", key="contrib_email", placeholder="jane@example.com"
        )
    with col2:
        contrib_org = st.text_input(
            "Organization (optional)", key="contrib_org", placeholder="Example Org"
        )

    if st.button("Add Contributor"):
        if contrib_name:
            new_contributor = {"name": contrib_name, "role": contrib_role}
            if contrib_email:
                new_contributor["email"] = contrib_email
            if contrib_org:
                new_contributor["organization"] = contrib_org

            if "contributors" not in st.session_state.general_details:
                st.session_state.general_details["contributors"] = []
            st.session_state.general_details["contributors"].append(new_contributor)
            st.rerun()

    st.markdown("### Sources *")
    st.caption("At least one source is required")

    # Display existing sources
    current_sources = st.session_state.general_details.get("sources", [])
    if current_sources:
        st.markdown("**Current Sources:**")
        for idx, source in enumerate(current_sources):
            col1, col2 = st.columns([4, 1])
            with col1:
                source_text = f"{source.get('title', 'Unknown')}"
                if source.get("path"):
                    source_text += f" - {source['path']}"
                st.text(source_text)
            with col2:
                if st.button("🗑️", key=f"delete_source_{idx}"):
                    current_sources.pop(idx)
                    st.session_state.general_details["sources"] = current_sources
                    st.rerun()

    # Add new source
    st.markdown("**Add Source:**")
    source_title = st.text_input(
        "Source Title", key="source_title", placeholder="Original Dataset"
    )
    col1, col2 = st.columns(2)
    with col1:
        source_path = st.text_input(
            "Source URL (optional)",
            key="source_path",
            placeholder="https://example.com/data",
        )
    with col2:
        source_desc = st.text_input(
            "Source Description (optional)",
            key="source_desc",
            placeholder="Description of the source",
        )

    if st.button("Add Source"):
        if source_title:
            new_source = {"title": source_title}
            if source_path:
                new_source["path"] = source_path
            if source_desc:
                new_source["description"] = source_desc

            if "sources" not in st.session_state.general_details:
                st.session_state.general_details["sources"] = []
            st.session_state.general_details["sources"].append(new_source)
            st.rerun()

    # Check if required fields are filled (per DataPackageSchema.REQUIRED_FIELDS)
    # Required: name, title, resources (auto), licenses, created (auto), contributors, sources
    missing_fields = []

    if "name" not in st.session_state.general_details:
        missing_fields.append("Package Name")
    if "title" not in st.session_state.general_details:
        missing_fields.append("Title")
    if not st.session_state.general_details.get("licenses"):
        missing_fields.append("At least one License")
    if not st.session_state.general_details.get("contributors"):
        missing_fields.append("At least one Contributor")
    if not st.session_state.general_details.get("sources"):
        missing_fields.append("At least one Source")

    has_required_fields = len(missing_fields) == 0

    # Check if all filled fields are valid
    all_valid = True
    if "name" in st.session_state.general_details:
        is_valid, _ = schema.validate_package_name(
            st.session_state.general_details["name"]
        )
        all_valid = all_valid and is_valid
    if "version" in st.session_state.general_details:
        is_valid, _ = schema.validate_version(
            st.session_state.general_details["version"]
        )
        all_valid = all_valid and is_valid
    if "homepage" in st.session_state.general_details:
        is_valid, _ = schema.validate_url(
            st.session_state.general_details["homepage"]
        )
        all_valid = all_valid and is_valid
    if "repository" in st.session_state.general_details:
        is_valid, _ = schema.validate_url(
            st.session_state.general_details["repository"]
        )
        all_valid = all_valid and is_valid

    # Navigation
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("Back", use_container_width=True):
            navigate_to(3)

    with col3:
        if has_required_fields and all_valid:
            # Export section on page 4
            export_name = st.text_input(
                "Export file name",
                value=f"{st.session_state.general_details['name']}.parquet",
                help="Name for the exported Parquet file",
                key="export_filename",
            )

            if st.button(
                "📦 Generate Parquet File", type="primary", use_container_width=True
            ):
                with st.spinner("Building data package..."):
                    try:
                        from trailpack.packing.export_service import DataPackageExporter
                        from trailpack.packing.packing import read_parquet

                        exporter = DataPackageExporter(
                            df=st.session_state.df,
                            column_mappings=st.session_state.column_mappings,
                            general_details=st.session_state.general_details,
                            sheet_name=st.session_state.selected_sheet,
                            file_name=st.session_state.file_name,
                            suggestions_cache=st.session_state.suggestions_cache,
                        )

                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".parquet"
                        ) as tmp:
                            output_path, quality_level, validation_result = exporter.export(
                                tmp.name
                            )

                            # Store in session state for display
                            st.session_state.output_path = output_path
                            st.session_state.quality_level = quality_level
                            st.session_state.validation_result = validation_result
                            st.session_state.exporter = exporter
                            st.session_state.export_complete = True
                            st.session_state.export_name = export_name

                        # Navigate to page 5 to show results
                        navigate_to(5)

                    except Exception as e:
                        st.error(f"Export failed: {e}")
                        st.session_state.export_complete = False
        else:
            st.button(
                "📦 Generate Parquet File", type="primary", disabled=True, use_container_width=True
            )
            if not has_required_fields:
                st.caption(
                    f"Please fill in the required fields: {', '.join(missing_fields)}"
                )
            elif not all_valid:
                st.caption("Please fix validation errors in the form")


# Page 5: Review Parquet File
elif st.session_state.page == 5:
    st.title("Step 5: Review Parquet File")
    
    # Only show results if export is complete
    if st.session_state.get("export_complete", False):
        st.balloons()

        from trailpack.packing.packing import read_parquet

        # Read back the exported file
        exported_df, exported_metadata = read_parquet(st.session_state.output_path)

        # Display success message with quality level
        quality_level = st.session_state.get("quality_level", "VALID")
        st.success(
            f"Data package created successfully!\n\n**Validation Level:** {quality_level}"
        )

        # Display metadata in JSON format FIRST
        st.markdown("### Embedded Metadata")
        st.json(exported_metadata)

        # Display data sample SECOND
        st.markdown("### 📊 Data Sample (first 10 rows)")
        st.dataframe(exported_df.head(10), use_container_width=True)

        # Get export name from session state
        export_name = st.session_state.get("export_name", f"{st.session_state.general_details['name']}.parquet")

        # Offer download
        st.markdown("### Downloads")
        with open(st.session_state.output_path, "rb") as f:
            parquet_data = f.read()

        st.download_button(
            label="⬇️ Download Parquet File",
            data=parquet_data,
            file_name=export_name,
            mime="application/vnd.apache.parquet",
            use_container_width=True,
        )

        # Validation report download
        if st.session_state.get("validation_result") and st.session_state.get(
            "exporter"
        ):
            validation_report = (
                st.session_state.exporter.generate_validation_report(
                    st.session_state.validation_result
                )
            )

            report_filename = (
                f"{export_name.replace('.parquet', '')}_validation_report.txt"
            )

            st.download_button(
                label="Download Validation Report",
                data=validation_report,
                file_name=report_filename,
                mime="text/plain",
                use_container_width=True,
            )

        # Config downloads
        st.markdown("### Configuration Files")
        st.markdown(
            "Download reusable configuration files for reproducible processing"
        )

        # Build configs from session state
        mapping_config = build_mapping_config(
            column_mappings=st.session_state.column_mappings,
            file_name=st.session_state.file_name,
            sheet_name=st.session_state.selected_sheet,
            language=st.session_state.language,
        )

        metadata_config = build_metadata_config(
            general_details=st.session_state.general_details
        )

        # Generate filenames
        package_name = st.session_state.general_details.get("name")
        mapping_filename = generate_config_filename(
            config_type="mapping",
            package_name=package_name,
            file_name=st.session_state.file_name,
            sheet_name=st.session_state.selected_sheet,
        )
        metadata_filename = generate_config_filename(
            config_type="metadata",
            package_name=package_name,
            file_name=st.session_state.file_name,
        )

        # Download buttons in two columns
        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                label="Download Mapping Config",
                data=export_mapping_json(mapping_config),
                file_name=mapping_filename,
                mime="application/json",
                use_container_width=True,
                help="Column-to-ontology mappings for reuse with CLI or other datasets",
            )

        with col2:
            st.download_button(
                label="Download Metadata Config",
                data=export_metadata_json(metadata_config),
                file_name=metadata_filename,
                mime="application/json",
                use_container_width=True,
                help="Package metadata configuration for reproducible exports",
            )
    else:
        # If no export has been completed, show message and back button
        st.info("No parquet file has been generated yet. Please go back to page 4 and click 'Generate Parquet File'.")

    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("Back", use_container_width=True):
            navigate_to(4)


# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #888;">Trailpack - Excel to PyST Mapper</div>',
    unsafe_allow_html=True,
)
