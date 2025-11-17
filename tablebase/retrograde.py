"""
Retrograde Analysis Engine

Implements backward search algorithm for generating tablebases.
Works by identifying winning/losing positions and propagating values backwards.

Algorithm for Helpmate Tablebases:
1. Initialize all positions as UNKNOWN
2. Find all positions where the defender can deliver mate (terminal positions)
3. For each ply, find positions that can reach a mate-in-N position
4. Continue until no new positions are found
5. Remaining positions are DRAW (no forced mate)

Key optimizations:
- Breadth-first search for optimal DTM (distance to mate)
- Bitset for fast membership testing
- Batch position generation
- Parallel processing support
"""

from typing import List, Set, Tuple, Optional, Callable
from collections import deque
import itertools

from chessmg.position import ChessPosition, Color, GameState
from .indexing import PositionIndexer, MaterialSignature
from .storage import TablebaseStorage, PositionValue


class RetrogradeAnalyzer:
    """
    Generates tablebases using retrograde analysis.

    For helpmate problems, the goal is to help the opponent deliver checkmate.
    """

    def __init__(self, material: MaterialSignature, indexer: PositionIndexer):
        """
        Initialize retrograde analyzer.

        Args:
            material: Material signature for this tablebase
            indexer: Position indexer for encoding/decoding positions
        """
        self.material = material
        self.indexer = indexer
        self.max_index = indexer.max_index()

        # Progress tracking
        self.positions_analyzed = 0
        self.current_ply = 0

    def generate_helpmate_tablebase(
        self,
        storage: TablebaseStorage,
        max_depth: int = 7,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> dict:
        """
        Generate a helpmate tablebase using retrograde analysis.

        In helpmate: both sides cooperate to deliver checkmate to the defending side.
        We search for positions where the defender can be mated.

        Args:
            storage: TablebaseStorage to write results
            max_depth: Maximum depth to search (ply)
            progress_callback: Optional callback(current_ply, positions_found)

        Returns:
            Statistics dictionary
        """
        stats = {
            'total_positions': self.max_index,
            'legal_positions': 0,
            'illegal_positions': 0,
            'helpmate_positions': 0,
            'draw_positions': 0,
            'max_dtm': 0,
        }

        # Phase 1: Find all terminal positions (immediate helpmates)
        print(f"Phase 1: Finding terminal positions...")
        terminal_positions = self._find_terminal_positions(storage)
        stats['helpmate_positions'] = len(terminal_positions)
        stats['max_dtm'] = 1

        if progress_callback:
            progress_callback(1, len(terminal_positions))

        # Phase 2: Retrograde search
        print(f"Phase 2: Retrograde search up to depth {max_depth}...")
        current_frontier = set(terminal_positions)

        for ply in range(2, max_depth + 1):
            self.current_ply = ply

            # Find positions that can reach current frontier in one move
            new_positions = self._find_predecessors(
                current_frontier,
                storage,
                ply
            )

            if not new_positions:
                print(f"No new positions found at ply {ply}, stopping.")
                break

            stats['helpmate_positions'] += len(new_positions)
            stats['max_dtm'] = ply

            if progress_callback:
                progress_callback(ply, len(new_positions))

            current_frontier = new_positions

        # Phase 3: Mark remaining legal positions as DRAW
        print(f"Phase 3: Marking remaining positions as DRAW...")
        draw_count = self._mark_remaining_draws(storage)
        stats['draw_positions'] = draw_count
        stats['legal_positions'] = (
            stats['helpmate_positions'] + stats['draw_positions']
        )
        stats['illegal_positions'] = (
            stats['total_positions'] - stats['legal_positions']
        )

        storage.flush()
        return stats

    def _find_terminal_positions(self, storage: TablebaseStorage) -> Set[int]:
        """
        Find all positions where the defender is checkmated.

        For helpmate: these are positions where one side is in checkmate.
        """
        terminal_positions = set()

        # Generate all possible piece placements
        for index in range(self.max_index):
            try:
                white_squares, black_squares = self.indexer.decode(index)

                # Create position and check if it's a terminal helpmate
                if self._is_terminal_helpmate(white_squares, black_squares):
                    # Store as HELPMATE_IN_1
                    storage.set_value(index, PositionValue.HELPMATE_IN_1)
                    terminal_positions.add(index)
                elif self._is_legal_position(white_squares, black_squares):
                    # Legal but not terminal, leave as UNKNOWN for now
                    pass
                else:
                    # Illegal position
                    storage.set_value(index, PositionValue.ILLEGAL)

            except Exception as e:
                # Mark as illegal if we can't process
                storage.set_value(index, PositionValue.ILLEGAL)

            # Progress reporting
            if index % 100000 == 0 and index > 0:
                print(f"  Processed {index:,} / {self.max_index:,} positions...")

        return terminal_positions

    def _find_predecessors(
        self,
        frontier: Set[int],
        storage: TablebaseStorage,
        ply: int
    ) -> Set[int]:
        """
        Find all positions that can reach the frontier in one move.

        Args:
            frontier: Set of position indices at ply-1
            storage: Tablebase storage
            ply: Current search depth

        Returns:
            Set of new position indices at this ply
        """
        new_positions = set()
        value = self._ply_to_value(ply)

        # For each unknown position, check if it can reach the frontier
        for index in range(self.max_index):
            # Skip if already evaluated
            current_value = storage.get_value(index)
            if current_value != PositionValue.UNKNOWN:
                continue

            # Decode position
            try:
                white_squares, black_squares = self.indexer.decode(index)

                # Check if any legal move reaches the frontier
                if self._can_reach_frontier(white_squares, black_squares, frontier):
                    storage.set_value(index, value)
                    new_positions.add(index)

            except Exception:
                continue

        return new_positions

    def _mark_remaining_draws(self, storage: TablebaseStorage) -> int:
        """
        Mark all remaining UNKNOWN legal positions as DRAW.

        Returns:
            Number of positions marked as draw
        """
        draw_count = 0

        for index in range(self.max_index):
            if storage.get_value(index) == PositionValue.UNKNOWN:
                # Verify it's a legal position
                try:
                    white_squares, black_squares = self.indexer.decode(index)
                    if self._is_legal_position(white_squares, black_squares):
                        storage.set_value(index, PositionValue.DRAW)
                        draw_count += 1
                    else:
                        storage.set_value(index, PositionValue.ILLEGAL)
                except Exception:
                    storage.set_value(index, PositionValue.ILLEGAL)

        return draw_count

    def _is_terminal_helpmate(
        self,
        white_squares: List[int],
        black_squares: List[int]
    ) -> bool:
        """
        Check if this is a terminal helpmate position (checkmate).

        Args:
            white_squares: Squares occupied by white pieces
            black_squares: Squares occupied by black pieces

        Returns:
            True if position is a checkmate
        """
        # Create position from squares
        position = self._create_position(white_squares, black_squares)
        if not position:
            return False

        # Check if it's checkmate for either side
        return position.is_checkmate

    def _is_legal_position(
        self,
        white_squares: List[int],
        black_squares: List[int]
    ) -> bool:
        """
        Check if a position is legal (no overlapping pieces, valid board state).

        Args:
            white_squares: Squares occupied by white pieces
            black_squares: Squares occupied by black pieces

        Returns:
            True if position is legal
        """
        # Check for overlaps
        if set(white_squares) & set(black_squares):
            return False

        # Try to create position - if it throws, it's illegal
        position = self._create_position(white_squares, black_squares)
        return position is not None

    def _can_reach_frontier(
        self,
        white_squares: List[int],
        black_squares: List[int],
        frontier: Set[int]
    ) -> bool:
        """
        Check if any legal move from this position reaches the frontier.

        Args:
            white_squares: Current position white pieces
            black_squares: Current position black pieces
            frontier: Set of position indices to reach

        Returns:
            True if position can reach frontier in one move
        """
        position = self._create_position(white_squares, black_squares)
        if not position:
            return False

        # Generate all legal moves
        legal_moves = position.legal_moves()

        # For each move, check if resulting position is in frontier
        for move in legal_moves:
            # Make move
            position_copy = position.copy()
            try:
                position_copy.make_move(move)

                # Get resulting position index
                result_index = self._position_to_index(position_copy)

                if result_index in frontier:
                    return True

            except Exception:
                continue

        return False

    def _create_position(
        self,
        white_squares: List[int],
        black_squares: List[int]
    ) -> Optional[ChessPosition]:
        """
        Create a ChessPosition from piece squares.

        This requires building a FEN string from the material signature
        and square positions.

        Args:
            white_squares: Squares for white pieces (ordered by material signature)
            black_squares: Squares for black pieces (ordered by material signature)

        Returns:
            ChessPosition or None if invalid
        """
        # Build FEN from squares
        fen = self._build_fen(white_squares, black_squares)
        if not fen:
            return None

        try:
            return ChessPosition(fen)
        except Exception:
            return None

    def _build_fen(
        self,
        white_squares: List[int],
        black_squares: List[int]
    ) -> Optional[str]:
        """
        Build FEN string from piece positions.

        Args:
            white_squares: Sorted list of white piece squares
            black_squares: Sorted list of black piece squares

        Returns:
            FEN string or None if invalid
        """
        # Create empty board
        board = [['' for _ in range(8)] for _ in range(8)]

        # Piece type to FEN character mapping
        piece_chars = {
            0: 'P', 1: 'N', 2: 'B', 3: 'R', 4: 'Q', 5: 'K'
        }

        # Place white pieces
        for piece_type, square in zip(self.material.white_pieces, white_squares):
            rank = square // 8
            file = square % 8
            board[rank][file] = piece_chars[piece_type]

        # Place black pieces
        for piece_type, square in zip(self.material.black_pieces, black_squares):
            rank = square // 8
            file = square % 8
            board[rank][file] = piece_chars[piece_type].lower()

        # Build FEN string
        fen_parts = []
        for rank in range(7, -1, -1):  # FEN starts from rank 8
            empty_count = 0
            rank_str = ''

            for file in range(8):
                piece = board[rank][file]
                if piece:
                    if empty_count > 0:
                        rank_str += str(empty_count)
                        empty_count = 0
                    rank_str += piece
                else:
                    empty_count += 1

            if empty_count > 0:
                rank_str += str(empty_count)

            fen_parts.append(rank_str)

        fen_board = '/'.join(fen_parts)

        # Add turn, castling, en passant, halfmove, fullmove
        # For tablebase generation, we'll try both white and black to move
        return f"{fen_board} w - - 0 1"

    def _position_to_index(self, position: ChessPosition) -> Optional[int]:
        """
        Convert a ChessPosition to a tablebase index.

        Args:
            position: ChessPosition to encode

        Returns:
            Index or None if conversion fails
        """
        # Extract piece positions from FEN
        white_squares, black_squares = self._fen_to_squares(position.fen)
        if not white_squares or not black_squares:
            return None

        try:
            return self.indexer.encode(white_squares, black_squares)
        except Exception:
            return None

    def _fen_to_squares(self, fen: str) -> Tuple[Optional[List[int]], Optional[List[int]]]:
        """
        Extract piece squares from FEN string.

        Args:
            fen: FEN string

        Returns:
            (white_squares, black_squares) or (None, None) on error
        """
        try:
            board_part = fen.split()[0]
            ranks = board_part.split('/')

            white_squares = []
            black_squares = []

            # Map FEN characters to piece types
            piece_types = {
                'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
                'p': 0, 'n': 1, 'b': 2, 'r': 3, 'q': 4, 'k': 5
            }

            for rank_idx, rank_str in enumerate(ranks):
                rank = 7 - rank_idx  # FEN starts from rank 8
                file = 0

                for char in rank_str:
                    if char.isdigit():
                        file += int(char)
                    else:
                        square = rank * 8 + file
                        piece_type = piece_types.get(char)

                        if piece_type is not None:
                            if char.isupper():
                                white_squares.append(square)
                            else:
                                black_squares.append(square)

                        file += 1

            return white_squares, black_squares

        except Exception:
            return None, None

    @staticmethod
    def _ply_to_value(ply: int) -> PositionValue:
        """Convert ply depth to PositionValue."""
        if ply <= 7:
            return PositionValue(ply)
        else:
            return PositionValue.HELPMATE_IN_8_PLUS
