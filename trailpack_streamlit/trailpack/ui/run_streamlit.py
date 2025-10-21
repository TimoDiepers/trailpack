#!/usr/bin/env python
"""Script to run the Trailpack Streamlit UI."""

import sys
from pathlib import Path

# This script should be run from the repository root
# Usage: python trailpack/ui/run_streamlit.py

if __name__ == "__main__":
    import subprocess
    
    # Get the path to the streamlit app
    app_path = Path(__file__).parent / "streamlit_app.py"
    
    print("Starting Trailpack Streamlit UI...")
    print(f"App path: {app_path}")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    # Run streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.port", "8501",
        "--server.headless", "true"
    ])
