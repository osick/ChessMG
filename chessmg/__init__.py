"""
chessmg - High-performance chess move generator for Python.

This library provides fast chess move generation using a C++ engine,
with a clean Python API for ease of use.

Example:
    >>> from chessmg import ChessPosition
    >>> pos = ChessPosition()
    >>> moves = pos.legal_moves()
    >>> pos.make_move("e2e4")
"""

__version__ = "0.3.0"
__author__ = "Oliver Sick"
__email__ = "oliver.sick@gmail.com"

# Import new API
from .position import (
    ChessPosition,
    Move,
    Color,
    PieceType,
    GameState,
    square_to_index,
    index_to_square,
)

# Import legacy API for backward compatibility
from .libchessmg import (
    ChessMoveGenerator,
    perft,
    moves,
    COLOR,
    PC,
    SQ,
    MoveFlag,
)

# Warn about deprecated imports
import warnings

def __getattr__(name):
    """Provide deprecation warnings for old API usage."""
    deprecated_names = {
        'ChessMoveGenerator': 'Use ChessPosition instead',
        'moves': 'Use ChessPosition.legal_moves() instead',
        'perft': 'Use ChessPosition.perft() instead',
    }
    
    if name in deprecated_names:
        warnings.warn(
            f"{name} is deprecated. {deprecated_names[name]}",
            DeprecationWarning,
            stacklevel=2
        )
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Define public API
__all__ = [
    # New API (recommended)
    'ChessPosition',
    'Move',
    'Color',
    'PieceType',
    'GameState',
    'square_to_index',
    'index_to_square',
    
    # Legacy API (deprecated but available)
    'ChessMoveGenerator',
    'perft',
    'moves',
    'COLOR',
    'PC',
    'SQ',
    'MoveFlag',
]