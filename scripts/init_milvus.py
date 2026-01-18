#!/usr/bin/env python3
"""Initialize Milvus collections with sample data."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from oceanus_agent.config.settings import settings
from oceanus_agent.services.milvus_service import MilvusService


def main() -> None:
    """Initialize Milvus collections."""
    print("Initializing Milvus collections...")

    try:
        # Create service (this will create collections if they don't exist)
        milvus_service = MilvusService(settings.milvus)

        # Get collection stats
        stats = milvus_service.get_collection_stats()

        print("\nCollection Statistics:")
        for name, info in stats.items():
            print(f"  {name}: {info['num_entities']} entities")

        print("\nMilvus initialization complete!")
        print("\nNote: Collections are empty. To populate the knowledge base:")
        print("  1. Manually add historical cases using the insert_case() method")
        print("  2. Add Flink documentation using the insert_doc() method")
        print("  3. Let the agent auto-accumulate high-confidence diagnoses")

        milvus_service.close()

    except Exception as e:
        print(f"Error initializing Milvus: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
