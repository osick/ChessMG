#!/usr/bin/env python3
"""
Example: Using ChessMG Tablebase System

Demonstrates:
1. Generating a simple tablebase (KvK)
2. Probing positions
3. Using the tablebase API
"""

from pathlib import Path
from chessmg.tablebase import (
    MaterialSignature,
    TablebaseGenerator,
    TablebaseProbe,
    PositionIndexer
)
from chessmg.position import ChessPosition


def example_1_simple_generation():
    """Example 1: Generate a simple KvK tablebase."""
    print("\n" + "="*70)
    print("Example 1: Generate KvK Tablebase")
    print("="*70)

    # Define material: King vs King
    material = MaterialSignature.from_pieces(
        white=[5],  # White King
        black=[5]   # Black King
    )

    print(f"Material: {material}")

    # Create generator
    generator = TablebaseGenerator()

    # Estimate size first
    estimate = generator.estimate_size(material)
    print(f"\nEstimated size: {estimate['total_size_mb']:.2f} MB")
    print(f"Max positions: {estimate['max_positions']:,}")

    # Generate
    stats = generator.generate_helpmate_tablebase(
        material=material,
        output_dir=Path('./tablebases'),
        max_depth=5
    )

    print(f"\nGeneration completed!")
    print(f"Legal positions: {stats['legal_positions']:,}")
    print(f"Helpmate positions: {stats['helpmate_positions']:,}")


def example_2_probe_positions():
    """Example 2: Probe positions in a tablebase."""
    print("\n" + "="*70)
    print("Example 2: Probe Positions")
    print("="*70)

    # Create probe
    probe = TablebaseProbe(Path('./tablebases'))

    # List available tablebases
    available = probe.available_tablebases()
    print(f"\nAvailable tablebases: {available}")

    if not available:
        print("No tablebases found. Run example_1 first!")
        return

    # Probe a KvK position
    test_positions = [
        "4k3/8/8/8/8/8/8/4K3 w - - 0 1",  # Kings far apart
        "4k3/8/8/8/8/8/8/5K2 w - - 0 1",  # Kings close
    ]

    for fen in test_positions:
        print(f"\nPosition: {fen}")
        result = probe.probe_fen(fen)

        if result:
            print(f"  Result: {result.name}")
            if result.is_helpmate():
                print(f"  DTM: {result.moves_to_helpmate()}")
        else:
            print(f"  Not in tablebase")


def example_3_kpk_generation():
    """Example 3: Generate KPvK tablebase (more interesting)."""
    print("\n" + "="*70)
    print("Example 3: Generate KPvK Tablebase")
    print("="*70)

    # Define material: King + Pawn vs King
    material = MaterialSignature.from_pieces(
        white=[5, 0],  # King + Pawn
        black=[5]      # King
    )

    print(f"Material: {material}")

    # Create generator
    generator = TablebaseGenerator()

    # Estimate size
    estimate = generator.estimate_size(material)
    print(f"\nEstimated size: {estimate['total_size_mb']:.2f} MB")
    print(f"Max positions: {estimate['max_positions']:,}")

    # This will be larger, so let's just show the estimate
    print("\nTo generate, uncomment the following code:")
    print("""
    stats = generator.generate_helpmate_tablebase(
        material=material,
        output_dir=Path('./tablebases'),
        max_depth=10
    )
    """)


def example_4_indexing_demo():
    """Example 4: Demonstrate position indexing."""
    print("\n" + "="*70)
    print("Example 4: Position Indexing Demo")
    print("="*70)

    # Create indexer for KvK
    material = MaterialSignature.from_pieces([5], [5])
    indexer = PositionIndexer(material)

    print(f"Material: {material}")
    print(f"Max positions: {indexer.max_index():,}")

    # Encode some positions
    examples = [
        ([0], [63]),   # White king a1, black king h8
        ([0], [1]),    # White king a1, black king b1
        ([32], [40]),  # Both kings in center
    ]

    print("\nEncoding examples:")
    for white_sq, black_sq in examples:
        index = indexer.encode(white_sq, black_sq)
        decoded_w, decoded_b = indexer.decode(index)

        # Convert square to algebraic
        def sq_to_alg(sq):
            return chr(ord('a') + sq % 8) + str(sq // 8 + 1)

        print(f"  {sq_to_alg(white_sq[0])} vs {sq_to_alg(black_sq[0])} -> index {index}")
        print(f"    Decoded back to: {sq_to_alg(decoded_w[0])} vs {sq_to_alg(decoded_b[0])}")


def main():
    """Run all examples."""
    print("\n" + "#"*70)
    print("# ChessMG Tablebase System - Examples")
    print("#"*70)

    try:
        # Example 1: Simple generation
        example_1_simple_generation()

        # Example 2: Probing
        example_2_probe_positions()

        # Example 3: Larger tablebase (estimate only)
        example_3_kpk_generation()

        # Example 4: Indexing
        example_4_indexing_demo()

        print("\n" + "#"*70)
        print("# All examples completed!")
        print("#"*70 + "\n")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
