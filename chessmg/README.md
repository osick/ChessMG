# chessmg - High-Performance Chess Move Generation

Core Python module providing ultra-fast chess move generation via C++20 engine.

## Installation

From the repository root:

```bash
pip install .
```

Or build the extension in place:
```bash
python setup.py build_ext --inplace
```

## Quick Start

```python
from chessmg import ChessPosition

# Create position from FEN
pos = ChessPosition("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

# Generate legal moves
moves = pos.legal_moves()
print(f"Found {len(moves)} legal moves")

# Iterate through moves
for move in moves:
    print(f"{move.from_square_name} -> {move.to_square_name}: {move.uci}")

# Check game state
print(f"Turn: {['White', 'Black'][pos.turn()]}")
print(f"State: {pos.state(pos.turn())}")
```

## API Reference

### ChessPosition

Main class for position manipulation.

**Initialization:**
```python
# From FEN (default: starting position)
pos = ChessPosition()
pos = ChessPosition("8/8/8/8/8/8/8/8 w - - 0 1")

# From piece dictionary
pos = ChessPosition({
    'pieces': [(5, 4), (0, 12), (5, 60)],  # (piece, square) tuples
    'turn': True,  # True=White, False=Black
    'epsq': 64,  # En passant square (64=none)
    'castling': ''  # Castling rights
})
```

**Methods:**
- `legal_moves()` - Returns list of Move objects
- `fen()` - Get FEN string
- `turn()` - Get active color (0=White, 1=Black)
- `state(color)` - Get game state for color
- `is_legal()` - Check if position is legal
- `play(from_sq, to_sq, flags)` - Play a generated legal move (handles captures, castling, en passant, promotion, side to move)
- `move_piece(from_sq, to_sq)` - Low-level board edit: teleport a piece (no move semantics)
- `perft(depth)` - Performance test (count leaf nodes)

### Move

Represents a chess move with rich metadata.

**Properties:**
- `from_square` - Source square (0-63)
- `to_square` - Destination square (0-63)
- `flags` - Move type flags
- `from_square_str` - Source in algebraic notation
- `to_square_str` - Destination in algebraic notation
- `uci` - UCI notation (e.g., "e2e4")
- `move_type` - MoveFlag enum
- `is_capture` - Boolean
- `is_promotion` - Boolean
- `is_castle` - Boolean
- `is_en_passant` - Boolean

## Performance

ChessMG achieves 200M+ moves/second through:

- **Magic bitboards** for sliding piece attacks
- **Perfect hashing** with O(1) lookups
- **Zero-copy Cython bindings**
- **Cache-optimized data structures**

Typical benchmark results (see `tests/benchmark_perft.py`):
```
Move generation: 200,000,000+ moves/sec
Perft(6): ~0.5 seconds
Memory usage: < 1 MB per position
```

## Examples

### Perft Testing
```python
pos = ChessPosition()
nodes = pos.perft(6)  # Count all positions at depth 6
print(f"Nodes: {nodes:,}")  # 119,060,324
```

### Move Filtering
```python
pos = ChessPosition()
moves = pos.legal_moves()

# Filter by type
captures = [m for m in moves if m.is_capture]
promotions = [m for m in moves if m.is_promotion]
castles = [m for m in moves if m.is_castle]
```

### Game Validation
```python
def validate_moves(fen, uci_moves):
    pos = ChessPosition(fen)
    for uci in uci_moves:
        legal_ucis = [m.uci for m in pos.legal_moves()]
        if uci not in legal_ucis:
            return False
        # Make move (simplified - need actual implementation)
    return True
```

## See Also

- [Main README](../README.md) - Project overview
- [API Documentation](../docs/) - Detailed technical docs
