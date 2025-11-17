#!/usr/bin/env python3
"""
Standalone test for indexing and storage modules.
Imports modules directly without going through package __init__.py.
"""

import sys
import tempfile
from pathlib import Path

# Add tablebase directory to path for direct imports
sys.path.insert(0, str(Path(__file__).parent / 'chessmg' / 'tablebase'))

from indexing import MaterialSignature, PositionIndexer, binomial
from storage import TablebaseStorage, PositionValue


def test_binomial():
    """Test binomial coefficient calculation."""
    print("\n" + "="*70)
    print("Test 1: Binomial Coefficients")
    print("="*70)

    tests = [
        (5, 2, 10),
        (10, 3, 120),
        (64, 2, 2016),
        (64, 3, 41664),
    ]

    for n, k, expected in tests:
        result = binomial(n, k)
        status = "✓" if result == expected else "✗"
        print(f"{status} C({n},{k}) = {result} (expected {expected})")

        if result != expected:
            return False

    return True


def test_material_signature():
    """Test material signature creation."""
    print("\n" + "="*70)
    print("Test 2: Material Signatures")
    print("="*70)

    try:
        # Valid signatures
        kvk = MaterialSignature.from_pieces([5], [5])
        print(f"✓ KvK: {kvk}")

        kpk = MaterialSignature.from_pieces([5, 0], [5])
        print(f"✓ KPvK: {kpk}")

        kqkr = MaterialSignature.from_pieces([5, 4], [5, 3])
        print(f"✓ KQvKR: {kqkr}")

        # Test piece count
        if kpk.total_pieces() != 3:
            print(f"✗ KPvK should have 3 pieces, got {kpk.total_pieces()}")
            return False
        print(f"✓ KPvK has {kpk.total_pieces()} pieces")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test invalid signature (no king)
    try:
        invalid = MaterialSignature.from_pieces([0], [5])
        print(f"✗ Should have rejected no white king")
        return False
    except ValueError:
        print(f"✓ Correctly rejected missing white king")

    return True


def test_position_indexing():
    """Test position indexing encode/decode."""
    print("\n" + "="*70)
    print("Test 3: Position Indexing")
    print("="*70)

    # Test KvK
    material = MaterialSignature.from_pieces([5], [5])
    indexer = PositionIndexer(material)

    print(f"Material: {material}")
    print(f"Max positions: {indexer.max_index():,}")

    # Expected: C(64, 1) * C(63, 1) = 64 * 63 = 4032
    expected_max = 64 * 63
    if indexer.max_index() != expected_max:
        print(f"✗ Expected {expected_max} positions, got {indexer.max_index()}")
        return False

    # Test encode/decode
    test_cases = [
        ([0], [63]),    # a1 vs h8
        ([0], [1]),     # a1 vs b1
        ([32], [40]),   # center squares
    ]

    for white_sq, black_sq in test_cases:
        index = indexer.encode(white_sq, black_sq)
        decoded_w, decoded_b = indexer.decode(index)

        if decoded_w != white_sq or decoded_b != black_sq:
            print(f"✗ Encode/decode failed: {white_sq},{black_sq} -> {index} -> {decoded_w},{decoded_b}")
            return False

        print(f"✓ {white_sq} vs {black_sq} -> index {index} -> {decoded_w} vs {decoded_b}")

    # Test uniqueness - all KvK positions should have unique indices
    print(f"\n  Testing uniqueness of all {expected_max} positions...")
    indices_seen = set()
    collision_count = 0

    for w in range(64):
        for b in range(64):
            if w == b:
                continue
            idx = indexer.encode([w], [b])

            if idx in indices_seen:
                collision_count += 1
            indices_seen.add(idx)

    if collision_count > 0:
        print(f"✗ Found {collision_count} index collisions!")
        return False

    print(f"✓ All {len(indices_seen):,} positions have unique indices")

    # Test with 3 pieces (KPvK)
    print(f"\nTesting KPvK...")
    material3 = MaterialSignature.from_pieces([5, 0], [5])
    indexer3 = PositionIndexer(material3)
    print(f"Material: {material3}")
    print(f"Max positions: {indexer3.max_index():,}")

    # Test a few encodes/decodes
    test3 = [
        ([4, 12], [60]),  # e1, e2, e8
        ([0, 8], [63]),   # a1, a2, h8
    ]

    for white_sq, black_sq in test3:
        idx = indexer3.encode(white_sq, black_sq)
        dec_w, dec_b = indexer3.decode(idx)

        if sorted(dec_w) != sorted(white_sq) or sorted(dec_b) != sorted(black_sq):
            print(f"✗ KPvK encode/decode failed")
            return False

        print(f"✓ {white_sq} vs {black_sq} -> index {idx}")

    return True


def test_storage():
    """Test tablebase storage."""
    print("\n" + "="*70)
    print("Test 4: Tablebase Storage")
    print("="*70)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        filepath = tmpdir / "test_kvk.cmgtb"

        material = MaterialSignature.from_pieces([5], [5])
        indexer = PositionIndexer(material)
        table_size = indexer.max_index()

        print(f"Creating storage: {filepath.name}")
        print(f"Table size: {table_size:,} positions")

        try:
            # Create storage
            storage = TablebaseStorage(filepath, material, table_size, mode='w')

            # File size
            data_size_kb = storage.data_size / 1024
            print(f"✓ Data size: {data_size_kb:.2f} KB")

            # Write some values
            test_data = [
                (0, PositionValue.HELPMATE_IN_1),
                (100, PositionValue.HELPMATE_IN_3),
                (1000, PositionValue.DRAW),
                (table_size - 1, PositionValue.ILLEGAL),
            ]

            for idx, val in test_data:
                storage.set_value(idx, val)

            # Read back
            for idx, expected in test_data:
                actual = storage.get_value(idx)
                if actual != expected:
                    print(f"✗ Read/write mismatch at {idx}")
                    return False

            print(f"✓ Read/write test passed")

            storage.close()

            # Reopen and verify persistence
            storage = TablebaseStorage(filepath, material, table_size, mode='r')

            for idx, expected in test_data:
                actual = storage.get_value(idx)
                if actual != expected:
                    print(f"✗ Persistence failed at {idx}")
                    return False

            print(f"✓ Persistence test passed")

            # Get stats
            stats = storage.get_stats()
            print(f"\nStorage statistics:")
            for key, val in stats.items():
                if val > 0:
                    print(f"  {key}: {val:,}")

            storage.close()

        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    return True


def main():
    """Run all tests."""
    print("\n" + "#"*70)
    print("# ChessMG Tablebase - Indexing & Storage Tests")
    print("#"*70)

    tests = [
        ("Binomial Coefficients", test_binomial),
        ("Material Signatures", test_material_signature),
        ("Position Indexing", test_position_indexing),
        ("Storage Operations", test_storage),
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

    if passed == total:
        print("✓ All indexing and storage tests passed!")
        print("\nThese are the core building blocks of the tablebase system.")
        print("Full retrograde analysis requires ChessMG to be built.")
        print("See TABLEBASE_README.md for complete documentation.")

    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
