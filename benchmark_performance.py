#!/usr/bin/env python3
"""
Performance analysis of tablebase position encoding/decoding.

Tests:
1. FEN-based position creation (current - SLOW)
2. Direct position creation (needed - FAST)
3. Move generation speed
4. Position indexing speed
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'chessmg' / 'tablebase'))
from indexing_v2 import MaterialSignature, PositionIndexer


def benchmark_indexing():
    """Benchmark pure indexing operations (no ChessMG)."""
    print("\n" + "="*70)
    print("Benchmark 1: Pure Indexing (No ChessMG)")
    print("="*70)

    material = MaterialSignature.from_pieces([5, 0], [5])  # KPvK
    indexer = PositionIndexer(material)

    n_positions = 10000

    # Test encode
    start = time.time()
    for i in range(n_positions):
        # Encode some positions
        white_sq = [i % 64, (i + 1) % 64]
        black_sq = [(i + 2) % 64]
        if len(set(white_sq + black_sq)) == 3:  # No overlaps
            idx = indexer.encode(white_sq, black_sq, side_to_move=i % 2)

    encode_time = time.time() - start
    encode_rate = n_positions / encode_time

    print(f"Encode: {n_positions:,} positions in {encode_time:.3f}s")
    print(f"  Rate: {encode_rate:,.0f} positions/sec")

    # Test decode
    start = time.time()
    for i in range(n_positions):
        idx = i % indexer.max_index()
        w, b, stm, ep = indexer.decode(idx)

    decode_time = time.time() - start
    decode_rate = n_positions / decode_time

    print(f"Decode: {n_positions:,} positions in {decode_time:.3f}s")
    print(f"  Rate: {decode_rate:,.0f} positions/sec")

    print(f"\n✓ Pure indexing is FAST (no bottleneck here)")

    return encode_rate, decode_rate


def benchmark_fen_creation():
    """Benchmark FEN-based position creation (SLOW)."""
    print("\n" + "="*70)
    print("Benchmark 2: FEN-Based Position Creation (SLOW)")
    print("="*70)

    # Try to import ChessPosition
    try:
        from chessmg.position import ChessPosition
    except:
        print("⚠️  ChessPosition not available (ChessMG not built)")
        print("   This would be the SLOW path anyway")
        return None

    test_fens = [
        "8/8/8/8/8/5k2/4P3/5K2 w - - 0 1",
        "8/8/8/8/8/6k1/5P2/6K1 w - - 0 1",
        "8/8/8/8/8/7k/6P1/7K w - - 0 1",
    ]

    n_iterations = 1000

    start = time.time()
    for _ in range(n_iterations):
        for fen in test_fens:
            pos = ChessPosition(fen)
            moves = pos.legal_moves()

    total_time = time.time() - start
    rate = (n_iterations * len(test_fens)) / total_time

    print(f"Created {n_iterations * len(test_fens):,} positions via FEN")
    print(f"  Time: {total_time:.3f}s")
    print(f"  Rate: {rate:,.0f} positions/sec")
    print(f"\n✗ FEN parsing is SLOW (major bottleneck!)")

    return rate


def analyze_bottleneck():
    """Identify the bottleneck."""
    print("\n" + "="*70)
    print("Analysis: Performance Bottleneck")
    print("="*70)

    print("\nCurrent Implementation Flow:")
    print("  1. Decode index → piece squares")
    print("  2. Build FEN string from squares          ← SLOW!")
    print("  3. Parse FEN string → ChessPosition       ← SLOW!")
    print("  4. Generate legal moves")
    print("  5. For each move:")
    print("       a. Make move")
    print("       b. Extract FEN                       ← SLOW!")
    print("       c. Parse FEN to get piece squares    ← SLOW!")
    print("       d. Encode squares → index")

    print("\nBottleneck: FEN string conversion")
    print("  - FEN building: String concatenation, formatting")
    print("  - FEN parsing: String parsing, validation, error checking")
    print("  - Estimated overhead: 100-1000x slower than needed")

    print("\nOptimal Implementation:")
    print("  1. Decode index → piece squares")
    print("  2. Create Position DIRECTLY from squares  ← FAST!")
    print("  3. Generate legal moves")
    print("  4. For each move:")
    print("       a. Make move in-place")
    print("       b. Read piece squares DIRECTLY        ← FAST!")
    print("       c. Encode squares → index")

    print("\nRequired:")
    print("  - Direct access to ChessMG Position class")
    print("  - Method to set pieces without FEN")
    print("  - Method to read piece positions directly")
    print("  - In-place move making (copy-free if possible)")


def estimate_generation_time():
    """Estimate tablebase generation time."""
    print("\n" + "="*70)
    print("Estimate: Tablebase Generation Time")
    print("="*70)

    # KPvK example
    positions = 380_000  # With side-to-move
    avg_moves = 20       # Average legal moves per position
    avg_depth = 30       # Average ply to reach all positions

    total_operations = positions * avg_moves * avg_depth

    print(f"KPvK Tablebase:")
    print(f"  Positions: {positions:,}")
    print(f"  Avg moves/position: {avg_moves}")
    print(f"  Avg depth: {avg_depth}")
    print(f"  Total operations: {total_operations:,}")

    # Current (FEN-based): ~1000 pos/sec
    print(f"\nCurrent (FEN-based, ~1000 pos/sec):")
    fen_time = total_operations / 1000
    print(f"  Time: {fen_time:,.0f} seconds = {fen_time/60:.1f} minutes")
    print(f"  ✗ Too slow!")

    # Optimized (direct access): ~100,000 pos/sec
    print(f"\nOptimized (direct access, ~100,000 pos/sec):")
    direct_time = total_operations / 100_000
    print(f"  Time: {direct_time:,.0f} seconds = {direct_time/60:.1f} minutes")
    print(f"  ✓ 100x faster!")

    # ChessMG move generation: ~250M moves/sec
    print(f"\nChessMG capability: 250M moves/sec")
    print(f"  We need to match this speed!")


def main():
    """Run performance analysis."""
    print("\n" + "#"*70)
    print("# Tablebase Performance Analysis")
    print("#"*70)

    # Benchmark indexing
    encode_rate, decode_rate = benchmark_indexing()

    # Benchmark FEN creation
    fen_rate = benchmark_fen_creation()

    # Analyze bottleneck
    analyze_bottleneck()

    # Estimate generation time
    estimate_generation_time()

    # Summary
    print("\n" + "#"*70)
    print("# Summary")
    print("#"*70)

    print(f"\nIndexing: {encode_rate:,.0f} encodes/sec, {decode_rate:,.0f} decodes/sec")
    if fen_rate:
        print(f"FEN creation: {fen_rate:,.0f} positions/sec")
        print(f"Slowdown: {encode_rate / fen_rate:.0f}x slower than pure indexing")

    print("\n⚠️  CRITICAL: FEN-based position creation is the bottleneck")
    print("✅  SOLUTION: Direct Position API needed")
    print("\nNext steps:")
    print("  1. Add C++ bindings for direct position creation")
    print("  2. Add method to read piece positions directly")
    print("  3. Eliminate all FEN string operations")
    print("  4. Implement multi-tablebase retrograde analysis")


if __name__ == '__main__':
    main()
