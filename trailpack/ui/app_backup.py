"""Main Panel UI application for trailpack."""

import asyncio
import io
from pathlib import Path
from typing import Dict, List, Optional, Any

import panel as pn
import openpyxl

from trailpack.excel import ExcelReader
from trailpack.pyst.api.requests.suggest import SUPPORTED_LANGUAGES
from trailpack.pyst.api.client import get_suggest_client

pn.extension()


class TrailpackUI:
    """
    Multi-page Panel application for Excel file processing with PyST integration.
    
    Flow:
    1. Page 1: Upload Excel file and select language
    2. Page 2: Select sheet from uploaded file
    3. Page 3: Map columns to PyST concepts
    """
    
    def __init__(self):
        """Initialize the UI application."""
        # State variables
        self.uploaded_file: Optional[bytes] = None
        self.file_name: Optional[str] = None
        self.selected_language: str = "en"
        self.excel_reader: Optional[ExcelReader] = None
        self.selected_sheet: Optional[str] = None
        self.temp_file_path: Optional[Path] = None
        self.view_object: Dict[str, Any] = {}
        
        # Current page
        self.current_page = 1
        
        # Initialize Panel components
        self._init_page1_components()
        self._init_page2_components()
        self._init_page3_components()
        
    def _init_page1_components(self):
        """Initialize Page 1 components: File upload and language selection."""
        self.file_input = pn.widgets.FileInput(
            accept=".xlsx,.xlsm,.xltx,.xltm",
            name="Upload Excel File",
            sizing_mode="stretch_width"
        )
        
        self.language_select = pn.widgets.Select(
            name="Select Language",
            options=sorted(list(SUPPORTED_LANGUAGES)),
            value="en",
            sizing_mode="stretch_width"
        )
        
        self.page1_next_button = pn.widgets.Button(
            name="Next",
            button_type="primary",
            disabled=True,
            sizing_mode="stretch_width"
        )
        
        # Set up callbacks
        self.file_input.param.watch(self._on_file_upload, "value")
        self.language_select.param.watch(self._on_language_change, "value")
        self.page1_next_button.on_click(self._go_to_page2)
        
    def _init_page2_components(self):
        """Initialize Page 2 components: Sheet selection."""
        self.sheet_select = pn.widgets.RadioButtonGroup(
            name="Select Sheet",
            options=[],
            sizing_mode="stretch_width"
        )
        
        self.page2_back_button = pn.widgets.Button(
            name="Back",
            button_type="default",
            sizing_mode="stretch_width"
        )
        
        self.page2_next_button = pn.widgets.Button(
            name="Next",
            button_type="primary",
            disabled=True,
            sizing_mode="stretch_width"
        )
        
        self.sheet_select.param.watch(self._on_sheet_select, "value")
        self.page2_back_button.on_click(self._go_to_page1)
        self.page2_next_button.on_click(self._go_to_page3)
        
    def _init_page3_components(self):
        """Initialize Page 3 components: Column mapping."""
        self.column_mapping_pane = pn.Column(sizing_mode="stretch_width")
        self.column_widgets: Dict[str, Dict[str, Any]] = {}
        
        self.page3_back_button = pn.widgets.Button(
            name="Back",
            button_type="default",
            sizing_mode="stretch_width"
        )
        
        self.page3_finish_button = pn.widgets.Button(
            name="Finish",
            button_type="success",
            sizing_mode="stretch_width"
        )
        
        self.result_json = pn.widgets.TextAreaInput(
            name="Result (JSON)",
            disabled=True,
            height=400,
            sizing_mode="stretch_width"
        )
        
        self.page3_back_button.on_click(self._go_to_page2_from_page3)
        self.page3_finish_button.on_click(self._on_finish)
        
    def _on_file_upload(self, event):
        """Handle file upload."""
        if event.new is not None:
            self.uploaded_file = event.new
            self.file_name = self.file_input.filename
            self.page1_next_button.disabled = False
        else:
            self.uploaded_file = None
            self.file_name = None
            self.page1_next_button.disabled = True
            
    def _on_language_change(self, event):
        """Handle language selection change."""
        self.selected_language = event.new
        
    def _go_to_page2(self, event=None):
        """Navigate to page 2 and load sheets."""
        if self.uploaded_file is None:
            return
            
        # Save uploaded file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(self.uploaded_file)
            self.temp_file_path = Path(tmp.name)
            
        # Load Excel file
        try:
            self.excel_reader = ExcelReader(self.temp_file_path)
            sheets = self.excel_reader.sheets()
            self.sheet_select.options = sheets
            if sheets:
                self.sheet_select.value = sheets[0]
            self.current_page = 2
            self._update_view()
        except Exception as e:
            pn.state.notifications.error(f"Error loading Excel file: {e}")
            
    def _on_sheet_select(self, event):
        """Handle sheet selection."""
        if event.new:
            self.selected_sheet = event.new
            self.page2_next_button.disabled = False
        else:
            self.selected_sheet = None
            self.page2_next_button.disabled = True
            
    def _go_to_page3(self, event=None):
        """Navigate to page 3 and prepare column mapping."""
        if self.selected_sheet is None or self.excel_reader is None:
            return
            
        self.current_page = 3
        self._update_view()
        
        # Load columns and get suggestions asynchronously
        self._load_column_mappings()
        
    def _load_column_mappings(self):
        """Load columns and fetch PyST suggestions."""
        if self.excel_reader is None or self.selected_sheet is None:
            return
            
        try:
            columns = self.excel_reader.columns(self.selected_sheet)
            
            # Get sample values for each column (read actual data)
            workbook = openpyxl.load_workbook(self.temp_file_path, read_only=True, data_only=True)
            sheet = workbook[self.selected_sheet]
            
            # Read header row
            header_row = self.excel_reader.header_row
            
            # Read sample data (up to 10 rows)
            column_data: Dict[str, List[str]] = {col: [] for col in columns}
            
            for i, row in enumerate(sheet.iter_rows(min_row=header_row + 1, values_only=True)):
                if i >= 10:  # Limit to 10 sample rows
                    break
                for j, value in enumerate(row):
                    if j < len(columns):
                        column_data[columns[j]].append(str(value) if value is not None else "")
                        
            workbook.close()
            
            # Create UI for each column
            self.column_mapping_pane.clear()
            self.column_widgets.clear()
            
            for column in columns:
                self._create_column_widget(column, column_data[column])
                
            # Fetch suggestions asynchronously for all columns
            pn.state.notifications.info("Fetching PyST suggestions for columns...")
            asyncio.create_task(self._fetch_all_suggestions(columns))
            
        except Exception as e:
            pn.state.notifications.error(f"Error loading columns: {e}")
            
    def _create_column_widget(self, column_name: str, sample_values: List[str]):
        """Create widget for a single column mapping."""
        # Create widgets
        column_header = pn.pane.Markdown(f"### {column_name}")
        
        sample_text = pn.pane.Markdown(
            f"**Sample values:** {', '.join(sample_values[:5]) if sample_values else 'No data'}"
        )
        
        suggestions_select = pn.widgets.Select(
            name="PyST Mapping",
            options={"Loading...": None},
            sizing_mode="stretch_width"
        )
        
        # Store widgets
        self.column_widgets[column_name] = {
            "header": column_header,
            "sample": sample_text,
            "select": suggestions_select,
            "values": sample_values,
            "suggestions": []
        }
        
        # Add to pane
        self.column_mapping_pane.append(
            pn.Card(
                column_header,
                sample_text,
                suggestions_select,
                title=column_name,
                collapsed=False,
                sizing_mode="stretch_width"
            )
        )
        
    async def _fetch_all_suggestions(self, columns: List[str]):
        """Fetch PyST suggestions for all columns."""
        client = get_suggest_client()
        
        for column in columns:
            try:
                suggestions = await client.suggest(column, self.selected_language)
                
                # Update the widget with suggestions
                widget_data = self.column_widgets[column]
                widget_data["suggestions"] = suggestions
                
                # Create options dict for select widget
                options = {f"{s['label']} (ID: {s['id']})": s['id'] for s in suggestions[:10]}
                if not options:
                    options = {"No suggestions found": None}
                    
                widget_data["select"].options = options
                if options:
                    widget_data["select"].value = list(options.values())[0]
                    
            except Exception as e:
                widget_data = self.column_widgets[column]
                widget_data["select"].options = {f"Error: {str(e)}": None}
                
        pn.state.notifications.success("PyST suggestions loaded!")
        
    def _go_to_page1(self, event=None):
        """Navigate back to page 1."""
        self.current_page = 1
        self._update_view()
        
    def _go_to_page2_from_page3(self, event=None):
        """Navigate back to page 2 from page 3."""
        self.current_page = 2
        self._update_view()
        
    def _on_finish(self, event=None):
        """Handle finish button click and generate view object."""
        self._generate_view_object()
        
    def _generate_view_object(self):
        """Generate the final view object with all mappings."""
        if self.file_name is None or self.selected_sheet is None:
            return
            
        # Create dataset name
        dataset_name = f"{Path(self.file_name).stem}_{self.selected_sheet.replace(' ', '_')}"
        
        # Build columns dict
        columns_dict = {}
        
        for column_name, widget_data in self.column_widgets.items():
            selected_id = widget_data["select"].value
            suggestions = widget_data["suggestions"]
            
            # Find the selected suggestion
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
        self.view_object = {
            "sheet_name": self.selected_sheet,
            "dataset_name": dataset_name,
            "columns": columns_dict
        }
        
        # Display as JSON
        import json
        self.result_json.value = json.dumps(self.view_object, indent=2)
        
        pn.state.notifications.success("View object generated!")
        
    def _update_view(self):
        """Update the displayed page."""
        # This will trigger a re-render
        pass
        
    def _get_page1(self):
        """Get Page 1 layout."""
        return pn.Column(
            pn.pane.Markdown("# Step 1: Upload File and Select Language"),
            pn.pane.Markdown("Upload an Excel file (.xlsx) and select the language for PyST concept mapping."),
            self.file_input,
            self.language_select,
            pn.Row(
                pn.Spacer(),
                self.page1_next_button,
                sizing_mode="stretch_width"
            ),
            sizing_mode="stretch_width"
        )
        
    def _get_page2(self):
        """Get Page 2 layout."""
        return pn.Column(
            pn.pane.Markdown("# Step 2: Select Sheet"),
            pn.pane.Markdown(f"**File:** {self.file_name}"),
            pn.pane.Markdown("Select the sheet you want to process:"),
            self.sheet_select,
            pn.Row(
                self.page2_back_button,
                pn.Spacer(),
                self.page2_next_button,
                sizing_mode="stretch_width"
            ),
            sizing_mode="stretch_width"
        )
        
    def _get_page3(self):
        """Get Page 3 layout."""
        return pn.Column(
            pn.pane.Markdown("# Step 3: Map Columns to PyST Concepts"),
            pn.pane.Markdown(f"**File:** {self.file_name} | **Sheet:** {self.selected_sheet}"),
            pn.pane.Markdown("Select PyST concept mappings for each column:"),
            self.column_mapping_pane,
            pn.Row(
                self.page3_back_button,
                pn.Spacer(),
                self.page3_finish_button,
                sizing_mode="stretch_width"
            ),
            self.result_json,
            sizing_mode="stretch_width"
        )
        
    def view(self):
        """Get the current page view."""
        if self.current_page == 1:
            return self._get_page1()
        elif self.current_page == 2:
            return self._get_page2()
        elif self.current_page == 3:
            return self._get_page3()
        else:
            return pn.Column("Invalid page")
            
    def serve(self, **kwargs):
        """Serve the application."""
        # Create a container for dynamic content
        content_area = pn.Column(sizing_mode="stretch_width")
        
        # Function to render current page
        def render_page():
            content_area.clear()
            content_area.append(self.view())
        
        # Override callbacks to trigger re-render
        def make_callback(original_method):
            def callback(event):
                original_method(event)
                render_page()
            return callback
        
        # Re-bind callbacks
        self.page1_next_button.param.unwatch_all()
        self.page2_back_button.param.unwatch_all()
        self.page2_next_button.param.unwatch_all()
        self.page3_back_button.param.unwatch_all()
        
        self.page1_next_button.on_click(make_callback(self._go_to_page2))
        self.page2_back_button.on_click(make_callback(self._go_to_page1))
        self.page2_next_button.on_click(make_callback(self._go_to_page3))
        self.page3_back_button.on_click(make_callback(self._go_to_page2_from_page3))
        
        # Initial render
        render_page()
        
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
        
        template.main.append(content_area)
        
        return template.show(**kwargs)


def create_app():
    """Create and return the Trailpack UI application."""
    ui = TrailpackUI()
    
    # Create a reactive wrapper that watches the current_page
    @pn.depends(ui.param.current_page, watch=True)
    def update_view():
        return ui.view()
    
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
    
    # Add dynamic content
    def get_current_view():
        return ui.view()
    
    template.main.append(get_current_view)
    
    return ui, template


if __name__ == "__main__":
    ui = TrailpackUI()
    ui.serve(port=5006, show=True)
