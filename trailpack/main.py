"""Main entry point for trailpack PyST client."""

import asyncio
from pathlib import Path
from trailpack.pyst.api.config import config
from trailpack.pyst.api.client import get_suggest_client
from trailpack.excel import ExcelReader


def test_excel_reader():
    """Test the Excel reader."""
    excel_path = Path(__file__).parent / "data" / "Global-Energy-Ownership-Tracker-September-2025-V1.xlsx"

    print(f"\nTesting Excel Reader (Memory-Efficient):")
    print(f"  File: {excel_path.name}")
    print(f"  Size: {excel_path.stat().st_size / (1024*1024):.2f} MB")
    print(f"  Note: Only loading sheet structure, not data")

    # string, list<strng>
    sheet_columns_dict = {}
    
    try:
        with ExcelReader(excel_path) as reader:
            # Get all sheets
            sheets = reader.sheets()
            print(f"\n  Sheets ({len(sheets)} found):")
            for i, sheet in enumerate(sheets, 1):
                print(f"    {i}. {sheet}")
                # fill sheet_columns_dict
                sheet_columns_dict[sheet] = reader.columns(sheet)

            # string, list<string>
            column_name_pyst_suggestion = {}
            # choose a sheet All Entities and run suggest for each column name
            target_sheet = "All Entities"
            if target_sheet in sheets:
                columns = reader.columns(target_sheet)
                print(f"\n  Columns in '{target_sheet}' ({len(columns)} found):")
                for i, column in enumerate(columns, 1):
                    print(f"    {i}. {column}")
                    column_name_pyst_suggestion[column] = None  # placeholder

                # Now run suggest for each column name and load to dictionary first 10 suggestions
                print(f"\n  Running PyST suggest for each column name in '{target_sheet}':")
                client = get_suggest_client()
                for column in columns:
                    try:
                        suggestions = asyncio.run(client.suggest(column, "en"))
                        column_name_pyst_suggestion[column] = suggestions[0:10]  # first 10 suggestions
                        
                        print(f"    Suggestions for '{column}': {len(suggestions)} found")
                        for s in suggestions[0:10]:
                            print(f"      - {s.get('label')} (ID: {s.get('id')})")
                    except Exception as e:
                        print(f"    Error suggesting for '{column}': {e}")
                
        print(f"\nCompleted Excel Reader test.")

    except Exception as e:
        print(f"\n  Error: {e}")


def main():
    """Main entry point for the application."""
    print(f"PyST Configuration:")
    print(f"  Host: {config.host}")
    print(f"  Auth Token: {'Set' if config.auth_token else 'Not set'}")
    print(f"  Timeout: {config.timeout}s")

    # Test Excel reader
    print("\n" + "="*60)
    test_excel_reader()

    # Test suggest endpoint
    print("\n" + "="*60)

    return config


if __name__ == "__main__":
    main()
