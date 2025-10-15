Simplified Architecture: Local-First Data Quality Tool

  What It Really Is:

  ┌──────────────────────────────────────────────────────────┐
  │  Black/Prettier     →  Code Formatting                   │
  │  Pytest/Jest        →  Code Testing                      │
  │  ESLint/Flake8      →  Code Linting                      │
  │                                                          |
  │  TRAILPACK          →  Dataset Standardization           │
  └──────────────────────────────────────────────────────────┘

  The Complete Flow:

  YOU (Researcher)
      ↓
  1. pip install trailpack (or download .exe)
      ↓
  2. trailpack ui  (starts local Streamlit)
      ↓
  3. Drag & drop your Excel file
      ↓
  4. Human picks ontology mappings (mental process)
      ↓
  5. Fill metadata form
      ↓
  6. VALIDATE against standard ✓
      ↓
  7. Export: my-dataset.parquet
      ↓
  8. You manually submit to → Open Databank / Journal / Repository
      ↓
  DONE! ✅

  No Servers Needed (Unless You Want):

  | Deployment        | Use Case                        | Requirements               |
  |-------------------|---------------------------------|----------------------------|
  | Desktop App       | Single user on laptop           | Nothing! Just double-click |
  | Python Install    | pip install trailpack           | Python 3.9+                |
  | Docker (optional) | Team wants shared instance      | Docker only                |
  | Server (optional) | Institution wants internal tool | Any server                 |

⏺ Simplified Project Structure:

  trailpack/
  ├── __init__.py
  ├── cli.py                    # CLI interface
  │
  ├── ui/
  │   └── streamlit_app.py      # Already exists ✓
  │
  ├── excel/
  │   └── reader.py             # Already exists ✓
  │
  ├── pyst/
  │   └── api/
  │       └── client.py         # Already exists ✓
  │
  ├── packing/
  │   ├── datapackage_schema.py # Already exists ✓
  │   ├── export_service.py     # Already exists ✓
  │   └── packing.py            # Already exists ✓
  │
  ├── validation/
  │   ├── __init__.py
  │   ├── standard_validator.py # NEW - validate against standard
  │   └── standards/
  │       └── v1.0.0.yaml       # NEW - the standard definition
  │
  └── configs/
      └── templates/            # Example mapping configs
          ├── electricity.json
          ├── chemicals.json
          └── README.md

  CLI Interface:

  # Install
  pip install trailpack

  # Start UI (existing Streamlit)
  trailpack ui
  # → Opens browser at localhost:8501

  # CLI mode (for power users)
  trailpack process \
    --data inventory.xlsx \
    --sheet "Sheet1" \
    --mapping mapping.json \
    --metadata metadata.json \
    --output clean-data.parquet

  # Validate only (dry-run)
  trailpack validate \
    --data inventory.xlsx \
    --mapping mapping.json \
    --metadata metadata.json

  # Create config template from UI session
  trailpack export-config \
    --session-id abc123 \
    --output ./configs/

  # Initialize new project
  trailpack init my-dataset
  # Creates:
  #   my-dataset/
  #   ├── data/
  #   ├── configs/
  #   └── README.md

  # Check standard compliance
  trailpack check my-dataset.parquet
  # Output:
  #   ✓ Metadata complete
  #   ✓ All columns mapped
  #   ✓ Data quality passed
  #   → Quality Level: GOLD ⭐

⏺ Installation Options (Zero Friction):

  Option 1: Python Package (Easiest)

  # Install from PyPI
  pip install trailpack

  # Run
  trailpack ui

  # That's it! No configuration needed.

  Option 2: Standalone Desktop App

  # Download for your OS (using PyInstaller)
  # macOS
  curl -L https://github.com/trailpack/releases/trailpack-macos.zip -o trailpack.zip
  unzip trailpack.zip
  ./Trailpack.app

  # Windows
  # Download trailpack-windows.exe
  # Double-click to run

  # Linux
  curl -L https://github.com/trailpack/releases/trailpack-linux -o trailpack
  chmod +x trailpack
  ./trailpack

  Option 3: Docker (Optional, for Teams)

  # One-liner
  docker run -p 8501:8501 -v $(pwd)/data:/data trailpack/trailpack

  # Access at localhost:8501

  Option 4: From Source (Developers)

  git clone https://github.com/brightway-lca/trailpack
  cd trailpack
  pip install -e .
  trailpack ui

  What Gets Removed (Simplification):

  | Component        | Current Plan       | Simplified                       |
  |------------------|--------------------|----------------------------------|
  | Database         | PostgreSQL + Redis | ❌ Not needed (file-based)        |
  | REST API         | FastAPI server     | ❌ Optional add-on only           |
  | GraphQL          | Complex schema     | ❌ Not needed                     |
  | Celery Workers   | Background tasks   | ❌ Not needed (sync is fine)      |
  | MinIO/S3         | Object storage     | ❌ Local filesystem               |
  | Central Registry | Federation layer   | ❌ Out of scope (external system) |
  | Multi-user Auth  | User management    | ❌ Single-user tool               |

  What Stays (Core Value):

  | Component         | Purpose                      | Status          |
  |-------------------|------------------------------|-----------------|
  | Streamlit UI      | Interactive ontology mapping | ✅ Already works |
  | PyST Client       | Get ontology suggestions     | ✅ Already works |
  | Excel Reader      | Load data                    | ✅ Already works |
  | Export Service    | Build data package           | ✅ Already works |
  | Packing           | Write Parquet                | ✅ Already works |
  | StandardValidator | Validate against rules       | 🔲 Need to add  |
  | CLI               | Power user interface         | 🔲 Need to add  |
  | Config Export     | Save mapping templates       | 🔲 Need to add  |

⏺ Final Architecture: Open Source Data Quality Tool

  ┌──────────────────────────────────────────────────────────────┐
  │                    LOCAL LAPTOP / SERVER                     │
  │                                                              │
  │  ┌────────────────────────────────────────────────────────┐  │
  │  │  TRAILPACK (Python Package)                            │  │
  │  │                                                        │  │
  │  │  ┌──────────────┐      ┌──────────────┐                │  │
  │  │  │  UI Mode     │      │  CLI Mode    │                │  │
  │  │  │  (Streamlit) │      │  (typer)     │                │  │
  │  │  └──────────────┘      └──────────────┘                │  │
  │  │         │                      │                       │  │
  │  │         └──────────┬───────────┘                       │  │
  │  │                    ↓                                   │  │
  │  │         ┌─────────────────────┐                        │  │
  │  │         │  Core Pipeline      │                        │  │
  │  │         │  - Load data        │                        │  │
  │  │         │  - PyST enrich      │                        │  │
  │  │         │  - Validate         │                        │  │
  │  │         │  - Export Parquet   │                        │  │
  │  │         └─────────────────────┘                        │  │
  │  │                    ↓                                   │  │
  │  │         ┌─────────────────────┐                        │  │
  │  │         │  Local Filesystem   │                        │  │
  │  │         │  - uploads/         │                        │  │
  │  │         │  - exports/         │                        │  │
  │  │         │  - configs/         │                        │  │
  │  │         └─────────────────────┘                        │  │
  │  └────────────────────────────────────────────────────────┘  │
  │                                                              │
  │  Output: clean-data.parquet ✓                                │
  └──────────────────────────────────────────────────────────────┘
                           ↓
                User manually submits to
                           ↓
  ┌──────────────────────────────────────────────────────────────┐
  │          EXTERNAL SYSTEMS (Not Trailpack's Job)              │
  │                                                              │
  │  - Open Databank (peer review, DOI assignment)               │
  │  - Journal Submission Systems                                │
  │  - Institutional Repositories                                │
  │  - Zenodo / Figshare / Dryad                                 │
  └──────────────────────────────────────────────────────────────┘

  Current State vs. Target State:

  | Feature                     | Status  | Priority |
  |-----------------------------|---------|----------|
  | ✅ Streamlit UI              | Working | Done    |
  | ✅ Excel loading             | Working | Done    |
  | ✅ PyST ontology mapping     | Working | Done    |
  | ✅ Metadata form             | Working | Done    |
  | ✅ Parquet export            | Working | Done    |
  | ✅ Data preview              | Working | Done    |
  | 🔲 StandardValidator        | Missing | HIGH     |
  | 🔲 Config export (JSON)     | Missing | HIGH     |
  | 🔲 CLI interface            | Missing | Medium   |
  | 🔲 Desktop app packaging    | Missing | Medium   |
  | 🔲 Config templates library | Missing | Low      |

  Immediate Next Steps (Implementation Priority):

  1. Add StandardValidator (Critical)

  # Enforce submission standards
  validator = StandardValidator("v1.0.0")
  is_valid, errors, quality = validator.validate_all(df, metadata, mappings)

  if not is_valid:
      st.error(f"Cannot export: {errors}")
  else:
      st.success(f"✅ Quality Level: {quality}")

  2. Add Config Export (Critical)

  # After successful export, download config templates
  st.download_button("📋 Download Mapping Template", mapping_json)
  st.download_button("📄 Download Metadata Template", metadata_json)

  3. Add CLI (Nice to have)

  trailpack process --data file.xlsx --config mapping.json

  4. Package for Distribution (Polish)

  # PyPI
  pip install trailpack

  # Standalone
  brew install trailpack  # macOS
  choco install trailpack # Windows

  ---
  The Vision (Complete):

  Trailpack is like Git for code, but for data:

  - Git: Makes code version-controlled → GitHub accepts it
  - Black: Makes code formatted → PRs pass CI
  - Pytest: Makes code tested → Releases are safe
  - Trailpack: Makes data standardized → Open Databank accepts it

  100% open source, runs anywhere, no commercial aspect, just helps you prepare clean data.