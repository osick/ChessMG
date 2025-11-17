# cython: language_level=3
# cython: c_string_type=unicode, c_string_encoding=utf8
# distutils: language=c++

import sys
from libcpp cimport bool
from libcpp.string cimport string
from libcpp.vector cimport vector
from libc.stdint cimport int64_t, uint64_t, uint8_t
from enum import Enum, auto
import numpy as np
cimport numpy as np

from libcpp.pair cimport pair as cpair
ctypedef cpair[int, int] ipair

# Import numpy array API
np.import_array()

class COLOR(Enum):
    WHITE = 0
    BLACK = 1

class PC(Enum):
    P=0; N=1; B=2; R=3; Q=4; K=5; p=8; n=9; b=10; r=11; q=12; k=13
    NO_PIECE=14

class SQ(Enum): 
    a1=0; b1=auto(); c1=auto(); d1=auto(); e1=auto(); f1=auto(); g1=auto(); h1=auto()
    a2=auto(); b2=auto(); c2=auto(); d2=auto(); e2=auto(); f2=auto(); g2=auto(); h2=auto()
    a3=auto(); b3=auto(); c3=auto(); d3=auto(); e3=auto(); f3=auto(); g3=auto(); h3=auto()
    a4=auto(); b4=auto(); c4=auto(); d4=auto(); e4=auto(); f4=auto(); g4=auto(); h4=auto()
    a5=auto(); b5=auto(); c5=auto(); d5=auto(); e5=auto(); f5=auto(); g5=auto(); h5=auto()
    a6=auto(); b6=auto(); c6=auto(); d6=auto(); e6=auto(); f6=auto(); g6=auto(); h6=auto()
    a7=auto(); b7=auto(); c7=auto(); d7=auto(); e7=auto(); f7=auto(); g7=auto(); h7=auto()
    a8=auto(); b8=auto(); c8=auto(); d8=auto(); e8=auto(); f8=auto(); g8=auto(); h8=auto()
    NO_SQUARE=auto()

# Move flags constants for better API
class MoveFlag(Enum):
    QUIET = 0
    DOUBLE_PUSH = 1
    OO = 2  # King-side castle
    OOO = 3  # Queen-side castle
    CAPTURE = 8
    EN_PASSANT = 10
    PROMOTION_KNIGHT = 4
    PROMOTION_BISHOP = 5
    PROMOTION_ROOK = 6
    PROMOTION_QUEEN = 7
    CAPTURE_PROMOTION_KNIGHT = 12
    CAPTURE_PROMOTION_BISHOP = 13
    CAPTURE_PROMOTION_ROOK = 14
    CAPTURE_PROMOTION_QUEEN = 15

cdef extern from "libcmg.h" namespace "cmg":
    cdef cppclass CMGPosition:
        CMGPosition() except +
        CMGPosition(string fen) except +
        CMGPosition(vector[ipair] piecelist, bool turn, int epsq, string castling) except +
        string fen()
        void set_fen(string fen)
        void print()
        int turn()
        bool is_legal()
        uint8_t state(int c)
        vector[int] moves(int color)              
        int64_t perft(int depth)        
        void move_piece(int _from, int _to)
    cdef string sqstr(int idx)

cdef class Move:
    """Represents a chess move with from square, to square, and move type."""
    cdef readonly int from_square
    cdef readonly int to_square
    cdef readonly int flags
    
    def __init__(self, int from_square, int to_square, int flags):
        self.from_square = from_square
        self.to_square = to_square
        self.flags = flags
    
    @property
    def from_square_str(self):
        """Get from square in algebraic notation."""
        return sqstr(self.from_square)
    
    @property
    def to_square_str(self):
        """Get to square in algebraic notation."""
        return sqstr(self.to_square)
    
    @property
    def uci(self):
        """Get move in UCI notation."""
        move_str = f"{self.from_square_str}{self.to_square_str}"
        # Add promotion piece if needed
        if self.flags in [4, 5, 6, 7, 12, 13, 14, 15]:
            promotion_pieces = {4: 'n', 5: 'b', 6: 'r', 7: 'q',
                              12: 'n', 13: 'b', 14: 'r', 15: 'q'}
            move_str += promotion_pieces.get(self.flags, '')
        return move_str
    
    @property
    def move_type(self):
        """Get the type of move as MoveFlag enum."""
        return MoveFlag(self.flags)
    
    @property
    def is_capture(self):
        """Check if move is a capture."""
        return self.flags >= 8
    
    @property
    def is_promotion(self):
        """Check if move is a promotion."""
        return self.flags in [4, 5, 6, 7, 12, 13, 14, 15]
    
    @property
    def is_castle(self):
        """Check if move is castling."""
        return self.flags in [2, 3]
    
    @property
    def is_en_passant(self):
        """Check if move is en passant."""
        return self.flags == 10
    
    def __repr__(self):
        return f"Move({self.from_square_str}->{self.to_square_str}, type={self.move_type.name})"
    
    def __str__(self):
        return self.uci

cdef class ChessMoveGenerator:
    cdef CMGPosition* _pos
    cdef bint _initialized
    
    def __cinit__(self):
        self._pos = NULL
        self._initialized = False
    
    def __init__(self, input=None):
        """Initialize chess position from FEN string or position dict.
        
        Args:
            input: Either a FEN string or dict with position data
                  Dict format: {"position": [(piece, square)...], "turn": bool, "epsq": int, "castling": str}
                  
        Raises:
            ValueError: If input format is invalid or position is illegal
            TypeError: If input type is not supported
        """
        cdef string fen_str
        
        if self._initialized:
            raise RuntimeError("ChessMoveGenerator already initialized")
        
        try:
            if input is None:
                self._pos = new CMGPosition()
            elif isinstance(input, str):
                # Input is FEN string
                fen_str = input.encode('utf-8')
                self._pos = new CMGPosition(fen_str)
                if not self._pos.is_legal():
                    raise ValueError(f"Invalid position from FEN: {input}")
            elif isinstance(input, dict):
                # Validate dict structure
                pos = []
                turn = input.get("turn", True)
                epsq = int(input.get("epsq", 64))
                castling = str(input.get("castling", ""))
                
                if "raw" in input:
                    pos = input["raw"]
                elif "position" in input:
                    try:
                        pos = [(PC[it[0]].value, SQ[it[1]].value) for it in input["position"]]
                    except (KeyError, ValueError) as e:
                        raise ValueError(f"Invalid piece or square in position dict: {e}")
                else:
                    raise ValueError("Dict must contain either 'raw' or 'position' key")
                
                self._pos = new CMGPosition(pos, turn, epsq, castling)
                if not self._pos.is_legal():
                    raise ValueError("Invalid position from dict input")
            else:
                raise TypeError(f"Invalid input type: {type(input)}. Expected str, dict or None")
                
            self._initialized = True
            
        except Exception as e:
            if self._pos != NULL:
                del self._pos
                self._pos = NULL
            raise

    def set_fen(self, str fen):
        """Set position from FEN string.
        
        Args:
            fen: Position in Forsyth-Edwards Notation
            
        Raises:
            ValueError: If FEN is invalid
        """
        if not self._initialized:
            raise RuntimeError("ChessMoveGenerator not initialized")
        
        cdef string fen_str = fen.encode('utf-8')
        self._pos.set_fen(fen_str)
        if not self._pos.is_legal():
            raise ValueError(f"Invalid FEN: {fen}")

    def __dealloc__(self):
        if self._pos != NULL:
            del self._pos
            self._pos = NULL

    def fen(self):
        """Get current position as FEN string."""
        if not self._initialized:
            raise RuntimeError("ChessMoveGenerator not initialized")
        return self._pos.fen()
    
    def print(self):
        """Print the board to stdout."""
        if not self._initialized:
            raise RuntimeError("ChessMoveGenerator not initialized")
        return self._pos.print()
    
    def turn(self):
        """Get current turn (0=white, 1=black)."""
        if not self._initialized:
            raise RuntimeError("ChessMoveGenerator not initialized")
        return self._pos.turn()
    
    def move_piece(self, int _from, int _to):
        """Move a piece from one square to another.
        
        Args:
            _from: Source square (0-63)
            _to: Destination square (0-63)
            
        Raises:
            ValueError: If squares are out of bounds
        """
        if not self._initialized:
            raise RuntimeError("ChessMoveGenerator not initialized")
        
        if not (0 <= _from < 64 and 0 <= _to < 64):
            raise ValueError(f"Square indices must be 0-63, got from={_from}, to={_to}")
            
        self._pos.move_piece(_from, _to)
    
    def perft(self, int depth):
        """Run perft test to given depth."""
        if not self._initialized:
            raise RuntimeError("ChessMoveGenerator not initialized")
        
        if depth < 0:
            raise ValueError(f"Depth must be non-negative, got {depth}")
            
        return self._pos.perft(depth)
    
    def is_legal(self):
        """Check if current position is legal."""
        if not self._initialized:
            raise RuntimeError("ChessMoveGenerator not initialized")
        return self._pos.is_legal()
    
    def state(self, color):
        """Get position state for given color."""
        if not self._initialized:
            raise RuntimeError("ChessMoveGenerator not initialized")
        return self._pos.state(color)
    
    def moves(self, as_string=False, color=None, return_objects=False):
        """Generate all legal moves for the position.
        
        Args:
            as_string: Return moves in algebraic notation if True
            color: Side to move (0=white, 1=black), defaults to current turn
            return_objects: Return Move objects if True (new API)
            
        Returns:
            If return_objects=True: List of Move objects
            If as_string=True: List of move strings like "e2-e4"
            Otherwise: numpy array of shape (n_moves, 3) with columns [from, to, flags]
        """
        if not self._initialized:
            raise RuntimeError("ChessMoveGenerator not initialized")
            
        if color is None:
            color = self._pos.turn()

        cdef vector[int] raw_moves = self._pos.moves(color)
        cdef int n_moves
        cdef int i
        cdef np.ndarray[np.int32_t, ndim=2] moves_array

        # Return empty result if no moves
        if raw_moves.size() == 0:
            if return_objects:
                return []
            elif as_string:
                return []
            else:
                return np.empty((0, 3), dtype=np.int32)
        
        # New API: Return Move objects
        if return_objects:
            moves_list = []
            for i in range(0, raw_moves.size(), 3):
                moves_list.append(Move(raw_moves[i], raw_moves[i+1], raw_moves[i+2]))
            return moves_list
        
        # Legacy string API
        elif as_string:
            moves_list = []
            for i in range(0, raw_moves.size(), 3):
                moves_list.append(f"{sqstr(raw_moves[i])}-{sqstr(raw_moves[i+1])}")
            return moves_list
        
        # Improved array API: Return properly shaped numpy array
        else:
            # Convert to numpy array and reshape
            n_moves = raw_moves.size() // 3
            moves_array = np.empty((n_moves, 3), dtype=np.int32)

            for i in range(n_moves):
                moves_array[i, 0] = raw_moves[i * 3]
                moves_array[i, 1] = raw_moves[i * 3 + 1]
                moves_array[i, 2] = raw_moves[i * 3 + 2]

            return moves_array
    
    def legal_moves(self):
        """Get legal moves as Move objects (new preferred API)."""
        return self.moves(return_objects=True)

# Global functions for backward compatibility
def moves(str fen, bool w):
    """Generate moves for a position (legacy API)."""
    position = ChessMoveGenerator(fen)
    return position.moves(color=(0 if w == True else 1))
    
def perft(fen, depth):
    """Run perft test (legacy API)."""
    position = ChessMoveGenerator(fen)
    return position.perft(depth)