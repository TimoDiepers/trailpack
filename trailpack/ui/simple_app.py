"""Simple Panel UI application for trailpack - working version."""

import asyncio
import io
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any

import panel as pn
import openpyxl

from trailpack.excel import ExcelReader
from trailpack.pyst.api.requests.suggest import SUPPORTED_LANGUAGES
from trailpack.pyst.api.client import get_suggest_client

pn.extension(notifications=True)


def create_app():
    """Create and return the Trailpack UI application."""
    
    # State variables
    state = {
        "page": 1,
        "file_bytes": None,
        "file_name": None,
        "language": "en",
        "temp_path": None,
        "reader": None,
        "selected_sheet": None,
        "columns": [],
        "column_data": {},
        "column_widgets": {},
        "view_object": {}
    }
    
    # ===== PAGE 1: File Upload and Language Selection =====
    file_input = pn.widgets.FileInput(
        accept=".xlsx,.xlsm,.xltx,.xltm",
        name="Upload Excel File",
        sizing_mode="stretch_width"
    )
    
    language_select = pn.widgets.Select(
        name="Select Language",
        options=sorted(list(SUPPORTED_LANGUAGES)),
        value="en",
        sizing_mode="stretch_width"
    )
    
    page1_next = pn.widgets.Button(
        name="Next",
        button_type="primary",
        disabled=True,
        sizing_mode="stretch_width"
    )
    
    page1 = pn.Column(
        pn.pane.Markdown("# Step 1: Upload File and Select Language"),
        pn.pane.Markdown("Upload an Excel file (.xlsx) and select the language for PyST concept mapping."),
        file_input,
        language_select,
        pn.Row(pn.Spacer(), page1_next, sizing_mode="stretch_width"),
        sizing_mode="stretch_width"
    )
    
    # ===== PAGE 2: Sheet Selection =====
    sheet_info = pn.pane.Markdown("")
    sheet_select = pn.widgets.RadioButtonGroup(
        name="Select Sheet",
        options=[],
        sizing_mode="stretch_width"
    )
    
    page2_back = pn.widgets.Button(
        name="Back",
        button_type="default",
        sizing_mode="stretch_width"
    )
    
    page2_next = pn.widgets.Button(
        name="Next",
        button_type="primary",
        disabled=True,
        sizing_mode="stretch_width"
    )
    
    page2 = pn.Column(
        pn.pane.Markdown("# Step 2: Select Sheet"),
        sheet_info,
        pn.pane.Markdown("Select the sheet you want to process:"),
        sheet_select,
        pn.Row(page2_back, pn.Spacer(), page2_next, sizing_mode="stretch_width"),
        sizing_mode="stretch_width",
        visible=False
    )
    
    # ===== PAGE 3: Column Mapping =====
    column_info = pn.pane.Markdown("")
    column_mapping_area = pn.Column(sizing_mode="stretch_width")
    
    page3_back = pn.widgets.Button(
        name="Back",
        button_type="default",
        sizing_mode="stretch_width"
    )
    
    page3_finish = pn.widgets.Button(
        name="Generate View Object",
        button_type="success",
        sizing_mode="stretch_width"
    )
    
    result_json = pn.widgets.TextAreaInput(
        name="Result (JSON)",
        disabled=True,
        height=300,
        sizing_mode="stretch_width"
    )
    
    page3 = pn.Column(
        pn.pane.Markdown("# Step 3: Map Columns to PyST Concepts"),
        column_info,
        pn.pane.Markdown("Select PyST concept mappings for each column:"),
        column_mapping_area,
        pn.Row(page3_back, pn.Spacer(), page3_finish, sizing_mode="stretch_width"),
        result_json,
        sizing_mode="stretch_width",
        visible=False
    )
    
    # ===== CALLBACKS =====
    
    def on_file_upload(event):
        """Handle file upload."""
        if event.new is not None:
            state["file_bytes"] = event.new
            state["file_name"] = file_input.filename
            page1_next.disabled = False
        else:
            state["file_bytes"] = None
            state["file_name"] = None
            page1_next.disabled = True
    
    def on_language_change(event):
        """Handle language change."""
        state["language"] = event.new
    
    def go_to_page2(event):
        """Navigate to page 2."""
        if state["file_bytes"] is None:
            return
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(state["file_bytes"])
            state["temp_path"] = Path(tmp.name)
        
        # Load Excel file
        try:
            state["reader"] = ExcelReader(state["temp_path"])
            sheets = state["reader"].sheets()
            
            # Update UI
            sheet_info.object = f"**File:** {state['file_name']}"
            sheet_select.options = sheets
            if sheets:
                sheet_select.value = sheets[0]
                state["selected_sheet"] = sheets[0]
                page2_next.disabled = False
            
            # Show page 2
            page1.visible = False
            page2.visible = True
            page3.visible = False
            state["page"] = 2
            
        except Exception as e:
            pn.state.notifications.error(f"Error loading Excel file: {e}")
    
    def on_sheet_select(event):
        """Handle sheet selection."""
        if event.new:
            state["selected_sheet"] = event.new
            page2_next.disabled = False
    
    def go_to_page3(event):
        """Navigate to page 3."""
        if state["selected_sheet"] is None or state["reader"] is None:
            return
        
        # Update info
        column_info.object = f"**File:** {state['file_name']} | **Sheet:** {state['selected_sheet']}"
        
        # Load columns and sample data
        try:
            columns = state["reader"].columns(state["selected_sheet"])
            state["columns"] = columns
            
            # Read sample data
            workbook = openpyxl.load_workbook(state["temp_path"], read_only=True, data_only=True)
            sheet = workbook[state["selected_sheet"]]
            header_row = state["reader"].header_row
            
            # Get sample values for each column
            column_data = {col: [] for col in columns}
            for i, row in enumerate(sheet.iter_rows(min_row=header_row + 1, values_only=True)):
                if i >= 10:
                    break
                for j, value in enumerate(row):
                    if j < len(columns):
                        column_data[columns[j]].append(str(value) if value is not None else "")
            
            workbook.close()
            state["column_data"] = column_data
            
            # Create column widgets
            column_mapping_area.clear()
            state["column_widgets"] = {}
            
            for column in columns:
                sample_values = column_data[column]
                sample_text = ', '.join(sample_values[:5]) if sample_values else 'No data'
                
                suggestions_select = pn.widgets.Select(
                    name="PyST Mapping",
                    options={"Loading...": None},
                    sizing_mode="stretch_width"
                )
                
                state["column_widgets"][column] = {
                    "select": suggestions_select,
                    "values": sample_values,
                    "suggestions": []
                }
                
                card = pn.Card(
                    pn.pane.Markdown(f"**Sample values:** {sample_text}"),
                    suggestions_select,
                    title=column,
                    collapsed=False,
                    sizing_mode="stretch_width"
                )
                
                column_mapping_area.append(card)
            
            # Show page 3
            page1.visible = False
            page2.visible = False
            page3.visible = True
            state["page"] = 3
            
            # Fetch suggestions asynchronously
            pn.state.notifications.info("Fetching PyST suggestions for columns...")
            asyncio.create_task(fetch_suggestions(columns))
            
        except Exception as e:
            pn.state.notifications.error(f"Error loading columns: {e}")
    
    async def fetch_suggestions(columns):
        """Fetch PyST suggestions for all columns."""
        client = get_suggest_client()
        
        for column in columns:
            try:
                suggestions = await client.suggest(column, state["language"])
                
                # Update widget
                widget_data = state["column_widgets"][column]
                widget_data["suggestions"] = suggestions
                
                # Create options
                options = {f"{s['label']} (ID: {s['id']})": s['id'] for s in suggestions[:10]}
                if not options:
                    options = {"No suggestions found": None}
                
                widget_data["select"].options = options
                if options:
                    widget_data["select"].value = list(options.values())[0]
                
            except Exception as e:
                widget_data = state["column_widgets"][column]
                widget_data["select"].options = {f"Error: {str(e)}": None}
        
        pn.state.notifications.success("PyST suggestions loaded!")
    
    def go_back_to_page1(event):
        """Navigate back to page 1."""
        page1.visible = True
        page2.visible = False
        page3.visible = False
        state["page"] = 1
    
    def go_back_to_page2(event):
        """Navigate back to page 2."""
        page1.visible = False
        page2.visible = True
        page3.visible = False
        state["page"] = 2
    
    def generate_view_object(event):
        """Generate the final view object."""
        if state["file_name"] is None or state["selected_sheet"] is None:
            return
        
        # Create dataset name
        dataset_name = f"{Path(state['file_name']).stem}_{state['selected_sheet'].replace(' ', '_')}"
        
        # Build columns dict
        columns_dict = {}
        
        for column_name, widget_data in state["column_widgets"].items():
            selected_id = widget_data["select"].value
            suggestions = widget_data["suggestions"]
            
            # Find selected suggestion
            selected_suggestion = None
            if selected_id:
                for s in suggestions:
                    if s['id'] == selected_id:
                        selected_suggestion = {"label": s['label'], "id": s['id']}
                        break
            
            columns_dict[column_name] = {
                "values": widget_data["values"],
                "mapping_to_pyst": {
                    "suggestions": [
                        {"label": s['label'], "id": s['id']}
                        for s in suggestions[:10]
                    ],
                    "selected": selected_suggestion if selected_suggestion else selected_id
                }
            }
        
        # Build final view object
        state["view_object"] = {
            "sheet_name": state["selected_sheet"],
            "dataset_name": dataset_name,
            "columns": columns_dict
        }
        
        # Display as JSON
        result_json.value = json.dumps(state["view_object"], indent=2)
        
        pn.state.notifications.success("View object generated!")
    
    # Connect callbacks
    file_input.param.watch(on_file_upload, "value")
    language_select.param.watch(on_language_change, "value")
    page1_next.on_click(go_to_page2)
    
    sheet_select.param.watch(on_sheet_select, "value")
    page2_back.on_click(go_back_to_page1)
    page2_next.on_click(go_to_page3)
    
    page3_back.on_click(go_back_to_page2)
    page3_finish.on_click(generate_view_object)
    
    # Create template
    template = pn.template.FastListTemplate(
        title="Trailpack - Excel to PyST Mapper",
        sidebar=[
            pn.pane.Markdown("## Trailpack UI"),
            pn.pane.Markdown("Map Excel columns to PyST concepts"),
            pn.pane.Markdown("---"),
            pn.pane.Markdown("### Steps:"),
            pn.pane.Markdown("1. Upload file & select language"),
            pn.pane.Markdown("2. Select sheet"),
            pn.pane.Markdown("3. Map columns"),
        ]
    )
    
    template.main.append(page1)
    template.main.append(page2)
    template.main.append(page3)
    
    return template


if __name__ == "__main__":
    app = create_app()
    pn.serve(app, port=5006, show=True, title="Trailpack UI")
elif __name__.startswith('bokeh'):
    # For panel serve command
    create_app().servable()
