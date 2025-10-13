"""Standalone script to run the Trailpack UI."""

import sys
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

import panel as pn
from trailpack.ui.app import TrailpackUI

# Enable Panel extension
pn.extension(notifications=True)

# Create the UI
ui = TrailpackUI()

# Create a servable app that dynamically updates based on current_page
def create_servable():
    """Create a servable Panel application."""
    
    # Create a container for the content
    content = pn.Column(sizing_mode="stretch_width")
    
    # Function to update content based on current page
    def update_content():
        content.clear()
        content.append(ui.view())
    
    # Initial content
    update_content()
    
    # Watch for changes (hack: we'll trigger updates through button callbacks)
    # Store original button callbacks
    original_page1_next = ui.page1_next_button.on_click
    original_page2_back = ui.page2_back_button.on_click
    original_page2_next = ui.page2_next_button.on_click
    original_page3_back = ui.page3_back_button.on_click
    
    # Override button callbacks to also update content
    def wrap_callback(original_callback):
        def wrapper(*args, **kwargs):
            result = original_callback(*args, **kwargs)
            update_content()
            return result
        return wrapper
    
    # We need to re-set the callbacks since on_click returns None
    ui.page1_next_button.on_click(lambda e: (ui._go_to_page2(e), update_content()))
    ui.page2_back_button.on_click(lambda e: (ui._go_to_page1(e), update_content()))
    ui.page2_next_button.on_click(lambda e: (ui._go_to_page3(e), update_content()))
    ui.page3_back_button.on_click(lambda e: (ui._go_to_page2_from_page3(e), update_content()))
    
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
    
    template.main.append(content)
    
    return template

# Create and serve the app
app = create_servable()

if __name__ == "__main__":
    pn.serve(app, port=5006, show=True, title="Trailpack UI")
elif __name__.startswith('bokeh'):
    # For panel serve command
    app.servable()
