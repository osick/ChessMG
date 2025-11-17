# ChessMG Tablebase System

Efficient tablebase generation and probing for chess problems, with a focus on helpmate stipulations.

## Features

- **Efficient Indexing**: Combinatorial indexing using binomial coefficients for compact position representation
- **Retrograde Analysis**: Backward search algorithm for complete tablebase generation
- **Compact Storage**: 4 bits per position with memory-mapped file access
- **Fast Lookups**: O(1) position probing with caching
- **Helpmate Support**: Specialized for helpmate problems with distance-to-mate values
- **Extensible**: Easy to add support for other stipulations

## Installation

The tablebase system is part of ChessMG. No additional installation required.

## Quick Start

### 1. Generate a Tablebase

```python
from pathlib import Path
from chessmg.tablebase import MaterialSignature, TablebaseGenerator

# Define material: King + Pawn vs King
material = MaterialSignature.from_pieces(
    white=[5, 0],  # King (5) + Pawn (0)
    black=[5]      # King (5)
)

# Generate tablebase
generator = TablebaseGenerator()
stats = generator.generate_helpmate_tablebase(
    material=material,
    output_dir=Path('./tablebases'),
    max_depth=7
)

print(f"Generated {stats['legal_positions']:,} positions")
```

### 2. Probe Positions

```python
from pathlib import Path
from chessmg.tablebase import TablebaseProbe

# Create probe
probe = TablebaseProbe(Path('./tablebases'))

# Probe a position
fen = "8/8/8/8/8/5k2/4P3/5K2 w - - 0 1"
result = probe.probe_fen(fen)

if result and result.is_helpmate():
    print(f"Helpmate in {result.moves_to_helpmate()} moves")
```

### 3. Command-Line Tools

```bash
# Generate tablebase
python generate_tablebase.py --material KPvK --output ./tablebases

# Probe position
python probe_tablebase.py --fen "8/8/8/8/8/5k2/4P3/5K2 w - - 0 1" --dir ./tablebases

# List available tablebases
python probe_tablebase.py --list --dir ./tablebases
```

## Architecture

### Components

1. **Indexing** (`tablebase/indexing.py`)
   - Converts positions to unique integer indices
   - Uses combinatorial number system for efficiency
   - Supports arbitrary piece configurations

2. **Storage** (`tablebase/storage.py`)
   - Binary file format with 4-bit position encoding
   - Memory-mapped for fast access
   - Thread-safe operations

3. **Retrograde Analysis** (`tablebase/retrograde.py`)
   - Backward search from mate positions
   - Breadth-first search for optimal DTM
   - Efficient position generation

4. **Generator** (`tablebase/generator.py`)
   - High-level API for tablebase creation
   - Progress tracking and statistics
   - Batch generation support

5. **Probe** (`tablebase/probe.py`)
   - Fast O(1) position lookups
   - Automatic tablebase discovery
   - In-memory caching

### Position Encoding

For a given material signature (e.g., KPvK), each position is encoded as a unique index:

```
Total positions = C(64, n_white) × C(64 - n_white, n_black)
```

Where:
- `n_white` = number of white pieces
- `n_black` = number of black pieces
- `C(n, k)` = binomial coefficient

Example: KPvK (3 pieces)
- White king: 64 squares
- White pawn: 63 remaining squares (48 legal ranks)
- Black king: 62 remaining squares
- Total: ~190,000 positions (with constraints)

### Storage Format

Binary file structure:

```
┌──────────────────────────────────────┐
│ Header (128 bytes)                   │
│  - Magic: "CMGTB"                    │
│  - Version: 1                        │
│  - Table size: uint64                │
│  - Material signature: string        │
├──────────────────────────────────────┤
│ Data (4 bits per position)           │
│  - 0: UNKNOWN                        │
│  - 1-7: HELPMATE_IN_N                │
│  - 8: HELPMATE_IN_8_PLUS             │
│  - 9: DRAW                           │
│  - 10: ILLEGAL                       │
└──────────────────────────────────────┘
```

Storage efficiency: 2 positions per byte

## Material Signature Format

Piece types:
- `0` = Pawn (P)
- `1` = Knight (N)
- `2` = Bishop (B)
- `3` = Rook (R)
- `4` = Queen (Q)
- `5` = King (K)

String format: `<white_pieces>v<black_pieces>`

Examples:
- `KvK` - King vs King
- `KPvK` - King + Pawn vs King
- `KQvKR` - King + Queen vs King + Rook
- `KRRvKQ` - King + 2 Rooks vs King + Queen

## Helpmate Tablebase Generation

Algorithm:

1. **Initialize**: Mark all positions as UNKNOWN
2. **Find terminals**: Identify checkmate positions (HELPMATE_IN_1)
3. **Retrograde search**:
   - For each ply N = 2 to max_depth:
     - Find positions reaching ply N-1 in one move
     - Mark as HELPMATE_IN_N
4. **Finalize**: Mark remaining legal positions as DRAW

Complexity:
- Time: O(P × M) where P = positions, M = avg moves per position
- Space: O(P) for position storage

## Performance

### Generation Speed

Approximate times (single-threaded):

| Material | Positions | Time | Size |
|----------|-----------|------|------|
| KvK | 3,612 | <1s | <2KB |
| KPvK | ~190K | <1min | ~100KB |
| KQvK | ~195K | <1min | ~100KB |
| KRvK | ~195K | <1min | ~100KB |

### Lookup Speed

- O(1) index calculation
- O(1) memory-mapped file access
- ~1-10 microseconds per probe (cached)

## API Reference

### MaterialSignature

```python
material = MaterialSignature.from_pieces(
    white=[5, 0],  # King + Pawn
    black=[5]      # King
)

print(material)  # "KPvK"
print(material.total_pieces())  # 3
```

### TablebaseGenerator

```python
generator = TablebaseGenerator()

# Generate single tablebase
stats = generator.generate_helpmate_tablebase(
    material=material,
    output_dir=Path('./tablebases'),
    max_depth=7,
    use_symmetry=False
)

# Estimate size
estimate = generator.estimate_size(material)
print(f"Estimated size: {estimate['total_size_mb']:.2f} MB")
```

### TablebaseProbe

```python
probe = TablebaseProbe(Path('./tablebases'))

# Probe by position object
from chessmg.position import ChessPosition
position = ChessPosition("8/8/8/8/8/5k2/4P3/5K2 w - - 0 1")
result = probe.probe(position)

# Probe by FEN
result = probe.probe_fen("8/8/8/8/8/5k2/4P3/5K2 w - - 0 1")

# Check if helpmate
if result and result.is_helpmate():
    dtm = result.moves_to_helpmate()
    print(f"Helpmate in {dtm} moves")

# List available tablebases
available = probe.available_tablebases()
```

### PositionIndexer

```python
from chessmg.tablebase import PositionIndexer

indexer = PositionIndexer(material)

# Encode position
white_squares = [4, 12]  # e1, e2
black_squares = [60]     # e8
index = indexer.encode(white_squares, black_squares)

# Decode index
white_sq, black_sq = indexer.decode(index)

# Get maximum index
max_idx = indexer.max_index()
```

## Advanced Usage

### Custom Progress Tracking

```python
def progress_callback(phase: str, current: int, total: int):
    print(f"{phase}: {current}/{total}")

stats = generator.generate_helpmate_tablebase(
    material=material,
    output_dir=Path('./tablebases'),
    progress_callback=progress_callback
)
```

### Batch Generation

```python
materials = [
    MaterialSignature.from_pieces([5], [5]),      # KvK
    MaterialSignature.from_pieces([5, 0], [5]),   # KPvK
    MaterialSignature.from_pieces([5, 4], [5]),   # KQvK
]

results = generator.generate_multiple(
    materials=materials,
    output_dir=Path('./tablebases'),
    max_depth=7
)
```

### Validation

```python
result = generator.validate_tablebase(
    Path('./tablebases/KPvK.cmgtb')
)

if result['valid']:
    print(f"Valid tablebase: {result['material']}")
else:
    print(f"Error: {result['error']}")
```

## Limitations & Future Work

### Current Limitations

1. **No pawn promotion handling**: Pawns can be on any square (including rank 1/8)
2. **No symmetry reduction**: Storage could be 8x smaller with symmetry
3. **No castling rights**: Not relevant for most endgame tablebases
4. **No en passant**: Not tracked in position encoding
5. **Single-threaded**: Generation is not parallelized

### Planned Features

- [ ] Pawn rank constraints (no pawns on rank 1/8)
- [ ] Symmetry reduction (horizontal/vertical/diagonal)
- [ ] Parallel generation using multiprocessing
- [ ] Compression for sparse tablebases
- [ ] Support for other stipulations (selfmate, series movers)
- [ ] Integration with chess problem databases
- [ ] Web API for tablebase access

## Contributing

To add support for new stipulations:

1. Extend `PositionValue` enum in `storage.py`
2. Implement new analyzer in `retrograde.py`
3. Add generation method in `generator.py`
4. Update CLI tools

## References

- [Retrograde Analysis](https://www.chessprogramming.org/Retrograde_Analysis)
- [Endgame Tablebases](https://en.wikipedia.org/wiki/Endgame_tablebase)
- [Combinatorial Number System](https://en.wikipedia.org/wiki/Combinatorial_number_system)

## License

Part of ChessMG. See main LICENSE file.
