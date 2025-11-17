#!/usr/bin/env python3
"""
ChessMG Tablebase Probe CLI

Command-line tool for querying generated tablebases.

Usage:
    # Probe a position by FEN
    python probe_tablebase.py --fen "8/8/8/8/8/5k2/4P3/5K2 w - - 0 1" --dir ./tablebases

    # List available tablebases
    python probe_tablebase.py --list --dir ./tablebases

    # Get statistics for a tablebase
    python probe_tablebase.py --stats KPvK --dir ./tablebases
"""

import argparse
import sys
from pathlib import Path

from chessmg.tablebase import TablebaseProbe, MaterialSignature, TablebaseStorage
from chessmg.tablebase.indexing import PositionIndexer


def main():
    parser = argparse.ArgumentParser(
        description="Probe ChessMG tablebases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--dir', '-d',
        type=Path,
        default=Path('./tablebases'),
        help='Tablebase directory (default: ./tablebases)'
    )

    parser.add_argument(
        '--fen', '-f',
        type=str,
        help='Position to probe (FEN format)'
    )

    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List available tablebases'
    )

    parser.add_argument(
        '--stats', '-s',
        type=str,
        help='Show statistics for a material (e.g., KPvK)'
    )

    args = parser.parse_args()

    # Create probe
    probe = TablebaseProbe(args.dir)

    # List mode
    if args.list:
        available = probe.available_tablebases()
        print(f"\nAvailable Tablebases in {args.dir}:")
        print("=" * 50)
        if available:
            for material in available:
                print(f"  {material}")
        else:
            print("  (none)")
        print("=" * 50)
        print(f"Total: {len(available)}\n")
        return 0

    # Stats mode
    if args.stats:
        filepath = args.dir / f"{args.stats}.cmgtb"
        if not filepath.exists():
            print(f"Error: Tablebase not found: {filepath}", file=sys.stderr)
            return 1

        print(f"\nTablebase Statistics: {args.stats}")
        print("=" * 70)

        try:
            # Parse material from string
            # For now, just open the file and get stats
            from chessmg.tablebase.generator import TablebaseGenerator

            # We need to extract material from the file
            # For simplicity, let's just show file info
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"File: {filepath.name}")
            print(f"Size: {size_mb:.2f} MB")

            # Try to get position counts
            # This requires opening the storage
            # For now, we'll need to know the material signature
            # This is a limitation - we should store it in the header!
            print("\nNote: Detailed statistics require parsing the material signature.")
            print("Use --fen to probe specific positions.")

        except Exception as e:
            print(f"Error reading tablebase: {e}", file=sys.stderr)
            return 1

        print("=" * 70)
        return 0

    # Probe mode
    if args.fen:
        print(f"\nProbing position:")
        print("=" * 70)
        print(f"FEN: {args.fen}")

        result = probe.probe_fen(args.fen)

        if result is None:
            print("\nResult: Position not found in tablebase")
            print("(Tablebase for this material may not exist)")
        else:
            print(f"\nResult: {result.name}")

            if result.is_helpmate():
                dtm = result.moves_to_helpmate()
                print(f"Distance to mate: {dtm} move(s)")
            elif result.name == 'DRAW':
                print("Position is a draw (no forced helpmate)")
            elif result.name == 'ILLEGAL':
                print("Position is illegal")

        print("=" * 70)
        return 0

    # No action specified
    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
