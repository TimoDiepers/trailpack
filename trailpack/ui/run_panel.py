#!/usr/bin/env python
"""Script to run the Trailpack Panel UI."""

import sys
from pathlib import Path

# This script should be run from the repository root
# Usage: python trailpack/ui/run_panel.py

if __name__ == "__main__":
    import subprocess
    
    # Get the path to the panel app
    app_path = Path(__file__).parent / "panel_app.py"
    
    print("Starting Trailpack Panel UI...")
    print(f"App path: {app_path}")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    # Run panel serve
    subprocess.run([
        sys.executable, "-m", "panel", "serve",
        str(app_path),
        "--port", "5006",
        "--show"
    ])
