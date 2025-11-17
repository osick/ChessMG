#!/usr/bin/env python3
"""
Tablebase Search Tool

Search tablebases for positions with specific properties:
- Solution length (distance to mate)
- Number of solutions (alternative paths)
- Side to move
- Position characteristics

Output: FEN strings, indices, analysis
"""

import sys
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent / 'chessmg' / 'tablebase'))

from indexing_v2 import MaterialSignature, PositionIndexer
from storage import TablebaseStorage, PositionValue


@dataclass
class SearchResult:
    """Result of a tablebase search."""
    index: int
    fen: str
    value: PositionValue
    dtm: Optional[int]  # Distance to mate
    num_solutions: int  # Number of different paths to mate
    side_to_move: str  # "white" or "black"


class TablebaseSearcher:
    """
    Search tablebases for positions with specific properties.
    """

    def __init__(self, tablebase_path: Path, material: MaterialSignature):
        """
        Initialize searcher.

        Args:
            tablebase_path: Path to tablebase file
            material: Material signature
        """
        self.tablebase_path = Path(tablebase_path)
        self.material = material
        self.indexer = PositionIndexer(material)

        # Load tablebase
        self.storage = TablebaseStorage(
            self.tablebase_path,
            material,
            self.indexer.max_index(),
            mode='r'
        )

    def search(
        self,
        dtm: Optional[int] = None,
        dtm_range: Optional[Tuple[int, int]] = None,
        side_to_move: Optional[str] = None,
        min_solutions: Optional[int] = None,
        max_solutions: Optional[int] = None,
        position_type: Optional[str] = None,
        max_results: int = 100
    ) -> List[SearchResult]:
        """
        Search for positions matching criteria.

        Args:
            dtm: Exact distance to mate (1-7, or 8+ for 8 or more)
            dtm_range: Range of DTM values (min, max)
            side_to_move: "white", "black", or None for both
            min_solutions: Minimum number of solution paths
            max_solutions: Maximum number of solution paths
            position_type: "helpmate", "draw", "illegal"
            max_results: Maximum results to return

        Returns:
            List of SearchResult objects

        Examples:
            # Find helpmate-in-3 positions
            >>> results = searcher.search(dtm=3, position_type="helpmate")

            # Find positions with exactly 2 solution paths
            >>> results = searcher.search(min_solutions=2, max_solutions=2)

            # Find helpmate-in-2-4 with white to move
            >>> results = searcher.search(dtm_range=(2,4), side_to_move="white")
        """
        results = []
        checked = 0
        matches = 0

        print(f"Searching {self.tablebase_path.name}...")
        print(f"Criteria:")
        if dtm:
            print(f"  DTM: {dtm}")
        if dtm_range:
            print(f"  DTM range: {dtm_range[0]}-{dtm_range[1]}")
        if side_to_move:
            print(f"  Side to move: {side_to_move}")
        if min_solutions:
            print(f"  Min solutions: {min_solutions}")
        if max_solutions:
            print(f"  Max solutions: {max_solutions}")
        if position_type:
            print(f"  Type: {position_type}")

        # Iterate through all positions
        for index in range(self.indexer.max_index()):
            value = self.storage.get_value(index)

            # Filter by position type
            if position_type:
                if position_type == "helpmate" and not value.is_helpmate():
                    continue
                elif position_type == "draw" and value != PositionValue.DRAW:
                    continue
                elif position_type == "illegal" and value != PositionValue.ILLEGAL:
                    continue

            # Filter by DTM
            if value.is_helpmate():
                pos_dtm = value.moves_to_helpmate()

                if dtm and pos_dtm != dtm:
                    continue

                if dtm_range and not (dtm_range[0] <= pos_dtm <= dtm_range[1]):
                    continue
            elif dtm or dtm_range:
                continue  # Not a helpmate, skip if DTM filter specified

            # Decode position
            w_sq, b_sq, stm, ep = self.indexer.decode(index)
            stm_str = "white" if stm == 0 else "black"

            # Filter by side to move
            if side_to_move and stm_str != side_to_move:
                continue

            # Build FEN
            fen = self._build_fen(w_sq, b_sq, stm, ep)

            # Count solutions (if requested)
            num_solutions = 0
            if min_solutions or max_solutions:
                num_solutions = self._count_solutions(index, value)

                if min_solutions and num_solutions < min_solutions:
                    continue
                if max_solutions and num_solutions > max_solutions:
                    continue

            # Add to results
            result = SearchResult(
                index=index,
                fen=fen,
                value=value,
                dtm=value.moves_to_helpmate() if value.is_helpmate() else None,
                num_solutions=num_solutions,
                side_to_move=stm_str
            )
            results.append(result)
            matches += 1

            if matches >= max_results:
                break

            checked += 1
            if checked % 10000 == 0:
                print(f"  Checked {checked:,} positions, found {matches}...")

        print(f"Search complete: {matches} matches out of {checked:,} checked")
        return results

    def _count_solutions(self, index: int, value: PositionValue) -> int:
        """
        Count the number of different solution paths.

        This is complex - for now, return 1 as placeholder.
        Full implementation would need to:
        1. Generate all legal moves from position
        2. Check which ones lead to mate in (DTM-1)
        3. Recursively count distinct paths

        TODO: Implement full solution counting
        """
        # Placeholder
        return 1

    def _build_fen(self, w_sq: List[int], b_sq: List[int],
                   stm: int, ep: int) -> str:
        """Build FEN string from position data."""
        # Create empty board
        board = [['.' for _ in range(8)] for _ in range(8)]

        # Piece type to character mapping
        piece_chars = {0: 'P', 1: 'N', 2: 'B', 3: 'R', 4: 'Q', 5: 'K'}

        # Place white pieces
        for piece_type, square in zip(self.material.white_pieces, w_sq):
            rank = square // 8
            file = square % 8
            board[rank][file] = piece_chars[piece_type]

        # Place black pieces
        for piece_type, square in zip(self.material.black_pieces, b_sq):
            rank = square // 8
            file = square % 8
            board[rank][file] = piece_chars[piece_type].lower()

        # Build FEN board part
        fen_parts = []
        for rank in range(7, -1, -1):  # FEN starts from rank 8
            empty_count = 0
            rank_str = ''

            for file in range(8):
                piece = board[rank][file]
                if piece == '.':
                    empty_count += 1
                else:
                    if empty_count > 0:
                        rank_str += str(empty_count)
                        empty_count = 0
                    rank_str += piece

            if empty_count > 0:
                rank_str += str(empty_count)

            fen_parts.append(rank_str)

        fen_board = '/'.join(fen_parts)

        # Add other FEN components
        stm_char = 'w' if stm == 0 else 'b'

        # En passant
        if ep > 0 and ep <= 8:
            ep_file = chr(ord('a') + ep - 1)
            ep_rank = '3' if stm == 1 else '6'  # Opposite of side to move
            ep_str = ep_file + ep_rank
        else:
            ep_str = '-'

        return f"{fen_board} {stm_char} - {ep_str} 0 1"

    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about tablebase contents."""
        return self.storage.get_stats()

    def find_unique_positions(self, dtm: int, max_results: int = 10) -> List[SearchResult]:
        """
        Find interesting/unique positions at a given DTM.

        Looks for positions with unusual characteristics.
        """
        results = self.search(dtm=dtm, position_type="helpmate", max_results=max_results * 10)

        # For now, just return first max_results
        # TODO: Add scoring for "interestingness"
        return results[:max_results]

    def export_to_pgn(self, results: List[SearchResult], output_path: Path):
        """
        Export search results to PGN format.

        Args:
            results: List of search results
            output_path: Output PGN file path
        """
        with open(output_path, 'w') as f:
            for i, result in enumerate(results):
                f.write(f"[Event \"Tablebase Position {i+1}\"]\n")
                f.write(f"[Site \"ChessMG Tablebase\"]\n")
                f.write(f"[FEN \"{result.fen}\"]\n")
                f.write(f"[DTM \"{result.dtm}\"]\n")
                f.write(f"[Value \"{result.value.name}\"]\n")
                f.write(f"[Index \"{result.index}\"]\n")
                f.write(f"\n")

        print(f"Exported {len(results)} positions to {output_path}")

    def close(self):
        """Close the tablebase."""
        self.storage.close()


def main():
    """Run tablebase search with command-line arguments."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Search ChessMG tablebases for positions with specific properties",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find all helpmate-in-3 positions
  python search_tablebase.py tablebases/KPvK.cmgtb --dtm 3

  # Find helpmate-in-2-4 with white to move
  python search_tablebase.py tablebases/KPvK.cmgtb --dtm-range 2 4 --side white

  # Find positions with 2+ solution paths
  python search_tablebase.py tablebases/KPvK.cmgtb --min-solutions 2

  # Export to PGN
  python search_tablebase.py tablebases/KPvK.cmgtb --dtm 3 --export results.pgn
        """
    )

    parser.add_argument('tablebase', type=Path, help='Path to tablebase file')
    parser.add_argument('--material', type=str, help='Material signature (e.g., KPvK)')
    parser.add_argument('--dtm', type=int, help='Exact distance to mate')
    parser.add_argument('--dtm-range', nargs=2, type=int, metavar=('MIN', 'MAX'),
                       help='Range of DTM values')
    parser.add_argument('--side', choices=['white', 'black'],
                       help='Side to move filter')
    parser.add_argument('--min-solutions', type=int,
                       help='Minimum number of solution paths')
    parser.add_argument('--max-solutions', type=int,
                       help='Maximum number of solution paths')
    parser.add_argument('--type', choices=['helpmate', 'draw', 'illegal'],
                       help='Position type filter')
    parser.add_argument('--max-results', type=int, default=100,
                       help='Maximum results to return (default: 100)')
    parser.add_argument('--export', type=Path,
                       help='Export results to PGN file')
    parser.add_argument('--stats', action='store_true',
                       help='Show tablebase statistics')

    args = parser.parse_args()

    # Parse material from filename if not provided
    if args.material:
        # Parse material string
        if 'v' not in args.material:
            print(f"Error: Invalid material format: {args.material}")
            return 1

        white_str, black_str = args.material.split('v')
        piece_map = {'K': 5, 'Q': 4, 'R': 3, 'B': 2, 'N': 1, 'P': 0}

        white_pieces = [piece_map[c] for c in white_str]
        black_pieces = [piece_map[c] for c in black_str]

        material = MaterialSignature.from_pieces(white_pieces, black_pieces)
    else:
        # Try to parse from filename
        filename = args.tablebase.stem  # e.g., "KPvK"
        if 'v' in filename:
            white_str, black_str = filename.split('v')
            piece_map = {'K': 5, 'Q': 4, 'R': 3, 'B': 2, 'N': 1, 'P': 0}

            white_pieces = [piece_map[c] for c in white_str]
            black_pieces = [piece_map[c] for c in black_str]

            material = MaterialSignature.from_pieces(white_pieces, black_pieces)
        else:
            print("Error: Could not parse material from filename. Use --material")
            return 1

    # Create searcher
    searcher = TablebaseSearcher(args.tablebase, material)

    # Show statistics if requested
    if args.stats:
        print(f"\nTablebase Statistics: {material}")
        print("=" * 70)
        stats = searcher.get_statistics()
        for key, value in stats.items():
            if value > 0:
                print(f"  {key}: {value:,}")
        print("=" * 70)
        searcher.close()
        return 0

    # Build search parameters
    dtm_range = tuple(args.dtm_range) if args.dtm_range else None

    # Search
    results = searcher.search(
        dtm=args.dtm,
        dtm_range=dtm_range,
        side_to_move=args.side,
        min_solutions=args.min_solutions,
        max_solutions=args.max_solutions,
        position_type=args.type,
        max_results=args.max_results
    )

    # Display results
    print(f"\n{'='*70}")
    print(f"Search Results: {len(results)} positions")
    print(f"{'='*70}\n")

    for i, result in enumerate(results[:20]):  # Show first 20
        print(f"{i+1}. Index: {result.index}")
        print(f"   FEN: {result.fen}")
        print(f"   Value: {result.value.name}")
        if result.dtm:
            print(f"   DTM: {result.dtm}")
        print(f"   Side to move: {result.side_to_move}")
        if result.num_solutions > 0:
            print(f"   Solutions: {result.num_solutions}")
        print()

    if len(results) > 20:
        print(f"... and {len(results) - 20} more positions")

    # Export if requested
    if args.export:
        searcher.export_to_pgn(results, args.export)

    searcher.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
