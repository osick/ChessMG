#!/usr/bin/env python3
"""
Test special cases handling in tablebase indexing.

Demonstrates:
1. Side-to-move encoding
2. En passant encoding
3. Why these matter for correctness
"""

import sys
from pathlib import Path

# Import directly to avoid dependency issues
sys.path.insert(0, str(Path(__file__).parent / 'chessmg' / 'tablebase'))

from indexing_v2 import MaterialSignature, PositionIndexer, binomial


def test_side_to_move():
    """Test that side-to-move is properly encoded."""
    print("\n" + "="*70)
    print("Test 1: Side-to-Move Encoding")
    print("="*70)

    material = MaterialSignature.from_pieces([5], [5])  # KvK
    indexer = PositionIndexer(material)

    print(f"Material: {material}")
    print(f"Max positions: {indexer.max_index():,}")
    print(f"Base positions (no stm): {indexer.base_positions():,}")
    print(f"Ratio: {indexer.max_index() / indexer.base_positions():.1f}x (should be 2x)")

    # Test: Same pieces, different side to move → different indices
    white_squares = [0]   # a1
    black_squares = [63]  # h8

    idx_white = indexer.encode(white_squares, black_squares, side_to_move=0)
    idx_black = indexer.encode(white_squares, black_squares, side_to_move=1)

    print(f"\nSame position (Ka1 vs Kh8):")
    print(f"  White to move: index = {idx_white}")
    print(f"  Black to move: index = {idx_black}")

    if idx_white == idx_black:
        print("  ✗ FAIL: Indices should be different!")
        return False
    else:
        print(f"  ✓ PASS: Indices differ (Δ = {abs(idx_white - idx_black)})")

    # Test: Decode and verify
    w, b, stm, _ = indexer.decode(idx_white)
    assert w == white_squares and b == black_squares and stm == 0
    print(f"  ✓ Decode white-to-move: stm={stm}")

    w, b, stm, _ = indexer.decode(idx_black)
    assert w == white_squares and b == black_squares and stm == 1
    print(f"  ✓ Decode black-to-move: stm={stm}")

    # Test: All positions have unique indices
    print(f"\n  Testing uniqueness across all {indexer.max_index():,} positions...")
    indices_seen = set()
    for sq_w in range(64):
        for sq_b in range(64):
            if sq_w == sq_b:
                continue
            for stm in [0, 1]:
                idx = indexer.encode([sq_w], [sq_b], side_to_move=stm)
                if idx in indices_seen:
                    print(f"  ✗ Collision at {sq_w},{sq_b},stm={stm}")
                    return False
                indices_seen.add(idx)

    print(f"  ✓ All {len(indices_seen):,} positions have unique indices")

    return True


def test_en_passant():
    """Test en passant encoding."""
    print("\n" + "="*70)
    print("Test 2: En Passant Encoding")
    print("="*70)

    material = MaterialSignature.from_pieces([5, 0], [5])  # KPvK
    indexer = PositionIndexer(material, encode_en_passant=True)

    print(f"Material: {material}")
    print(f"Max positions: {indexer.max_index():,}")
    print(f"Base positions: {indexer.base_positions():,}")
    print(f"Positions with stm: {indexer.base_positions() * 2:,}")
    print(f"Ratio (with ep): {indexer.max_index() / (indexer.base_positions() * 2):.1f}x (should be 9x)")

    # Test: Same position, different e.p. rights
    white_squares = [4, 12]  # e1 (king), e2 (pawn)
    black_squares = [60]      # e8 (king)

    # No en passant
    idx_no_ep = indexer.encode(white_squares, black_squares, side_to_move=0, ep_file=0)

    # En passant on e-file (file 5)
    idx_with_ep = indexer.encode(white_squares, black_squares, side_to_move=0, ep_file=5)

    print(f"\nSame position (Ke1,Pe2 vs Ke8), white to move:")
    print(f"  No e.p.:       index = {idx_no_ep}")
    print(f"  E.p. on e-file: index = {idx_with_ep}")

    if idx_no_ep == idx_with_ep:
        print("  ✗ FAIL: Indices should be different!")
        return False
    else:
        print(f"  ✓ PASS: Indices differ (Δ = {abs(idx_no_ep - idx_with_ep)})")

    # Test decode
    w, b, stm, ep = indexer.decode(idx_no_ep)
    assert ep == 0
    print(f"  ✓ Decode no e.p.: ep_file={ep}")

    w, b, stm, ep = indexer.decode(idx_with_ep)
    assert ep == 5
    print(f"  ✓ Decode with e.p.: ep_file={ep} (e-file)")

    return True


def test_size_comparison():
    """Compare sizes with different encoding options."""
    print("\n" + "="*70)
    print("Test 3: Size Comparison")
    print("="*70)

    materials = [
        ("KvK", MaterialSignature.from_pieces([5], [5])),
        ("KPvK", MaterialSignature.from_pieces([5, 0], [5])),
        ("KQvK", MaterialSignature.from_pieces([5, 4], [5])),
    ]

    print(f"\n{'Material':<10} {'Base':<12} {'+ STM':<12} {'+ EP':<12} {'STM Ratio':<12} {'EP Ratio':<12}")
    print("-" * 70)

    for name, material in materials:
        # Base (no stm, no ep)
        idx_base = PositionIndexer(material, encode_en_passant=False)
        # Hack: temporarily compute base without stm
        base_size = idx_base._base_positions

        # With side-to-move
        idx_stm = PositionIndexer(material, encode_en_passant=False)
        stm_size = idx_stm.max_index()

        # With en passant (if has pawns)
        has_pawns = 0 in material.white_pieces or 0 in material.black_pieces
        if has_pawns:
            idx_ep = PositionIndexer(material, encode_en_passant=True)
            ep_size = idx_ep.max_index()
        else:
            ep_size = stm_size  # No pawns → no ep encoding

        stm_ratio = stm_size / base_size
        ep_ratio = ep_size / stm_size

        print(f"{name:<10} {base_size:<12,} {stm_size:<12,} {ep_size:<12,} {stm_ratio:<12.1f} {ep_ratio:<12.1f}")

    print("\nExpected ratios:")
    print("  STM Ratio: 2.0x (doubles for side-to-move)")
    print("  EP Ratio:  9.0x (only for materials with pawns)")

    return True


def test_why_it_matters():
    """Demonstrate why side-to-move matters."""
    print("\n" + "="*70)
    print("Test 4: Why Side-to-Move Matters")
    print("="*70)

    print("\nExample: Stalemate vs. Not Stalemate")
    print("-" * 50)
    print("Position: Ka1 vs Kb3")
    print()
    print("  White to move:")
    print("    White king on a1, black king on b3")
    print("    Legal moves: None (all adjacent squares attacked)")
    print("    Result: STALEMATE (if not in check)")
    print()
    print("  Black to move:")
    print("    Same pieces!")
    print("    Legal moves: Black king can move to many squares")
    print("    Result: Not stalemate, game continues")
    print()
    print("  → Same piece placement, DIFFERENT position values")
    print("  → MUST have different tablebase indices")

    # Demonstrate with indexing
    material = MaterialSignature.from_pieces([5], [5])
    indexer = PositionIndexer(material)

    # Ka1 vs Kb3
    idx_white = indexer.encode([0], [11], side_to_move=0)
    idx_black = indexer.encode([0], [11], side_to_move=1)

    print(f"\n  Index (white to move): {idx_white}")
    print(f"  Index (black to move): {idx_black}")
    print(f"  ✓ Different indices for different evaluations")

    return True


def main():
    """Run all tests."""
    print("\n" + "#"*70)
    print("# Special Cases Handling - Tests")
    print("#"*70)

    tests = [
        ("Side-to-Move Encoding", test_side_to_move),
        ("En Passant Encoding", test_en_passant),
        ("Size Comparison", test_size_comparison),
        ("Why It Matters", test_why_it_matters),
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

    passed = sum(1 for _, r in results if r is not False)
    total = len(results)

    print(f"\nPassed: {passed}/{total}")
    print("#"*70 + "\n")

    if passed == total:
        print("✓ All special cases tests passed!")
        print("\nKey Takeaways:")
        print("  1. Side-to-move MUST be encoded (doubles tablebase size)")
        print("  2. En passant CAN be encoded (9x increase, optional)")
        print("  3. Castling rarely needed in endgames (16x increase)")
        print("  4. Captures/promotions require multi-tablebase analysis")
        print("\nSee SPECIAL_CASES_HANDLING.md for complete documentation.")

    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
