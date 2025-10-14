"""Streamlit UI application for trailpack - Excel to PyST mapper."""

import asyncio
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

import streamlit as st
import pandas as pd
import openpyxl

from trailpack.excel import ExcelReader
from trailpack.pyst.api.requests.suggest import SUPPORTED_LANGUAGES
from trailpack.pyst.api.client import get_suggest_client


# Page configuration

st.set_page_config(
    page_title="Trailpack - Excel to PyST Mapper",
    page_icon="🎒",
    layout="wide",
    initial_sidebar_state="expanded"
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
if "suggestions_cache" not in st.session_state:
    st.session_state.suggestions_cache = {}
if "view_object" not in st.session_state:
    st.session_state.view_object = {}


def navigate_to(page: int):
    """Navigate to a specific page."""
    st.session_state.page = page
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
    """Load Excel data into a pandas DataFrame."""
    if st.session_state.temp_path is None:
        return None
    
    try:
        df = pd.read_excel(
            st.session_state.temp_path,
            sheet_name=sheet_name,
            header=0
        )
        return df
    except Exception as e:
        st.error(f"Error loading Excel data: {e}")
        return None


async def fetch_suggestions_async(column_name: str, language: str) -> List[Dict[str, str]]:
    """Fetch PyST suggestions for a column name."""
    try:
        client = get_suggest_client()
        suggestions = await client.suggest(column_name, language)

        # Debug: Log first suggestion structure to understand response format
        if suggestions and len(suggestions) > 0:
            import sys
            print(f"DEBUG - First suggestion keys: {suggestions[0].keys() if isinstance(suggestions[0], dict) else dir(suggestions[0])}",
                  file=sys.stderr)
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
        sample_values = st.session_state.df[column].dropna().head(10).astype(str).tolist()
        
        # Get suggestions from cache
        suggestions = st.session_state.suggestions_cache.get(column, [])

        # Normalize suggestions to ensure they have id and label keys
        normalized_suggestions = []
        for s in suggestions:
            try:
                if isinstance(s, dict):
                    s_id = s.get('id') or s.get('uri') or s.get('concept_id')
                    s_label = s.get('label') or s.get('name') or s.get('title')
                else:
                    s_id = getattr(s, 'id', None) or getattr(s, 'uri', None)
                    s_label = getattr(s, 'label', None) or getattr(s, 'name', None)

                if s_id and s_label:
                    normalized_suggestions.append({'id': str(s_id), 'label': str(s_label)})
            except Exception:
                continue

        # Get selected mapping
        selected_id = st.session_state.column_mappings.get(column)
        selected_suggestion = None

        if selected_id:
            for s in normalized_suggestions:
                if s['id'] == selected_id:
                    selected_suggestion = {"label": s['label'], "id": s['id']}
                    break

        columns_dict[column] = {
            "values": sample_values,
            "mapping_to_pyst": {
                "suggestions": normalized_suggestions,
                "selected": selected_suggestion if selected_suggestion else selected_id
            }
        }
    
    # Build final view object
    view_object = {
        "sheet_name": st.session_state.selected_sheet,
        "dataset_name": dataset_name,
        "columns": columns_dict
    }
    
    return view_object


# ===== SIDEBAR =====
with st.sidebar:
    st.title("🎒 Trailpack")
    st.markdown("### Excel to PyST Mapper")
    st.markdown("---")
    
    st.markdown("### Steps:")

    # Step indicators with icons
    if st.session_state.page >= 1:
        st.markdown("✅ **1. Upload & Select Language**" if st.session_state.page > 1 else "▶️ **1. Upload & Select Language**")
    else:
        st.markdown("⬜ 1. Upload & Select Language")

    if st.session_state.page >= 2:
        st.markdown("✅ **2. Select Sheet**" if st.session_state.page > 2 else "▶️ **2. Select Sheet**")
    else:
        st.markdown("⬜ 2. Select Sheet")

    if st.session_state.page >= 3:
        st.markdown("▶️ **3. Map Columns**")
    else:
        st.markdown("⬜ 3. Map Columns")
    
    st.markdown("---")
    
    # Show current file info if available
    if st.session_state.file_name:
        st.markdown("### Current File")
        st.info(f"📄 {st.session_state.file_name}")
        if st.session_state.selected_sheet:
            st.info(f"📋 Sheet: {st.session_state.selected_sheet}")


# ===== MAIN CONTENT =====

# Page 1: File Upload and Language Selection
if st.session_state.page == 1:
    st.title("Step 1: Upload File and Select Language")
    st.markdown("Upload an Excel file and select the language for PyST concept mapping.")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose an Excel file",
        type=["xlsx", "xlsm", "xltx", "xltm"],
        help="Upload an Excel file to map its columns to PyST concepts"
    )
    
    # Language selection
    language = st.selectbox(
        "Select Language",
        options=sorted(list(SUPPORTED_LANGUAGES)),
        index=sorted(list(SUPPORTED_LANGUAGES)).index("en") if "en" in SUPPORTED_LANGUAGES else 0,
        help="Select the language for PyST concept suggestions"
    )
    
    st.session_state.language = language
    
    # Navigation
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col3:
        if uploaded_file is not None:
            if st.button("Next ➡️", type="primary", use_container_width=True):
                # Save file
                st.session_state.file_bytes = uploaded_file.getvalue()
                st.session_state.file_name = uploaded_file.name
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                    tmp.write(st.session_state.file_bytes)
                    st.session_state.temp_path = Path(tmp.name)
                
                # Load Excel reader
                try:
                    st.session_state.reader = ExcelReader(st.session_state.temp_path)
                    navigate_to(2)
                except Exception as e:
                    st.error(f"Error loading Excel file: {e}")
        else:
            st.button("Next ➡️", type="primary", disabled=True, use_container_width=True)


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
            label_visibility="collapsed"
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
                        column_count = len(st.session_state.reader.columns(selected_sheet))
                        st.metric("Columns", column_count)
                    with col3:
                        st.metric("Non-empty cells", df.notna().sum().sum())
                    
                    # Show first few rows
                    st.markdown("**First 10 rows:**")
                    st.dataframe(df.head(10), use_container_width=True)
    
    # Navigation
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            navigate_to(1)
    
    with col3:
        if st.session_state.selected_sheet:
            if st.button("Next ➡️", type="primary", use_container_width=True):
                navigate_to(3)
        else:
            st.button("Next ➡️", type="primary", disabled=True, use_container_width=True)


# Page 3: Column Mapping
elif st.session_state.page == 3:
    st.title("Step 3: Map Columns to PyST Concepts")
    st.markdown(f"**File:** {st.session_state.file_name} | **Sheet:** {st.session_state.selected_sheet}")
    
    if st.session_state.df is not None:
        # Show data preview at the top
        with st.expander("📊 View Data Preview", expanded=False):
            st.dataframe(st.session_state.df.head(20), use_container_width=True)
        
        st.markdown("### Column Mappings")
        st.markdown("Select a PyST concept for each column. Suggestions are generated automatically based on column names.")

        # Get column names from ExcelReader (consistent with sheet selection on Page 2)
        columns = st.session_state.reader.columns(st.session_state.selected_sheet)
        
        # Fetch suggestions for all columns if not already cached
        if not st.session_state.suggestions_cache:
            with st.spinner("Fetching PyST suggestions for all columns..."):
                progress_bar = st.progress(0)
                for idx, column in enumerate(columns):
                    if column not in st.session_state.suggestions_cache:
                        suggestions = fetch_suggestions_sync(column, st.session_state.language)
                        st.session_state.suggestions_cache[column] = suggestions
                    progress_bar.progress((idx + 1) / len(columns))
                progress_bar.empty()
                st.success("✅ Suggestions loaded!")
        
        # Display column mappings in a clean table-like format
        st.markdown("---")
        
        for column in columns:
            with st.container():
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown(f"**{column}**")
                    # Show sample values
                    sample_values = st.session_state.df[column].dropna().head(3).astype(str).tolist()
                    if sample_values:
                        st.caption(f"Sample: {', '.join(sample_values[:3])}")
                
                with col2:
                    suggestions = st.session_state.suggestions_cache.get(column, [])

                    if suggestions:
                        # Filter out invalid suggestions and create options
                        # Handle both dict-like and object-like suggestion formats
                        valid_suggestions = []
                        for s in suggestions:
                            try:
                                # Try to get id and label with different access methods
                                if isinstance(s, dict):
                                    s_id = s.get('id') or s.get('uri') or s.get('concept_id')
                                    s_label = s.get('label') or s.get('name') or s.get('title')
                                else:
                                    s_id = getattr(s, 'id', None) or getattr(s, 'uri', None)
                                    s_label = getattr(s, 'label', None) or getattr(s, 'name', None)

                                if s_id and s_label:
                                    valid_suggestions.append({'id': s_id, 'label': s_label})
                            except Exception:
                                # Skip suggestions we can't parse
                                continue

                        if valid_suggestions:
                            # Create options for selectbox
                            options = ["(No mapping)"] + [f"{s['label']} (ID: {s['id']})" for s in valid_suggestions]
                            option_ids = [None] + [s['id'] for s in valid_suggestions]
                        else:
                            # No valid suggestions found
                            st.warning(f"No valid suggestions for '{column}'")
                            st.session_state.column_mappings[column] = None
                            valid_suggestions = []
                            options = ["(No mapping)"]
                            option_ids = [None]
                        
                        # Get current selection
                        current_value = st.session_state.column_mappings.get(column)
                        default_index = 0
                        if current_value and current_value in option_ids:
                            default_index = option_ids.index(current_value)
                        
                        selected_option = st.selectbox(
                            f"PyST Mapping for {column}",
                            options=options,
                            index=default_index,
                            key=f"mapping_{column}",
                            label_visibility="collapsed"
                        )
                        
                        # Store the selected ID
                        selected_idx = options.index(selected_option)
                        st.session_state.column_mappings[column] = option_ids[selected_idx]
                    else:
                        st.warning("No suggestions available")
                        st.session_state.column_mappings[column] = None
                
                st.markdown("---")
        
        # Generate view object internally (not displayed)
        st.session_state.view_object = generate_view_object()
        
        # Navigation and actions
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("⬅️ Back", use_container_width=True):
                navigate_to(2)
        
        with col3:
            if st.button("✅ Finish", type="primary", use_container_width=True):
                st.success("✅ Column mappings completed!")
                st.balloons()
                
                # Show completion message
                st.info("Mappings have been saved internally. The view object is available for further processing.")
                
                # Optional: Show a summary
                with st.expander("📝 Mapping Summary"):
                    mapped_count = sum(1 for v in st.session_state.column_mappings.values() if v is not None)
                    st.metric("Columns Mapped", f"{mapped_count} / {len(columns)}")
                    
                    # Show which columns are mapped
                    for col, mapping_id in st.session_state.column_mappings.items():
                        if mapping_id:
                            suggestions = st.session_state.suggestions_cache.get(col, [])
                            mapping_label = next((s['label'] for s in suggestions if s['id'] == mapping_id), mapping_id)
                            st.markdown(f"- **{col}** → {mapping_label}")
                        else:
                            st.markdown(f"- **{col}** → *(No mapping)*")


# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #888;">Trailpack - Excel to PyST Mapper</div>',
    unsafe_allow_html=True
)
