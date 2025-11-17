# Special Cases Handling in ChessMG Tablebases

## Overview

Chess positions have several special rules that must be properly handled in tablebase generation:

1. **Side to move** - Who moves next affects the position value
2. **Capturing** - Captures change material (→ different tablebase)
3. **Promotion** - Pawn promotion changes material (→ different tablebase)
4. **En passant** - Temporary capturing opportunity
5. **Castling** - Special king+rook move with legality constraints

## ChessMG Position Representation

Based on analysis of `chessmg/libcmg/libsurge.h`, ChessMG stores:

```cpp
class Position {
    Bitboard piece_bb[NPIECES];  // Piece locations
    Piece board[NSQUARES];        // Mailbox representation
    Color side_to_play;           // WHITE or BLACK
    int game_ply;                 // Move counter
    uint64_t hash;                // Zobrist hash
    UndoInfo history[256];        // Move history
};

struct UndoInfo {
    Bitboard entry;      // For castling legality (tracks moved pieces)
    Piece captured;      // Captured piece (if any)
    Square epsq;         // En passant square (NO_SQUARE if none)
};
```

**FEN Support**: Full support for all FEN components:
```
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e3 0 1
                                             │  │   │  └─ Move counters
                                             │  │   └─ En passant square
                                             │  └─ Castling rights
                                             └─ Side to move
```

## How Special Cases Are Handled

### 1. Side to Move ⚠️ CRITICAL

**Problem**: The same piece configuration with different side-to-move represents **different positions** with potentially different values.

Example:
```
Position: Ke1, Pe2 vs Ke8
White to move: May be DRAW (stalemate possible)
Black to move: May be HELPMATE_IN_2
```

**Solution**: Double the index space

```python
# Original (WRONG):
index = encode_piece_positions(white_squares, black_squares)

# Correct:
base_index = encode_piece_positions(white_squares, black_squares)
index = base_index * 2 + side_to_move  # 0=white, 1=black
```

**Impact**:
- Doubles tablebase size
- **Essential for correctness**
- Implemented in `indexing_v2.py`

**Example**:
```python
indexer = PositionIndexer(KPvK, encode_en_passant=False)

# Same pieces, different side to move → different indices
idx1 = indexer.encode([4, 12], [60], side_to_move=0)  # White to move
idx2 = indexer.encode([4, 12], [60], side_to_move=1)  # Black to move
assert idx1 != idx2  # Different indices!
```

### 2. Capturing → Tablebase Transitions

**Problem**: Captures change material configuration, moving to a different tablebase.

Example:
```
KPvK (tablebase A) --[pawn captures]--> KvK (tablebase B)
```

**Solution**: Link tablebases during retrograde analysis

```python
def find_predecessors_with_captures(frontier, current_material):
    """Find positions that can capture into the frontier."""

    # Get possible parent materials (one extra piece)
    parent_materials = get_capture_parents(current_material)

    for parent_material in parent_materials:
        parent_tablebase = load_tablebase(parent_material)

        # For each position in parent tablebase
        for pos_index in range(parent_tablebase.size()):
            pos = decode_position(pos_index, parent_material)

            # Check if any capture leads to frontier
            for move in pos.legal_moves():
                if move.is_capture():
                    result_pos = pos.copy().make_move(move)
                    result_index = encode_position(result_pos, current_material)

                    if result_index in frontier:
                        # Mark parent position accordingly
                        mark_position(parent_tablebase, pos_index, ...)
```

**Impact**:
- Enables connected tablebase generation
- Required for complete endgame databases
- **Not yet implemented** - needs multi-tablebase retrograde analysis

**Example Transitions**:
```
KQPvK → KQvK  (pawn captured)
KQPvK → KPvK  (queen captured)
KQPvK → KQvK  (pawn promotes to queen)
```

### 3. Promotion → Tablebase Transitions

**Problem**: Pawn promotion changes material, similar to captures.

Example:
```
KPvK --[pawn promotes to Q]--> KQvK
```

**Solution**: Same as captures - link tablebases

```python
# During retrograde analysis
if move.is_promotion():
    promoted_material = calculate_new_material(current_material, move)
    promoted_tablebase = load_tablebase(promoted_material)
    # Link positions...
```

**Promotion Types**:
- Promote to Queen (most common)
- Promote to Rook
- Promote to Bishop
- Promote to Knight (underpromotion)

Each promotion type leads to a different material configuration.

**Impact**:
- Essential for pawn endgames
- Creates complex tablebase dependencies
- **Not yet implemented**

### 4. En Passant 📝 Optional

**Problem**: Positions differing only by en passant rights are technically different.

Example:
```
Position A: Ke1, Pa5 vs Ke8, Pb5 (just moved b7-b5, e.p. possible)
Position B: Same pieces, but no e.p. rights
```

**Solution**: Add 9 possibilities to index (none, or files a-h)

```python
# Without en passant encoding:
index = base_index * 2 + side_to_move

# With en passant encoding:
index = (base_index * 2 + side_to_move) * 9 + ep_file
# where ep_file = 0 (none) or 1-8 (files a-h)
```

**Impact**:
- Multiplies tablebase size by 9x
- Only relevant for positions with pawns
- **Rare in endgames** (most e.p. opportunities expire quickly)
- Implemented in `indexing_v2.py` as optional

**Recommendation**: Only enable for pawn-heavy endgames where accuracy is critical.

### 5. Castling 📝 Rare in Endgames

**Problem**: Castling rights affect position legality.

Example:
```
Ke1, Rh1 vs Ke8 - Can white castle? Depends on move history.
```

**Solution**: Add castling rights to index (4 bits: KQkq)

```python
# Full encoding with castling:
index = (((base_index * 2 + stm) * 9 + ep) * 16 + castling)
# where castling = bitfield (8=wK, 4=wQ, 2=bK, 1=bQ)
```

**Impact**:
- Multiplies tablebase size by 16x
- **Very rare** in endgames (pieces usually moved)
- **Not implemented** (not worth the cost)

**Recommendation**: Ignore castling for endgame tablebases. If a position allows castling, it's typically not an endgame.

## Implementation Status

### ✅ Implemented

1. **Side to move** - `indexing_v2.py`
   ```python
   indexer = PositionIndexer(material)
   idx = indexer.encode(white_sq, black_sq, side_to_move=0)
   ```

2. **En passant** (optional) - `indexing_v2.py`
   ```python
   indexer = PositionIndexer(material, encode_en_passant=True)
   idx = indexer.encode(white_sq, black_sq, stm=0, ep_file=3)  # e-file
   ```

### ❌ Not Yet Implemented

1. **Captures** - Requires multi-tablebase retrograde analysis
2. **Promotion** - Requires multi-tablebase retrograde analysis
3. **Castling** - Not worth the 16x size increase

## Comparison: V1 vs V2

### Original Implementation (`indexing.py`)

```python
# PROBLEM: Only encodes piece positions
indexer = PositionIndexer(KPvK)
index = indexer.encode([4, 12], [60])  # No side-to-move!

# Same index for both colors to move
idx_white = indexer.encode([4, 12], [60])  # White moves
idx_black = indexer.encode([4, 12], [60])  # Black moves
# idx_white == idx_black  ← WRONG!
```

**Issues**:
- ❌ Side to move not encoded → incorrect values
- ❌ En passant not encoded → minor errors
- ❌ No tablebase transitions → isolated tables only

### Enhanced Implementation (`indexing_v2.py`)

```python
# CORRECT: Encodes positions + side-to-move
indexer = PositionIndexer(KPvK)
idx_white = indexer.encode([4, 12], [60], side_to_move=0)
idx_black = indexer.encode([4, 12], [60], side_to_move=1)
# idx_white != idx_black  ← CORRECT!

# Optional en passant
indexer_ep = PositionIndexer(KPvK, encode_en_passant=True)
idx = indexer_ep.encode([4, 12], [60], stm=0, ep_file=0)
```

**Improvements**:
- ✅ Side to move properly encoded
- ✅ Optional en passant encoding
- ✅ Ready for tablebase transitions (future work)

## Size Impact

| Configuration | KvK | KPvK | KQvK |
|--------------|-----|------|------|
| Base (piece positions only) | 4K | 190K | 195K |
| + Side-to-move | 8K | 380K | 390K |
| + En passant | 72K | 3.4M | 3.5M |
| + Castling | 1.2M | 55M | 56M |

**Recommendation**: Use side-to-move always, en passant rarely, castling never.

## Testing Special Cases

### Test: Side to Move

```python
def test_side_to_move():
    indexer = PositionIndexer(MaterialSignature.from_pieces([5], [5]))

    # Same pieces, different side to move
    idx_white = indexer.encode([0], [63], side_to_move=0)
    idx_black = indexer.encode([0], [63], side_to_move=1)

    assert idx_white != idx_black

    # Decode and verify
    w, b, stm, _ = indexer.decode(idx_white)
    assert stm == 0

    w, b, stm, _ = indexer.decode(idx_black)
    assert stm == 1
```

### Test: En Passant

```python
def test_en_passant():
    material = MaterialSignature.from_pieces([5, 0], [5])
    indexer = PositionIndexer(material, encode_en_passant=True)

    # Same position, different e.p. rights
    idx_no_ep = indexer.encode([4, 12], [60], stm=0, ep_file=0)
    idx_with_ep = indexer.encode([4, 12], [60], stm=0, ep_file=5)  # e-file

    assert idx_no_ep != idx_with_ep
```

## Migration Guide

### Step 1: Update Indexer

Replace `indexing.py` imports with `indexing_v2.py`:

```python
# Old
from chessmg.tablebase.indexing import PositionIndexer

# New
from chessmg.tablebase.indexing_v2 import PositionIndexer
```

### Step 2: Update Encoding Calls

Add side-to-move parameter:

```python
# Old
index = indexer.encode(white_squares, black_squares)

# New
index = indexer.encode(white_squares, black_squares, side_to_move=0)
```

### Step 3: Update Decoding Calls

Handle additional return values:

```python
# Old
white_sq, black_sq = indexer.decode(index)

# New
white_sq, black_sq, side_to_move, ep_file = indexer.decode(index)
```

### Step 4: Update Retrograde Analysis

Extract side-to-move from FEN:

```python
fen = position.fen
parts = fen.split()
side_to_move = 0 if parts[1] == 'w' else 1
ep_square = parts[2]  # e.g., "e3" or "-"
ep_file = ord(ep_square[0]) - ord('a') + 1 if ep_square != '-' else 0
```

## Future Work

### High Priority

1. **Tablebase Transitions**
   - Implement multi-tablebase retrograde analysis
   - Handle captures and promotions
   - Build dependency graph of tablebases

2. **FEN-based Encoding**
   - Extract all position info from FEN string
   - Integrate with ChessMG's FEN parser
   - Simplify API

### Medium Priority

3. **Pawn Rank Constraints**
   - Exclude pawns on rank 1/8 (illegal)
   - Reduces index space

4. **Verification**
   - Cross-check with Syzygy/Nalimov tablebases
   - Validate special case handling

### Low Priority

5. **Castling Support**
   - Only if specifically needed
   - Consider separate "with-castling" variant

## References

- [Endgame Tablebases - Wikipedia](https://en.wikipedia.org/wiki/Endgame_tablebase)
- [Syzygy Bases](https://syzygy-tables.info/) - Modern 7-piece tablebases
- [ChessMG Source](https://github.com/osick/ChessMG) - Position representation

## Conclusion

**Critical**: Side-to-move encoding is essential for correctness.

**Recommended**: Enable side-to-move always, en passant for pawn endgames.

**Future**: Implement tablebase transitions for captures and promotions to build complete endgame databases.
