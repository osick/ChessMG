# ChessMG Codebase Architecture Analysis

## Project Overview
ChessMG is a high-performance chess move generation library for Python that combines a C++ engine (libsurge) with Python bindings via Cython. It achieves 250M+ moves per second with sophisticated move generation and position management.

---

## 1. Position Representation and Encoding

### Core Data Structures (libsurge.h/cpp)

#### Bitboard Representation
- **Type**: `uint64_t` (Bitboard)
- **Layout**: 64-bit integer representing 8x8 chessboard
  - Bit position = square index (0-63)
  - a1=0, h1=7, a8=56, h8=63
  
#### Position Class (libsurge.h:362-423)
```cpp
class Position {
    Bitboard piece_bb[15];      // Bitboard for each piece type
    Piece board[64];            // Mailbox representation (piece at each square)
    Color side_to_play;         // WHITE (0) or BLACK (1)
    int game_ply;               // Current game depth
    uint64_t hash;              // Zobrist hash (incrementally updated)
    UndoInfo history[256];      // Move history for undo support
    Bitboard checkers;          // Squares attacking the king
    Bitboard pinned;            // Pinned pieces
}
```

#### Piece Encoding
```cpp
enum Piece : int {
    WHITE_PAWN=0, WHITE_KNIGHT=1, WHITE_BISHOP=2, WHITE_ROOK=3, 
    WHITE_QUEEN=4, WHITE_KING=5,
    BLACK_PAWN=8, BLACK_KNIGHT=9, BLACK_BISHOP=10, BLACK_ROOK=11, 
    BLACK_QUEEN=12, BLACK_KING=13,
    NO_PIECE=14
};
// Derived from: make_piece(Color c, PieceType pt) = (c << 3) + pt
```

#### Square Indexing
```
Rank 8: 56 57 58 59 60 61 62 63
Rank 7: 48 49 50 51 52 53 54 55
...
Rank 1: 0  1  2  3  4  5  6  7
        a  b  c  d  e  f  g  h
```

### FEN Parsing and Position Creation

**Methods** (libsurge.h:397-400):
- `Position::set(const std::string& fen, Position& p)` - Create from FEN
- `Position::set_position(vector<pair<Piece,Square>>, Color, string castlings, Square epsq, Position& p)` - Create from raw piece list
- `position.fen()` - Get FEN string representation

### Python-Level Position API

**ChessPosition class** (position.py):
- Wraps C++ `ChessMoveGenerator` 
- Provides Pythonic interface with type hints
- Stores move history for undo/redo

**Move representation**:
```python
@dataclass(frozen=True)
class Move:
    from_square: int              # 0-63
    to_square: int                # 0-63
    promotion: Optional[PieceType] # None or KNIGHT/BISHOP/ROOK/QUEEN
```

---

## 2. Move Generation System

### Magic Bitboards (Core Algorithm)

**Implementation Details**:
- Uses magic bitboards for O(1) sliding piece attacks
- Pre-computed magic numbers for rooks and bishops:
  - `ROOK_MAGICS[64]` with shift values in `ROOK_ATTACK_SHIFTS[64]`
  - `BISHOP_MAGICS[64]` with shift values in `BISHOP_ATTACK_SHIFTS[64]`
- Lookup tables:
  - `ROOK_ATTACKS[64][4096]` - Rook move database
  - `BISHOP_ATTACKS[64][512]` - Bishop move database

**Attack Generation** (libsurge.h:297-309):
```cpp
// Compile-time templated attack generation
template<PieceType P>
constexpr Bitboard attacks(Square s, Bitboard occ)
// Returns valid attacks for piece type at square with occupancy

get_rook_attacks(Square s, Bitboard occ)    // O(1) with magic lookup
get_bishop_attacks(Square s, Bitboard occ)  // O(1) with magic lookup
```

### Legal Move Generation

**Core Function** (libsurge.h:595-857):
```cpp
template<Color Us> Move* Position::generate_legals(Move* list)
```

**Algorithm**:
1. **Danger Zone Calculation**: Compute all squares attacked by opponent
2. **King Moves**: Generate king moves to non-attacked squares
3. **Check Detection**: Identify checking pieces and pins
4. **Move Filtering**:
   - Double check: Only king moves
   - Single check: Capture checker OR block attack
   - No check: All pseudo-legal moves that don't expose king
5. **Piece-by-Piece Generation**:
   - Non-pinned pieces: Generate normally
   - Pinned pieces: Only moves along line to king
   - Pawns: Handle promotions separately

**Move Flags** (libsurge.h:166-184):
```cpp
enum MoveFlags : int {
    QUIET = 0,          // Normal quiet move
    DOUBLE_PUSH = 1,    // Pawn double push
    OO = 2,             // Kingside castle
    OOO = 3,            // Queenside castle
    CAPTURE = 8,        // Normal capture
    EN_PASSANT = 10,    // En passant capture
    PR_KNIGHT = 4,      // Quiet promotion
    PR_BISHOP = 5,      // Quiet promotion
    PR_ROOK = 6,        // Quiet promotion
    PR_QUEEN = 7,       // Quiet promotion
    PC_KNIGHT = 12,     // Capture promotion
    PC_BISHOP = 13,     // Capture promotion
    PC_ROOK = 14,       // Capture promotion
    PC_QUEEN = 15       // Capture promotion
}
```

### Move Make/Unmake

**Move Execution** (libsurge.h:451-535):
```cpp
template<Color C> void Position::play(const Move m)
// Updates:
// - side_to_play (toggles)
// - game_ply (increments)
// - piece_bb and board arrays
// - zobrist hash (XOR updates)
// - history[game_ply] (captures, en passant square)
```

**Move Undo** (libsurge.h:537-590):
- Uses stored `UndoInfo` to restore captured pieces
- Restores previous side to move and ply
- All information recoverable from history stack

### Python Move Interface (libchessmg.pyx)

**Move Objects** (libchessmg.pyx:72-134):
```python
cdef class Move:
    - from_square: int
    - to_square: int
    - flags: int
    
    @property
    - uci: str              # e.g., "e2e4" or "e7e8q"
    - from_square_str: str  # Algebraic notation
    - to_square_str: str
    - is_capture: bool
    - is_promotion: bool
    - is_castle: bool
    - is_en_passant: bool
    - move_type: MoveFlag
```

---

## 3. Stipulation Handling (Current Status)

### Game State Detection

**Position State Enum** (libcmg.h:9-17):
```cpp
enum CMG_POSITION_STATE : uint8_t {
    CMG_CHECKMATE = 0,        // Checkmate
    CMG_STALEMATE = 2,        // Stalemate  
    CMG_CHECK = 4,            // Check (in check)
    CMG_OPEN_STATE = 32,      // Normal position
    CMG_ILLEGAL_POSITION = 128 // Illegal (pawns on rank 1/8, kings adjacent, opponent in check)
}
```

**State Calculation** (libcmg.cpp:232-249):
```cpp
template<Color Us> void CMGPosition::_states()
{
    // Check legality
    if (_illegal_pawn() || _king_contact() || them_in_check)
        _state = CMG_ILLEGAL_POSITION
    
    // Check for checkmate/stalemate
    if (no_legal_moves)
        _state = us_in_check ? CMG_CHECKMATE : CMG_STALEMATE
    else
        _state = us_in_check ? CMG_CHECK : CMG_OPEN_STATE
}
```

### Available Game State Detection

1. Check detection
2. Checkmate detection (no legal moves + in check)
3. Stalemate detection (no legal moves + not in check)
4. Illegal position detection
5. Basic game termination conditions

### Python API for Game States (position.py)

```python
class GameState(IntEnum):
    CHECKMATE = 0
    STALEMATE = 2
    CHECK = 4
    NORMAL = 32
    ILLEGAL = 128

class ChessPosition:
    @property
    def is_check(self) -> bool
    
    @property
    def is_checkmate(self) -> bool
    
    @property
    def is_stalemate(self) -> bool
    
    @property
    def is_game_over(self) -> bool
```

---

## 4. Current API Structure and Entry Points

### Three-Layer Architecture

```
Python Application
    ↓
Python API Layer (position.py, __init__.py)
    ↓
Cython Binding Layer (libchessmg.pyx)
    ↓
C++ Core Engine (libcmg.cpp, libsurge.cpp/h)
```

### Main Entry Points

#### Python API (position.py)

**Primary Class**:
```python
class ChessPosition:
    def __init__(self, fen: str = DEFAULT_FEN)
    
    # Move Generation
    def legal_moves(self) -> List[Move]
    
    # Position Manipulation
    def make_move(self, move: Union[Move, str]) -> None
    def undo_move(self) -> Optional[Move]
    def copy(self) -> 'ChessPosition'
    
    # Position Analysis
    def perft(self, depth: int) -> int
    
    # Position Properties
    @property fen -> str
    @property turn -> Color
    @property is_check -> bool
    @property is_checkmate -> bool
    @property is_stalemate -> bool
    @property is_game_over -> bool
```

#### Cython Binding Layer (libchessmg.pyx)

**Main Class**:
```python
cdef class ChessMoveGenerator:
    def __init__(self, input=None)  # FEN str or dict
    def legal_moves(self) -> List[Move]
    def moves(self, as_string=False, color=None) -> Union[np.ndarray, List[str], List[Move]]
    def fen(self) -> str
    def set_fen(self, fen: str) -> None
    def turn(self) -> int  # 0=WHITE, 1=BLACK
    def state(self, color: int) -> int
    def perft(self, depth: int) -> int64_t
    def move_piece(self, from_: int, to: int) -> None
    def is_legal(self) -> bool
```

**Input Formats**:
```python
# FEN string
pos = ChessMoveGenerator("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

# Dictionary with raw piece list
pos = ChessMoveGenerator({
    "raw": [(13,2), (5,18), (4,40), (12,53)],  # (piece_id, square)
    "turn": True,      # true=white, false=black
    "epsq": 64,        # en passant square (64=none)
    "castling": ""     # "KQkq" format
})

# Dictionary with named pieces
pos = ChessMoveGenerator({
    "position": [("K", "e1"), ("Q", "d1")],  # Piece names, square names
    "turn": True,
    "epsq": 64,
    "castling": "KQkq"
})
```

---

## 5. File Structure and Organization

```
ChessMG/
├── README.md                      # Project documentation
├── setup.py                       # Build configuration
├── Makefile                       # Top-level build
├── Version.txt                    # Version: 0.3.0
├── requirements.txt               # Dependencies
│
├── chessmg/                       # Main package
│   ├── __init__.py               # API exports
│   ├── position.py               # High-level Python API
│   ├── libchessmg.pyx            # Cython binding layer
│   │
│   └── libcmg/                   # C++ Core Engine
│       ├── libcmg.h              # CMG wrapper (CMGPosition, CMGMove)
│       ├── libcmg.cpp            # CMG implementation
│       ├── libsurge.h            # Core chess logic (Position, Move, Bitboards)
│       ├── libsurge.cpp          # Lookup tables, FEN parsing, move generation
│       ├── Makefile              # Build C++ components
│       │
│       └── tests/                # C++ unit tests
│           ├── test_libsurge.cpp
│           ├── test_libcmg.cpp
│           ├── test_libsurge_multithreading.cpp
│           └── test_iterator.cpp
│
├── examples/                      # Example usage
│   ├── simple.py                 # Basic usage (legacy API)
│   ├── example_new_api.py        # Comprehensive examples (new API)
│   └── iterator.py               # Iterator pattern demo
│
└── tests/                        # Python tests
    ├── test_new_api.py           # ChessPosition API tests
    ├── test_perft.py             # Performance benchmarking
    ├── test_set_position.py      # Position creation tests
    ├── test_correctness.py       # Move correctness validation
    ├── test_average.py
    └── test_perft_start_fen.py
```

---

## 6. Indexing and Position Encoding Systems

### Board Representation

**Multiple Representations Used**:

1. **Bitboard Representation**
   - 64-bit integer with one bit per square
   - Used for fast move generation
   - Operations: bitwise AND, OR, XOR, shifts

2. **Mailbox Representation**
   - `Piece board[64]` array
   - Direct piece type lookup at any square
   - Used for move execution and undo

3. **Piece Bitboards**
   - `Bitboard piece_bb[15]` 
   - One bitboard per piece type
   - Used for finding pieces of specific type

4. **Zobrist Hashing**
   - `zobrist_table[15][64]`
   - Incremental hash updates
   - Used for position comparison

### Square Indexing System

**Linear Mapping** (0-63):
```
Index = rank * 8 + file
Rank = index >> 3
File = index & 0b111
```

**File and Rank Enums**:
```cpp
enum File : int {AFILE, BFILE, CFILE, DFILE, EFILE, FFILE, GFILE, HFILE}
enum Rank : int {RANK1, RANK2, RANK3, RANK4, RANK5, RANK6, RANK7, RANK8}
```

**Pre-computed Masks** (libsurge.cpp):
- `MASK_FILE[8]` - Column masks (0x0101010101010101, etc.)
- `MASK_RANK[8]` - Row masks (0xff, 0xff00, etc.)
- `MASK_DIAGONAL[15]` - Diagonal masks
- `MASK_ANTI_DIAGONAL[15]` - Anti-diagonal masks
- `SQUARE_BB[65]` - Single square masks

### Move Encoding

**Internal Move Representation** (libsurge.h:187-206):
```cpp
class Move {
    uint16_t move;
    // Bit layout:
    // [15:12] = flags (4 bits)
    // [11:6]  = from square (6 bits)
    // [5:0]   = to square (6 bits)
}
```

**Conversion to Array** (libchessmg.pyx):
```python
# C++ returns flat array: [from, to, flags, from, to, flags, ...]
# Python reshapes to: [[from, to, flags], [from, to, flags], ...]
moves_array = np.array(raw_moves).reshape(-1, 3)
```

### Perft Implementation

**Performance Test** (libcmg.cpp:181-197):
```cpp
template<Color Us>
int64_t CMGPosition::_perft(unsigned int depth)
{
    if (depth == 1) return move_count;
    
    for (each legal move):
        position.play<Us>(move);
        nodes += _perft<~Us>(depth - 1);
        position.undo<Us>(move);
    
    return nodes;
}
```

**Known Perft Values** (test_new_api.py):
- perft(0) = 1
- perft(1) = 20
- perft(2) = 400
- perft(3) = 8,902

---

## 7. Key Design Patterns

### Template Metaprogramming (C++)
- Compile-time color inversion: `~Color c`
- Templated move generation by color
- Templated perft with color alternation

### Incremental Updates
- Zobrist hash XOR updates during move/undo
- Efficient pin/checker detection during move generation

### Move History Stack
- `UndoInfo history[256]` stores non-recoverable info
- Enables fast undo without board reconstruction

### Dual Representation
- Bitboards for efficient operations
- Mailbox for direct lookup
- Both kept synchronized

---

## 8. Build System

**Compilation Pipeline**:
```
1. C++ Libraries (Makefile in libcmg/):
   - libsurge.cpp → libsurge.a
   - libcmg.cpp → libcmg.a (depends on libsurge)

2. Cython Binding (setup.py):
   - libchessmg.pyx → libchessmg.so (C extension)
   - Depends on: libcmg.a, libsurge.a

3. Python Package:
   - position.py → ChessPosition class
   - __init__.py → API exports
```

**Build Commands**:
```bash
pip install .              # Full build and install
make -C chessmg/libcmg     # Build C++ only
python setup.py build_ext  # Build Cython only
```

---

## 9. Performance Characteristics

**Move Generation**: 250M+ moves/sec (AMD Ryzen 9 5900X)
- Magic bitboards: O(1) sliding piece attacks
- Pre-computed lookup tables
- Bitwise operations for bitboard manipulation

**Memory Usage**: <1MB per position
- Efficient bitboard representation
- Shared lookup tables (not per-position)

**Perft(7)**: ~12.8 seconds (3.2B positions)

---

## Summary

The ChessMG codebase provides:
✓ Robust position representation (bitboard + mailbox)
✓ High-performance legal move generation
✓ Fast move make/unmake with history
✓ Basic game state detection (check, checkmate, stalemate)
✓ FEN parsing and generation
✓ Clean Python API with type hints
✓ Extensible Cython binding layer
