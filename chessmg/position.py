"""
chessmg.position - High-level Python API for chess move generation.

This module provides a clean, Pythonic interface to the high-performance
chess move generator engine.
"""

from typing import List, Optional, Union, Tuple, Iterator
from dataclasses import dataclass
from enum import IntEnum
import warnings

# Import the Cython extension
try:
    from .libchessmg import ChessMoveGenerator, Move as CMove, COLOR, MoveFlag
except ImportError:
    from libchessmg import ChessMoveGenerator, Move as CMove, COLOR, MoveFlag


class Color(IntEnum):
    """Chess piece colors."""
    WHITE = 0
    BLACK = 1
    
    def __str__(self):
        return "white" if self == Color.WHITE else "black"


class PieceType(IntEnum):
    """Chess piece types."""
    PAWN = 0
    KNIGHT = 1
    BISHOP = 2
    ROOK = 3
    QUEEN = 4
    KING = 5


class GameState(IntEnum):
    """Game state flags."""
    CHECKMATE = 0
    STALEMATE = 2
    CHECK = 4
    NORMAL = 32
    ILLEGAL = 128


# Square name to index mapping
SQUARE_NAMES = {}
for i in range(64):
    file = chr(ord('a') + (i % 8))
    rank = str((i // 8) + 1)
    SQUARE_NAMES[f"{file}{rank}"] = i

# Reverse mapping
INDEX_TO_SQUARE = {v: k for k, v in SQUARE_NAMES.items()}


def square_to_index(square: str) -> int:
    """Convert algebraic notation to square index."""
    if square not in SQUARE_NAMES:
        raise ValueError(f"Invalid square: {square}")
    return SQUARE_NAMES[square]


def index_to_square(index: int) -> str:
    """Convert square index to algebraic notation."""
    if not 0 <= index < 64:
        raise ValueError(f"Square index must be 0-63, got {index}")
    return INDEX_TO_SQUARE[index]


# Move flag values (see MoveFlag in libchessmg) mapped to promotion piece types
_PROMOTION_FLAGS = {
    4: PieceType.KNIGHT, 12: PieceType.KNIGHT,
    5: PieceType.BISHOP, 13: PieceType.BISHOP,
    6: PieceType.ROOK, 14: PieceType.ROOK,
    7: PieceType.QUEEN, 15: PieceType.QUEEN,
}


@dataclass(frozen=True)
class Move:
    """
    Represents a chess move.
    
    Attributes:
        from_square: Source square index (0-63)
        to_square: Destination square index (0-63)
        promotion: Piece type for promotion, if applicable
    """
    from_square: int
    to_square: int
    promotion: Optional[PieceType] = None
    
    def __post_init__(self):
        if not 0 <= self.from_square < 64:
            raise ValueError(f"Invalid from_square: {self.from_square}")
        if not 0 <= self.to_square < 64:
            raise ValueError(f"Invalid to_square: {self.to_square}")
    
    @property
    def from_square_name(self) -> str:
        """Get source square in algebraic notation."""
        return index_to_square(self.from_square)
    
    @property
    def to_square_name(self) -> str:
        """Get destination square in algebraic notation."""
        return index_to_square(self.to_square)
    
    @property
    def uci(self) -> str:
        """Get move in UCI notation."""
        move_str = f"{self.from_square_name}{self.to_square_name}"
        if self.promotion is not None:
            promotion_chars = {
                PieceType.KNIGHT: 'n',
                PieceType.BISHOP: 'b',
                PieceType.ROOK: 'r',
                PieceType.QUEEN: 'q'
            }
            move_str += promotion_chars.get(self.promotion, '')
        return move_str
    
    @classmethod
    def from_uci(cls, uci: str) -> 'Move':
        """
        Create a Move from UCI notation.
        
        Args:
            uci: Move string like "e2e4" or "e7e8q"
            
        Returns:
            Move object
            
        Raises:
            ValueError: If UCI string is invalid
        """
        if len(uci) < 4 or len(uci) > 5:
            raise ValueError(f"Invalid UCI move: {uci}")
        
        from_sq = uci[:2]
        to_sq = uci[2:4]
        
        promotion = None
        if len(uci) == 5:
            promotion_map = {
                'n': PieceType.KNIGHT,
                'b': PieceType.BISHOP,
                'r': PieceType.ROOK,
                'q': PieceType.QUEEN
            }
            if uci[4] not in promotion_map:
                raise ValueError(f"Invalid promotion piece: {uci[4]}")
            promotion = promotion_map[uci[4]]
        
        return cls(
            square_to_index(from_sq),
            square_to_index(to_sq),
            promotion
        )
    
    def __str__(self):
        return self.uci
    
    def __repr__(self):
        return f"Move('{self.uci}')"


class ChessPosition:
    """
    High-performance chess position representation.
    
    This class provides a clean Python interface to the fast C++ chess engine,
    offering move generation, position analysis, and game state detection.
    
    Examples:
        >>> pos = ChessPosition()
        >>> moves = pos.legal_moves()
        >>> pos.make_move("e2e4")
        >>> print(pos.fen)
    """
    
    def __init__(self, fen: str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"):
        """
        Initialize a chess position.
        
        Args:
            fen: Position in Forsyth-Edwards Notation. Defaults to starting position.
            
        Raises:
            ValueError: If FEN string is invalid or position is illegal
        """
        self._engine = ChessMoveGenerator(fen)
        self._move_history: List[Tuple[Move, str]] = []  # Store (move, previous_fen)
    
    @property
    def fen(self) -> str:
        """Get current position as FEN string."""
        return self._engine.fen()
    
    @property
    def turn(self) -> Color:
        """Get the side to move."""
        return Color(self._engine.turn())
    
    @property
    def is_check(self) -> bool:
        """Check if the current side is in check."""
        state = self._engine.state(self.turn.value)
        return state == GameState.CHECK
    
    @property
    def is_checkmate(self) -> bool:
        """Check if the position is checkmate."""
        state = self._engine.state(self.turn.value)
        return state == GameState.CHECKMATE
    
    @property
    def is_stalemate(self) -> bool:
        """Check if the position is stalemate."""
        state = self._engine.state(self.turn.value)
        return state == GameState.STALEMATE
    
    @property
    def is_game_over(self) -> bool:
        """Check if the game has ended."""
        return self.is_checkmate or self.is_stalemate
    
    def legal_moves(self) -> List[Move]:
        """
        Get all legal moves in the current position.
        
        Returns:
            List of Move objects
        """
        return [
            Move(cmove.from_square, cmove.to_square, _PROMOTION_FLAGS.get(cmove.flags))
            for cmove in self._engine.legal_moves()
        ]
    
    def make_move(self, move: Union[Move, str]) -> None:
        """
        Make a move on the board.
        
        Args:
            move: Either a Move object or UCI string like "e2e4"
            
        Raises:
            ValueError: If the move is illegal
        """
        # Store current position for undo
        current_fen = self.fen

        if isinstance(move, str):
            move = Move.from_uci(move)

        # Find the matching generated move; its flags encode capture/castle/
        # en passant/promotion semantics needed to play the move correctly
        cmove = next(
            (m for m in self._engine.legal_moves()
             if m.from_square == move.from_square
             and m.to_square == move.to_square
             and _PROMOTION_FLAGS.get(m.flags) == move.promotion),
            None
        )
        if cmove is None:
            raise ValueError(f"Illegal move: {move}")

        self._engine.play(cmove.from_square, cmove.to_square, cmove.flags)

        # Store in history
        self._move_history.append((move, current_fen))
    
    def undo_move(self) -> Optional[Move]:
        """
        Undo the last move.
        
        Returns:
            The move that was undone, or None if no moves to undo
        """
        if not self._move_history:
            return None
        
        move, previous_fen = self._move_history.pop()
        self._engine.set_fen(previous_fen)
        return move
    
    def perft(self, depth: int) -> int:
        """
        Run perft (move path enumeration) test.
        
        Args:
            depth: Search depth
            
        Returns:
            Number of leaf nodes at the given depth
        """
        if depth < 0:
            raise ValueError("Depth must be non-negative")
        return self._engine.perft(depth)
    
    def copy(self) -> 'ChessPosition':
        """Create a copy of the current position."""
        return ChessPosition(self.fen)
    
    def __str__(self) -> str:
        """Return FEN representation."""
        return self.fen
    
    def __repr__(self) -> str:
        """Return string representation."""
        return f"ChessPosition('{self.fen}')"
    
    def print_board(self) -> None:
        """Print the board to stdout."""
        self._engine.print()


# Backward compatibility wrapper
class ChessMoveGeneratorCompat(ChessMoveGenerator):
    """
    Backward compatibility wrapper for ChessMoveGenerator.
    
    This class is deprecated. Use ChessPosition instead.
    """
    
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "ChessMoveGenerator is deprecated. Use ChessPosition instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)