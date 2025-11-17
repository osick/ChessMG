#!/usr/bin/env python3
"""
Example of using the tablebase search functionality.

Demonstrates searching for positions with specific properties.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'chessmg' / 'tablebase'))

from indexing_v2 import MaterialSignature, PositionIndexer
from storage import TablebaseStorage, PositionValue


def create_sample_tablebase():
    """Create a small sample tablebase for testing."""
    print("Creating sample KvK tablebase for testing...")

    material = MaterialSignature.from_pieces([5], [5])
    indexer = PositionIndexer(material)

    # Create storage
    storage_path = Path('./sample_KvK.cmgtb')
    storage = TablebaseStorage(
        storage_path,
        material,
        indexer.max_index(),
        mode='w'
    )

    # Manually mark some positions for testing
    # Mark a few as checkmate
    for i in range(10):
        storage.set_value(i, PositionValue.HELPMATE_IN_1)

    # Mark some as helpmate-in-3
    for i in range(10, 30):
        storage.set_value(i, PositionValue.HELPMATE_IN_3)

    # Mark some as draw
    for i in range(100, 200):
        storage.set_value(i, PositionValue.DRAW)

    # Rest remain UNKNOWN (will be marked ILLEGAL)
    for i in range(200, min(1000, indexer.max_index())):
        storage.set_value(i, PositionValue.ILLEGAL)

    storage.close()
    print(f"Sample tablebase created: {storage_path}")
    print(f"  10 positions: HELPMATE_IN_1")
    print(f"  20 positions: HELPMATE_IN_3")
    print(f"  100 positions: DRAW")

    return storage_path


def search_examples():
    """Run example searches."""
    from search_tablebase import TablebaseSearcher

    # Create sample tablebase
    tb_path = create_sample_tablebase()

    material = MaterialSignature.from_pieces([5], [5])
    searcher = TablebaseSearcher(tb_path, material)

    print("\n" + "="*70)
    print("Example Searches")
    print("="*70)

    # Example 1: Find helpmate-in-1
    print("\n1. Search for helpmate-in-1 positions:")
    results = searcher.search(dtm=1, position_type="helpmate", max_results=5)
    print(f"   Found {len(results)} positions")
    for r in results[:3]:
        print(f"   - Index {r.index}: {r.fen}")

    # Example 2: Find helpmate-in-3
    print("\n2. Search for helpmate-in-3 positions:")
    results = searcher.search(dtm=3, position_type="helpmate", max_results=5)
    print(f"   Found {len(results)} positions")
    for r in results[:3]:
        print(f"   - Index {r.index}: {r.fen}")

    # Example 3: Find draws
    print("\n3. Search for draw positions:")
    results = searcher.search(position_type="draw", max_results=5)
    print(f"   Found {len(results)} positions")
    for r in results[:3]:
        print(f"   - Index {r.index}: {r.fen}")

    # Example 4: Get statistics
    print("\n4. Tablebase statistics:")
    stats = searcher.get_statistics()
    for key, value in stats.items():
        if value > 0:
            print(f"   {key}: {value}")

    searcher.close()

    # Cleanup
    tb_path.unlink()
    print(f"\nCleaned up sample tablebase")


if __name__ == '__main__':
    search_examples()
