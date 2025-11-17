#!/usr/bin/env python3
"""
cmgtb - ChessMG Tablebase CLI

A polished command-line interface for generating and probing helpmate tablebases.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional
import time


def print_header(text: str):
    """Print a formatted header."""
    width = 70
    print("\n" + "=" * width)
    print(text.center(width))
    print("=" * width + "\n")


def print_success(text: str):
    """Print success message."""
    print(f"✓ {text}")


def print_error(text: str):
    """Print error message."""
    print(f"✗ {text}", file=sys.stderr)


def print_info(text: str):
    """Print info message."""
    print(f"→ {text}")


def format_time(seconds: float) -> str:
    """Format seconds into human-readable time."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


def format_size(bytes: int) -> str:
    """Format bytes into human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024
    return f"{bytes:.1f} TB"


def progress_bar(current: int, total: int, width: int = 50) -> str:
    """Generate a progress bar string."""
    if total == 0:
        return "[" + "=" * width + "]"

    filled = int(width * current / total)
    bar = "=" * filled + "-" * (width - filled)
    percent = 100.0 * current / total
    return f"[{bar}] {percent:5.1f}%"


def cmd_generate(args):
    """Generate a tablebase."""
    from tablebase import MaterialSignature, PositionIndexer, TablebaseStorage
    from tablebase.retrograde_helpmate import HelpmateRetrogradeAnalyzer

    print_header(f"Generating {args.material} Helpmate Tablebase")

    # Parse material
    try:
        material = parse_material(args.material)
    except ValueError as e:
        print_error(f"Invalid material: {e}")
        return 1

    print_info(f"Material: {material}")
    print_info(f"Output: {args.output}")
    print_info(f"Max depth: {args.depth} ply")
    print_info(f"Target: Mate {['White', 'Black'][args.target_color]} king\n")

    # Create indexer
    indexer = PositionIndexer(material)
    print_info(f"Total position space: {indexer.max_index():,} positions")

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create storage
    output_file = output_dir / f"{args.material}.cmgtb"
    storage = TablebaseStorage(
        output_file,
        material,
        indexer.max_index(),
        mode='w'
    )

    # Generate
    print("\n" + "-" * 70)
    start_time = time.time()

    analyzer = HelpmateRetrogradeAnalyzer(material, indexer)

    # Progress callback
    def on_progress(ply, count):
        elapsed = time.time() - start_time
        print(f"  Ply {ply:2d}: {count:8,} positions  [{format_time(elapsed)}]")

    stats = analyzer.generate_tablebase(
        storage,
        max_depth=args.depth,
        target_color=args.target_color,
        progress_callback=on_progress
    )

    storage.close()

    # Print results
    elapsed = time.time() - start_time
    print("-" * 70)

    print_header("Generation Complete")

    print(f"  Time elapsed:       {format_time(elapsed)}")
    print(f"  Total positions:    {stats['total_positions']:,}")
    print(f"  Helpmate positions: {stats['helpmate_positions']:,}")
    print(f"  Draw positions:     {stats['draw_positions']:,}")
    print(f"  Illegal positions:  {stats['illegal_positions']:,}")
    print(f"  Max DTM:            {stats['max_dtm']}")

    file_size = output_file.stat().st_size
    print(f"  File size:          {format_size(file_size)}")

    if stats['helpmate_positions'] > 0:
        print(f"\n  Distribution by DTM:")
        for ply in sorted(stats['positions_by_dtm'].keys()):
            count = stats['positions_by_dtm'][ply]
            percent = 100.0 * count / stats['helpmate_positions']
            print(f"    DTM {ply}: {count:8,} positions ({percent:5.1f}%)")

    print_success(f"Tablebase saved to {output_file}\n")
    return 0


def cmd_probe(args):
    """Probe a position."""
    from tablebase import TablebaseProbe
    from chessmg import ChessPosition

    print_header("Probing Position")

    # Create position
    try:
        pos = ChessPosition(args.fen)
    except Exception as e:
        print_error(f"Invalid FEN: {e}")
        return 1

    print(f"  FEN: {args.fen}")
    print(f"  Turn: {['White', 'Black'][pos.turn()]}\n")

    # Initialize probe
    probe = TablebaseProbe(Path(args.dir))

    # Probe position
    value = probe.probe(pos)

    if value is None:
        print_info("Position not found in tablebase")
        return 0

    print_success(f"Position value: {value.name}")

    if value.is_helpmate():
        dtm = value.moves_to_helpmate()
        print(f"  Distance to mate: {dtm} ply")

    print()
    return 0


def cmd_search(args):
    """Search for positions in tablebase."""
    from tablebase import TablebaseStorage, MaterialSignature, PositionIndexer
    from tablebase.fast_helpers import create_position_fast

    print_header(f"Searching {args.material} Tablebase")

    # Parse material
    try:
        material = parse_material(args.material)
    except ValueError as e:
        print_error(f"Invalid material: {e}")
        return 1

    # Open tablebase
    tb_file = Path(args.dir) / f"{args.material}.cmgtb"
    if not tb_file.exists():
        print_error(f"Tablebase not found: {tb_file}")
        return 1

    storage = TablebaseStorage.open(tb_file, mode='r')
    indexer = PositionIndexer(material)

    print_info(f"Searching for positions with DTM = {args.dtm}")
    print_info(f"Limit: {args.limit} results\n")

    # Search
    results = []
    for index in range(storage.table_size):
        value = storage.get_value(index)

        # Check DTM filter
        if value.is_helpmate() and value.moves_to_helpmate() == args.dtm:
            # Decode position
            white_sq, black_sq, stm, ep = indexer.decode(index)

            # Create position
            pos = create_position_fast(
                list(material.white_pieces),
                list(white_sq),
                list(material.black_pieces),
                list(black_sq),
                stm,
                ep if ep < 64 else 64
            )

            if pos:
                results.append((index, pos.fen(), value))

            if len(results) >= args.limit:
                break

    # Print results
    if results:
        print_success(f"Found {len(results)} matching positions:\n")
        for i, (index, fen, value) in enumerate(results, 1):
            print(f"{i:3d}. Index {index:8d}: {fen}")
            print(f"     Value: {value.name}\n")
    else:
        print_info("No matching positions found")

    storage.close()
    return 0


def cmd_list(args):
    """List available tablebases."""
    print_header("Available Tablebases")

    tb_dir = Path(args.dir)
    if not tb_dir.exists():
        print_error(f"Directory not found: {tb_dir}")
        return 1

    tb_files = list(tb_dir.glob("*.cmgtb"))

    if not tb_files:
        print_info("No tablebases found")
        return 0

    print(f"  Directory: {tb_dir}\n")

    for tb_file in sorted(tb_files):
        try:
            from tablebase import TablebaseStorage
            storage = TablebaseStorage.open(tb_file, mode='r')

            size = tb_file.stat().st_size
            print(f"  {tb_file.name}")
            print(f"    Material: {storage.material}")
            print(f"    Positions: {storage.table_size:,}")
            print(f"    Size: {format_size(size)}\n")

            storage.close()

        except Exception as e:
            print(f"  {tb_file.name}: Error - {e}\n")

    return 0


def cmd_stats(args):
    """Show tablebase statistics."""
    from tablebase import TablebaseStorage, PositionValue

    print_header(f"{args.material} Tablebase Statistics")

    tb_file = Path(args.dir) / f"{args.material}.cmgtb"
    if not tb_file.exists():
        print_error(f"Tablebase not found: {tb_file}")
        return 1

    storage = TablebaseStorage.open(tb_file, mode='r')

    print_info(f"Material: {storage.material}")
    print_info(f"Total positions: {storage.table_size:,}")

    file_size = tb_file.stat().st_size
    print_info(f"File size: {format_size(file_size)}\n")

    # Count values
    print("Analyzing tablebase...")
    value_counts = {}
    for index in range(storage.table_size):
        value = storage.get_value(index)
        value_counts[value] = value_counts.get(value, 0) + 1

        # Progress indication
        if index % 50000 == 0 and index > 0:
            print(f"  Processed {index:,} / {storage.table_size:,}", end='\r')

    print()  # Clear progress line

    # Print distribution
    print_header("Position Distribution")

    for value in sorted(value_counts.keys(), key=lambda v: v.value):
        count = value_counts[value]
        percent = 100.0 * count / storage.table_size
        print(f"  {value.name:20s}: {count:10,} ({percent:5.1f}%)")

    print()
    storage.close()
    return 0


def parse_material(material_str: str) -> 'MaterialSignature':
    """Parse material string like 'KPvK' to MaterialSignature."""
    from tablebase import MaterialSignature

    if 'v' not in material_str:
        raise ValueError(f"Material must contain 'v' separator: {material_str}")

    piece_map = {'K': 5, 'Q': 4, 'R': 3, 'B': 2, 'N': 1, 'P': 0}

    white_str, black_str = material_str.split('v')

    white_pieces = []
    for char in white_str:
        if char in piece_map:
            white_pieces.append(piece_map[char])
        else:
            raise ValueError(f"Unknown piece: {char}")

    black_pieces = []
    for char in black_str:
        if char in piece_map:
            black_pieces.append(piece_map[char])
        else:
            raise ValueError(f"Unknown piece: {char}")

    return MaterialSignature.from_pieces(white_pieces, black_pieces)


def main():
    parser = argparse.ArgumentParser(
        prog='cmgtb',
        description='ChessMG Tablebase Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate KPvK helpmate tablebase
  cmgtb generate KPvK --output ./tablebases --depth 10

  # Probe a position
  cmgtb probe "8/8/8/8/8/5k2/4P3/5K2 w - - 0 1" --dir ./tablebases

  # Search for helpmate-in-5 positions
  cmgtb search --material KPvK --dtm 5 --dir ./tablebases --limit 10

  # List available tablebases
  cmgtb list --dir ./tablebases

  # Show statistics
  cmgtb stats KPvK --dir ./tablebases
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate a tablebase')
    gen_parser.add_argument('material', help='Material signature (e.g., KPvK, KQvK)')
    gen_parser.add_argument('--output', default='./tablebases', help='Output directory')
    gen_parser.add_argument('--depth', type=int, default=7, help='Max search depth in ply')
    gen_parser.add_argument('--target-color', type=int, default=1, choices=[0, 1],
                           help='Which side to mate (0=White, 1=Black)')

    # Probe command
    probe_parser = subparsers.add_parser('probe', help='Probe a position')
    probe_parser.add_argument('fen', help='FEN string of position')
    probe_parser.add_argument('--dir', default='./tablebases', help='Tablebase directory')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search tablebase')
    search_parser.add_argument('--material', required=True, help='Material signature')
    search_parser.add_argument('--dtm', type=int, required=True, help='Distance to mate')
    search_parser.add_argument('--dir', default='./tablebases', help='Tablebase directory')
    search_parser.add_argument('--limit', type=int, default=10, help='Max results to show')

    # List command
    list_parser = subparsers.add_parser('list', help='List available tablebases')
    list_parser.add_argument('--dir', default='./tablebases', help='Tablebase directory')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show tablebase statistics')
    stats_parser.add_argument('material', help='Material signature')
    stats_parser.add_argument('--dir', default='./tablebases', help='Tablebase directory')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    commands = {
        'generate': cmd_generate,
        'probe': cmd_probe,
        'search': cmd_search,
        'list': cmd_list,
        'stats': cmd_stats,
    }

    try:
        return commands[args.command](args)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
