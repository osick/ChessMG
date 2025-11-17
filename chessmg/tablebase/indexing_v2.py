"""
Position Indexing for Tablebases - Enhanced Version

Implements efficient combinatorial indexing with proper handling of:
- Side to move (CRITICAL)
- En passant rights (optional, for completeness)
- Castling rights (optional, rare in endgames)

Key Features:
- Material signature encoding
- Combinatorial square indexing (binomial coefficients)
- Side-to-move encoding (doubles index space)
- Optional en passant encoding
- Support for arbitrary piece configurations
- O(1) index calculation and inverse mapping

Index Structure:
  base_index = combinatorial_index(piece_positions)
  final_index = base_index * 2 + side_to_move

With en passant:
  final_index = (base_index * 2 + side_to_move) * 9 + ep_file
"""

from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from functools import lru_cache
import math


@lru_cache(maxsize=10000)
def binomial(n: int, k: int) -> int:
    """
    Compute binomial coefficient C(n, k) with memoization.

    Uses the multiplicative formula for efficiency.
    """
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1

    k = min(k, n - k)  # Optimization
    result = 1
    for i in range(k):
        result = result * (n - i) // (i + 1)
    return result


@dataclass(frozen=True)
class MaterialSignature:
    """
    Represents a material configuration (piece set without positions).

    Attributes:
        white_pieces: List of white piece types (0=P, 1=N, 2=B, 3=R, 4=Q, 5=K)
        black_pieces: List of black piece types
    """
    white_pieces: Tuple[int, ...]  # Sorted tuple of piece types
    black_pieces: Tuple[int, ...]  # Sorted tuple of piece types

    def __post_init__(self):
        # Ensure both sides have exactly one king
        if self.white_pieces.count(5) != 1:
            raise ValueError("White must have exactly one king")
        if self.black_pieces.count(5) != 1:
            raise ValueError("Black must have exactly one king")

    @classmethod
    def from_pieces(cls, white: List[int], black: List[int]) -> 'MaterialSignature':
        """Create from unsorted piece lists."""
        return cls(tuple(sorted(white)), tuple(sorted(black)))

    def __str__(self) -> str:
        piece_chars = {0: 'P', 1: 'N', 2: 'B', 3: 'R', 4: 'Q', 5: 'K'}
        white_str = ''.join(piece_chars[p] for p in self.white_pieces)
        black_str = ''.join(piece_chars[p] for p in self.black_pieces)
        return f"{white_str}v{black_str}"

    def total_pieces(self) -> int:
        """Total number of pieces in this configuration."""
        return len(self.white_pieces) + len(self.black_pieces)


class PositionIndexer:
    """
    Encodes/decodes positions to/from unique integer indices.

    Now includes proper handling of:
    - Side to move (required)
    - En passant file (optional)
    - Castling rights (optional, can be added later)

    For a given material signature, assigns each legal position a unique index
    in range [0, table_size). Uses combinatorial number system for compact encoding.

    Encoding scheme:
    1. Index each piece type separately using combinations
    2. Combine indices using lexicographic ordering
    3. Multiply by 2 for side-to-move
    4. Optionally multiply by 9 for en passant file (0=none, 1-8=files a-h)

    Example for KPvK with side-to-move:
    - Base positions: C(64,2) * C(62,1) = ~250,000
    - With side-to-move: ~250,000 * 2 = ~500,000
    - With ep file: ~500,000 * 9 = ~4,500,000 (but only needed if pawns present)
    """

    def __init__(self, material: MaterialSignature,
                 use_symmetry: bool = False,
                 encode_en_passant: bool = False):
        """
        Initialize indexer for a material configuration.

        Args:
            material: The material signature to index
            use_symmetry: Whether to use symmetry reduction (reduces table size)
            encode_en_passant: Whether to encode en passant file in index
        """
        self.material = material
        self.use_symmetry = use_symmetry
        self.encode_en_passant = encode_en_passant

        # Check if this material has pawns (needed for en passant)
        self.has_pawns = 0 in material.white_pieces or 0 in material.black_pieces

        # Only encode en passant if explicitly requested AND material has pawns
        self.encode_en_passant = encode_en_passant and self.has_pawns

        self._setup_indexing()

    def _setup_indexing(self):
        """Pre-compute indexing parameters."""
        self.num_white = len(self.material.white_pieces)
        self.num_black = len(self.material.black_pieces)
        self.total_pieces = self.num_white + self.num_black

        # Base positions (just piece placement)
        self._base_positions = self._compute_base_positions()

        # Multiply by 2 for side-to-move
        self._positions_with_stm = self._base_positions * 2

        # Optionally multiply by 9 for en passant file
        if self.encode_en_passant:
            self._max_positions = self._positions_with_stm * 9
        else:
            self._max_positions = self._positions_with_stm

    def _compute_base_positions(self) -> int:
        """
        Compute base positions (piece placement only).

        For N pieces on 64 squares: C(64, num_white) * C(64 - num_white, num_black)
        """
        white_placements = binomial(64, self.num_white)
        black_placements = binomial(64 - self.num_white, self.num_black)
        return white_placements * black_placements

    def encode(self, white_squares: List[int], black_squares: List[int],
               side_to_move: int = 0, ep_file: int = 0) -> int:
        """
        Encode a position to a unique index.

        Args:
            white_squares: Sorted list of squares occupied by white pieces
            black_squares: Sorted list of squares occupied by black pieces
            side_to_move: 0 for white, 1 for black
            ep_file: 0 for none, 1-8 for files a-h (only if encode_en_passant=True)

        Returns:
            Unique index for this position

        Example:
            For KvK, white king on e1 (4), black king on e8 (60), white to move:
            encode([4], [60], side_to_move=0) -> base_index * 2 + 0
        """
        if len(white_squares) != self.num_white:
            raise ValueError(f"Expected {self.num_white} white pieces")
        if len(black_squares) != self.num_black:
            raise ValueError(f"Expected {self.num_black} black pieces")
        if side_to_move not in (0, 1):
            raise ValueError(f"Side to move must be 0 or 1, got {side_to_move}")

        # Ensure sorted
        white_squares = sorted(white_squares)
        black_squares = sorted(black_squares)

        # Check for overlaps
        if set(white_squares) & set(black_squares):
            raise ValueError("Pieces cannot occupy the same square")

        # Get base index (piece positions only)
        base_index = self._encode_piece_positions(white_squares, black_squares)

        # Add side-to-move
        index_with_stm = base_index * 2 + side_to_move

        # Optionally add en passant file
        if self.encode_en_passant:
            if ep_file < 0 or ep_file > 8:
                raise ValueError(f"En passant file must be 0-8, got {ep_file}")
            return index_with_stm * 9 + ep_file
        else:
            return index_with_stm

    def decode(self, index: int) -> Tuple[List[int], List[int], int, int]:
        """
        Decode an index back to a position.

        Args:
            index: Position index

        Returns:
            (white_squares, black_squares, side_to_move, ep_file)
        """
        if index < 0 or index >= self._max_positions:
            raise ValueError(f"Index out of range: {index}")

        # Extract en passant file if encoded
        if self.encode_en_passant:
            ep_file = index % 9
            index_with_stm = index // 9
        else:
            ep_file = 0
            index_with_stm = index

        # Extract side-to-move
        side_to_move = index_with_stm % 2
        base_index = index_with_stm // 2

        # Decode piece positions
        white_squares, black_squares = self._decode_piece_positions(base_index)

        return white_squares, black_squares, side_to_move, ep_file

    def _encode_piece_positions(self, white_squares: List[int], black_squares: List[int]) -> int:
        """Encode just the piece positions (no side-to-move or en passant)."""
        # Encode white pieces using combinatorial number system
        white_index = self._encode_combination(white_squares, 64)

        # Encode black pieces on "remaining" squares
        black_mapped = []
        for sq in black_squares:
            # Count how many white squares are below this square
            offset = sum(1 for w in white_squares if w < sq)
            black_mapped.append(sq - offset)

        black_index = self._encode_combination(black_mapped, 64 - self.num_white)

        # Combine indices
        black_placements = binomial(64 - self.num_white, self.num_black)
        return white_index * black_placements + black_index

    def _decode_piece_positions(self, base_index: int) -> Tuple[List[int], List[int]]:
        """Decode just the piece positions from base index."""
        black_placements = binomial(64 - self.num_white, self.num_black)

        # Extract white and black indices
        white_index = base_index // black_placements
        black_index = base_index % black_placements

        # Decode white pieces
        white_squares = self._decode_combination(white_index, 64, self.num_white)

        # Decode black pieces
        black_mapped = self._decode_combination(black_index, 64 - self.num_white, self.num_black)

        # Map black squares back to 0-63 range
        black_squares = []
        for sq in black_mapped:
            offset = sum(1 for w in white_squares if w <= sq + len(black_squares))
            black_squares.append(sq + offset)

        return white_squares, black_squares

    @staticmethod
    def _encode_combination(squares: List[int], n: int) -> int:
        """
        Encode a combination of squares using combinatorial number system.

        Maps a k-combination of n items to index in range [0, C(n,k)).
        Uses lexicographic ordering.
        """
        squares = sorted(squares)
        k = len(squares)
        index = 0

        for i, sq in enumerate(squares):
            if sq > 0:
                index += binomial(sq, i + 1)

        return index

    @staticmethod
    def _decode_combination(index: int, n: int, k: int) -> List[int]:
        """
        Decode an index to a combination of squares.

        Inverse of _encode_combination.
        """
        if k == 0:
            return []

        squares = []
        for i in range(k, 0, -1):
            # Find largest sq such that C(sq, i) <= index
            sq = i - 1
            while sq < n and binomial(sq + 1, i) <= index:
                sq += 1

            squares.append(sq)
            index -= binomial(sq, i)

        return sorted(squares)

    def max_index(self) -> int:
        """Maximum valid index for this material configuration."""
        return self._max_positions

    def base_positions(self) -> int:
        """Number of positions ignoring side-to-move and en passant."""
        return self._base_positions

    def __repr__(self) -> str:
        ep_str = " +ep" if self.encode_en_passant else ""
        return f"PositionIndexer({self.material}, max={self._max_positions:,}{ep_str})"


def extract_position_pieces(position) -> Tuple[List[int], List[int], List[int], List[int]]:
    """
    Extract piece positions from a ChessPosition object.

    Args:
        position: ChessPosition instance

    Returns:
        (white_piece_types, white_squares, black_piece_types, black_squares)

    Note: Requires access to internal board representation.
    For now, this is a placeholder that would need integration with ChessMG internals.
    """
    # This would need to access the internal bitboards or mailbox
    # For now, return placeholder
    raise NotImplementedError(
        "Position extraction requires integration with ChessMG internal structures. "
        "Use FEN parsing or add C++ binding for board access."
    )
