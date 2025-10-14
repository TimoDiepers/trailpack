"""Main entry point for trailpack PyST client."""

import asyncio
from pathlib import Path
from trailpack.pyst.api.config import config
from trailpack.pyst.api.client import get_suggest_client
from trailpack.excel import ExcelReader


async def test_pyst_suggestions():
    """Test PyST API suggestions with multiple queries."""
    print("=" * 70)
    print("Testing PyST API Suggest Endpoint")
    print("=" * 70)

    # Test queries
    test_queries = [
        ("sustainability", "en"),
        ("carbon footprint", "en"),
        ("renewable energy", "en"),
    ]

    client = get_suggest_client()

    for query, language in test_queries:
        print(f"\nQuery: '{query}' (language: {language})")
        print("-" * 70)

        try:
            suggestions = await client.suggest(query, language)

            if suggestions:
                print(f"✅ Received {len(suggestions)} suggestions:")
                for i, concept in enumerate(suggestions[:5], 1):  # Show first 5
                    # Handle different response formats
                    if isinstance(concept, dict):
                        concept_id = concept.get('id') or concept.get('uri') or concept.get('concept_id', 'N/A')
                        concept_label = concept.get('label') or concept.get('name') or concept.get('title', 'N/A')
                        print(f"  {i}. {concept_label}")
                        print(f"     ID: {concept_id}")
                        print(f"     Keys: {list(concept.keys())}")
                    else:
                        print(f"  {i}. {concept}")
            else:
                print("⚠️  No suggestions returned")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


def test_excel_reader():
    """Test the Excel reader."""
    print("\n" + "=" * 70)
    print("Testing Excel Reader")
    print("=" * 70)

    excel_path = Path(__file__).parent / "data" / "Global-Energy-Ownership-Tracker-September-2025-V1.xlsx"

    if not excel_path.exists():
        print(f"❌ Test file not found: {excel_path}")
        return

    print(f"✅ File found: {excel_path.name}")
    print(f"   Size: {excel_path.stat().st_size / (1024*1024):.2f} MB")

    try:
        with ExcelReader(excel_path) as reader:
            sheets = reader.sheets()
            print(f"\n✅ Found {len(sheets)} sheets:")
            for i, sheet in enumerate(sheets[:5], 1):  # Show first 5
                print(f"  {i}. {sheet}")
                columns = reader.columns(sheet)
                print(f"     Columns: {len(columns)}")
                if columns:
                    print(f"     First 3: {', '.join(columns[:3])}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("PyST Configuration")
    print("=" * 70)
    print(f"Host: {config.host}")
    print(f"Auth Token: {'Set' if config.auth_token else 'Not set'}")
    print(f"Timeout: {config.timeout}s")

    # Test PyST API
    print("\n")

    # Create event loop properly
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Run async test
    loop.run_until_complete(test_pyst_suggestions())

    print("\n" + "=" * 70)
    print("Tests Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
