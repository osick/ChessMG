"""
Position Indexing for Tablebases

Implements efficient combinatorial indexing to map chess positions to unique indices.
Uses binomial coefficients for compact representation of piece placements.

Key Features:
- Material signature encoding
- Combinatorial square indexing (binomial coefficients)
- Support for arbitrary piece configurations
- O(1) index calculation and inverse mapping
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

    For a given material signature, assigns each legal position a unique index
    in range [0, table_size). Uses combinatorial number system for compact encoding.

    Encoding scheme:
    1. Index each piece type separately using combinations
    2. Combine indices using lexicographic ordering
    3. Handle symmetries (optional) for further compression

    Example for KPvK (White: King+Pawn, Black: King):
    - 64 positions for white king
    - 48 positions for white pawn (not on rank 1 or 8)
    - 62 positions for black king (cannot be on white king square)
    - Total: ~190,000 positions with constraints
    """

    def __init__(self, material: MaterialSignature, use_symmetry: bool = False):
        """
        Initialize indexer for a material configuration.

        Args:
            material: The material signature to index
            use_symmetry: Whether to use symmetry reduction (reduces table size)
        """
        self.material = material
        self.use_symmetry = use_symmetry
        self._setup_indexing()

    def _setup_indexing(self):
        """Pre-compute indexing parameters."""
        # For now, simple implementation without pawn/symmetry constraints
        # Can be optimized later with rank restrictions for pawns

        self.num_white = len(self.material.white_pieces)
        self.num_black = len(self.material.black_pieces)
        self.total_pieces = self.num_white + self.num_black

        # Maximum table size (upper bound, actual size may be smaller)
        # This is C(64, num_white) * C(64 - num_white, num_black)
        self._max_positions = self._compute_max_positions()

    def _compute_max_positions(self) -> int:
        """
        Compute theoretical maximum positions.

        For N pieces on 64 squares: C(64, N) * N! / (permutation symmetries)
        Simplified: place pieces sequentially with combinations
        """
        # Place white pieces: C(64, num_white)
        white_placements = binomial(64, self.num_white)

        # Place black pieces on remaining squares: C(64 - num_white, num_black)
        black_placements = binomial(64 - self.num_white, self.num_black)

        return white_placements * black_placements

    def encode(self, white_squares: List[int], black_squares: List[int]) -> int:
        """
        Encode a position to a unique index.

        Args:
            white_squares: Sorted list of squares occupied by white pieces
            black_squares: Sorted list of squares occupied by black pieces

        Returns:
            Unique index for this position

        Example:
            For KvK, white king on e1 (4), black king on e8 (60):
            encode([4], [60]) -> some unique index
        """
        if len(white_squares) != self.num_white:
            raise ValueError(f"Expected {self.num_white} white pieces")
        if len(black_squares) != self.num_black:
            raise ValueError(f"Expected {self.num_black} black pieces")

        # Ensure sorted
        white_squares = sorted(white_squares)
        black_squares = sorted(black_squares)

        # Check for overlaps
        if set(white_squares) & set(black_squares):
            raise ValueError("Pieces cannot occupy the same square")

        # Encode white pieces using combinatorial number system
        white_index = self._encode_combination(white_squares, 64)

        # Encode black pieces on "remaining" squares
        # Map black squares to 0-63 range excluding white squares
        black_mapped = []
        for sq in black_squares:
            # Count how many white squares are below this square
            offset = sum(1 for w in white_squares if w < sq)
            black_mapped.append(sq - offset)

        black_index = self._encode_combination(black_mapped, 64 - self.num_white)

        # Combine indices: white_index * black_placements + black_index
        black_placements = binomial(64 - self.num_white, self.num_black)
        return white_index * black_placements + black_index

    def decode(self, index: int) -> Tuple[List[int], List[int]]:
        """
        Decode an index back to a position.

        Args:
            index: Position index

        Returns:
            (white_squares, black_squares) as sorted lists
        """
        if index < 0 or index >= self._max_positions:
            raise ValueError(f"Index out of range: {index}")

        black_placements = binomial(64 - self.num_white, self.num_black)

        # Extract white and black indices
        white_index = index // black_placements
        black_index = index % black_placements

        # Decode white pieces
        white_squares = self._decode_combination(white_index, 64, self.num_white)

        # Decode black pieces
        black_mapped = self._decode_combination(black_index, 64 - self.num_white, self.num_black)

        # Map black squares back to 0-63 range
        black_squares = []
        for sq in black_mapped:
            # Add back the offset from white pieces
            offset = sum(1 for w in white_squares if w <= sq + len(black_squares))
            black_squares.append(sq + offset)

        return white_squares, black_squares

    @staticmethod
    def _encode_combination(squares: List[int], n: int) -> int:
        """
        Encode a combination of squares using combinatorial number system.

        Maps a k-combination of n items to index in range [0, C(n,k)).
        Uses lexicographic ordering.

        Example: squares=[2,5,7] with n=10, k=3
        """
        squares = sorted(squares)
        k = len(squares)
        index = 0

        for i, sq in enumerate(squares):
            # Add number of combinations with smaller elements at position i
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

    def __repr__(self) -> str:
        return f"PositionIndexer({self.material}, max_positions={self._max_positions:,})"


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
