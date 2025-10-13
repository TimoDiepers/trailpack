"""Main entry point for trailpack PyST client."""

import asyncio
from trailpack.pyst.api.config import config
from trailpack.pyst.api.client import get_suggest_client


async def test_suggest():
    """Test the suggest endpoint."""
    query, language = ("capac", "en")

    print(f"\nTesting suggest endpoint:")
    print(f"  Query: {query}")
    print(f"  Language: {language}")

    client = get_suggest_client()

    try:
        results = await client.suggest(query, language)
        print(f"\nResults ({len(results)} found):")
        for i, result in enumerate(results[:5], 1):  # Show first 5
            print(f"  {i}. {result}")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        await client.close()


def main():
    """Main entry point for the application."""
    print(f"PyST Configuration:")
    print(f"  Host: {config.host}")
    print(f"  Auth Token: {'Set' if config.auth_token else 'Not set'}")
    print(f"  Timeout: {config.timeout}s")

    # Test suggest endpoint
    asyncio.run(test_suggest())

    return config


if __name__ == "__main__":
    main()
