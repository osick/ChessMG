#!/usr/bin/env python3
"""
ChessMG Tablebase Generator CLI

Command-line tool for generating helpmate tablebases.

Usage:
    # Generate KPvK tablebase
    python generate_tablebase.py --material KPvK --output ./tablebases

    # Generate multiple tablebases
    python generate_tablebase.py --material KQvK KRvK KBvK KNvK --output ./tablebases

    # Generate with custom depth
    python generate_tablebase.py --material KPvK --depth 10 --output ./tablebases

Examples of material signatures:
    KvK     - King vs King
    KPvK    - King + Pawn vs King
    KQvK    - King + Queen vs King
    KRvK    - King + Rook vs King
    KQvKR   - King + Queen vs King + Rook
    KPPvK   - King + 2 Pawns vs King
"""

import argparse
import sys
from pathlib import Path

from chessmg.tablebase import MaterialSignature, TablebaseGenerator


def parse_material(material_str: str) -> MaterialSignature:
    """
    Parse material signature from string format.

    Format: "KPvK" means White has K+P, Black has K

    Args:
        material_str: Material string like "KPvK"

    Returns:
        MaterialSignature object
    """
    if 'v' not in material_str:
        raise ValueError(f"Invalid material format: {material_str} (expected format: KPvK)")

    white_str, black_str = material_str.split('v')

    # Map piece characters to types
    piece_map = {
        'K': 5,  # King
        'Q': 4,  # Queen
        'R': 3,  # Rook
        'B': 2,  # Bishop
        'N': 1,  # Knight
        'P': 0,  # Pawn
    }

    # Parse white pieces
    white_pieces = []
    for char in white_str:
        if char not in piece_map:
            raise ValueError(f"Unknown piece type: {char}")
        white_pieces.append(piece_map[char])

    # Parse black pieces
    black_pieces = []
    for char in black_str:
        if char not in piece_map:
            raise ValueError(f"Unknown piece type: {char}")
        black_pieces.append(piece_map[char])

    return MaterialSignature.from_pieces(white_pieces, black_pieces)


def main():
    parser = argparse.ArgumentParser(
        description="Generate ChessMG helpmate tablebases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--material', '-m',
        nargs='+',
        required=True,
        help='Material configuration(s) to generate (e.g., KPvK KQvK)'
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('./tablebases'),
        help='Output directory for tablebase files (default: ./tablebases)'
    )

    parser.add_argument(
        '--depth', '-d',
        type=int,
        default=7,
        help='Maximum search depth in plies (default: 7)'
    )

    parser.add_argument(
        '--symmetry',
        action='store_true',
        help='Use symmetry reduction (experimental)'
    )

    parser.add_argument(
        '--estimate',
        action='store_true',
        help='Only estimate size without generating'
    )

    args = parser.parse_args()

    # Parse material signatures
    try:
        materials = [parse_material(m) for m in args.material]
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Create generator
    generator = TablebaseGenerator()

    # Estimate mode
    if args.estimate:
        print("\nTablebase Size Estimates:")
        print("=" * 70)
        for material in materials:
            info = generator.estimate_size(material)
            print(f"\n{info['material']}:")
            print(f"  Max positions:  {info['max_positions']:,}")
            print(f"  Data size:      {info['data_size_mb']:.2f} MB")
            print(f"  Total size:     {info['total_size_mb']:.2f} MB")
        print("=" * 70)
        return 0

    # Generate tablebases
    try:
        if len(materials) == 1:
            # Single tablebase
            generator.generate_helpmate_tablebase(
                material=materials[0],
                output_dir=args.output,
                max_depth=args.depth,
                use_symmetry=args.symmetry
            )
        else:
            # Multiple tablebases
            generator.generate_multiple(
                materials=materials,
                output_dir=args.output,
                max_depth=args.depth,
                use_symmetry=args.symmetry
            )

        print("\nAll tablebases generated successfully!")
        return 0

    except Exception as e:
        print(f"\nError during generation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
