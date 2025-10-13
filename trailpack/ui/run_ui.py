#!/usr/bin/env python
"""CLI script to run the Trailpack UI."""

import sys
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

import panel as pn
from trailpack.ui import create_app

if __name__ == "__main__":
    print("Starting Trailpack UI...")
    print("The UI will open in your browser at http://localhost:5006")
    print("Press Ctrl+C to stop the server")
    
    app = create_app()
    pn.serve(app, port=5006, show=False, title="Trailpack UI")
