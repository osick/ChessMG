#!/usr/bin/env python3
"""
Basic tests for the tablebase system.

Tests:
1. Material signature creation
2. Position indexing (encode/decode)
3. Storage operations
4. Basic generation (small tablebase)
"""

import sys
from pathlib import Path
import tempfile
import shutil

from tablebase import (
    MaterialSignature,
    PositionIndexer,
    TablebaseStorage,
    PositionValue,
    TablebaseGenerator,
    TablebaseProbe
)


def test_material_signature():
    """Test material signature creation and validation."""
    print("\n" + "="*70)
    print("Test 1: Material Signature")
    print("="*70)

    # Valid signatures
    try:
        kvk = MaterialSignature.from_pieces([5], [5])
        print(f"✓ KvK: {kvk}")

        kpk = MaterialSignature.from_pieces([5, 0], [5])
        print(f"✓ KPvK: {kpk}")

        kqkr = MaterialSignature.from_pieces([5, 4], [5, 3])
        print(f"✓ KQvKR: {kqkr}")

        print("\n✓ All valid signatures created successfully")

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    # Invalid signatures (no king)
    try:
        invalid = MaterialSignature.from_pieces([0], [5])
        print(f"✗ Should have failed: {invalid}")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected no white king: {e}")

    return True


def test_position_indexing():
    """Test position indexing encode/decode."""
    print("\n" + "="*70)
    print("Test 2: Position Indexing")
    print("="*70)

    # KvK indexing
    material = MaterialSignature.from_pieces([5], [5])
    indexer = PositionIndexer(material)

    print(f"Material: {material}")
    print(f"Max positions: {indexer.max_index():,}")

    # Test encode/decode for several positions
    test_cases = [
        ([0], [63]),    # Corners
        ([0], [1]),     # Adjacent
        ([32], [40]),   # Center
        ([27], [35]),   # Center
    ]

    for white_sq, black_sq in test_cases:
        try:
            # Encode
            index = indexer.encode(white_sq, black_sq)

            # Decode
            decoded_white, decoded_black = indexer.decode(index)

            # Verify
            if decoded_white == white_sq and decoded_black == black_sq:
                print(f"✓ {white_sq} vs {black_sq} -> index {index} -> {decoded_white} vs {decoded_black}")
            else:
                print(f"✗ Mismatch: {white_sq} vs {black_sq} -> {decoded_white} vs {decoded_black}")
                return False

        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    # Test that different positions have different indices
    indices = set()
    for i in range(64):
        for j in range(64):
            if i != j:
                try:
                    idx = indexer.encode([i], [j])
                    if idx in indices:
                        print(f"✗ Collision: positions {i},{j} has duplicate index {idx}")
                        return False
                    indices.add(idx)
                except:
                    pass

    print(f"✓ Generated {len(indices):,} unique indices")

    return True


def test_storage():
    """Test tablebase storage operations."""
    print("\n" + "="*70)
    print("Test 3: Storage Operations")
    print("="*70)

    # Create temporary file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        filepath = tmpdir / "test.cmgtb"

        material = MaterialSignature.from_pieces([5], [5])
        indexer = PositionIndexer(material)
        table_size = indexer.max_index()

        print(f"Creating storage with {table_size:,} positions...")

        # Create storage
        try:
            storage = TablebaseStorage(filepath, material, table_size, mode='w')
            print(f"✓ Storage created: {filepath.name}")

            # Test write/read
            test_data = [
                (0, PositionValue.HELPMATE_IN_1),
                (100, PositionValue.HELPMATE_IN_3),
                (1000, PositionValue.DRAW),
                (table_size - 1, PositionValue.ILLEGAL),
            ]

            for index, value in test_data:
                storage.set_value(index, value)

            storage.flush()

            # Read back
            for index, expected in test_data:
                actual = storage.get_value(index)
                if actual == expected:
                    print(f"✓ Index {index}: {expected.name}")
                else:
                    print(f"✗ Index {index}: expected {expected.name}, got {actual.name}")
                    storage.close()
                    return False

            storage.close()

            # Reopen and verify
            storage = TablebaseStorage(filepath, material, table_size, mode='r')
            print("✓ Reopened storage in read mode")

            for index, expected in test_data:
                actual = storage.get_value(index)
                if actual != expected:
                    print(f"✗ After reopen, index {index}: expected {expected.name}, got {actual.name}")
                    storage.close()
                    return False

            print("✓ All values persisted correctly")
            storage.close()

        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    return True


def test_small_generation():
    """Test generating a small tablebase (KvK)."""
    print("\n" + "="*70)
    print("Test 4: Small Tablebase Generation")
    print("="*70)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        material = MaterialSignature.from_pieces([5], [5])
        print(f"Generating {material} tablebase...")

        try:
            generator = TablebaseGenerator()

            # Generate
            stats = generator.generate_helpmate_tablebase(
                material=material,
                output_dir=tmpdir,
                max_depth=5
            )

            print(f"\n✓ Generation completed")
            print(f"  Total positions: {stats['total_positions']:,}")
            print(f"  Legal positions: {stats['legal_positions']:,}")
            print(f"  Helpmate positions: {stats['helpmate_positions']:,}")
            print(f"  Draw positions: {stats['draw_positions']:,}")
            print(f"  Illegal positions: {stats['illegal_positions']:,}")
            print(f"  Max DTM: {stats['max_dtm']}")
            print(f"  Time: {stats['generation_time_seconds']:.2f}s")

            # Verify file exists
            filepath = tmpdir / f"{material}.cmgtb"
            if not filepath.exists():
                print(f"✗ Output file not created")
                return False

            print(f"✓ Output file: {filepath.name} ({filepath.stat().st_size / 1024:.2f} KB)")

            # Try to probe it
            probe = TablebaseProbe(tmpdir)
            available = probe.available_tablebases()

            if str(material) in available:
                print(f"✓ Tablebase is discoverable")
            else:
                print(f"✗ Tablebase not found by probe")
                return False

        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    return True


def main():
    """Run all tests."""
    print("\n" + "#"*70)
    print("# ChessMG Tablebase System - Basic Tests")
    print("#"*70)

    tests = [
        ("Material Signature", test_material_signature),
        ("Position Indexing", test_position_indexing),
        ("Storage Operations", test_storage),
        ("Small Generation", test_small_generation),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "#"*70)
    print("# Test Summary")
    print("#"*70)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    print(f"\nPassed: {passed}/{total}")
    print("#"*70 + "\n")

    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
