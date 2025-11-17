# tablebase - True Helpmate Tablebase System

Python package for generating and probing true helpmate endgame tablebases using cooperative retrograde analysis.

## What is a Helpmate Tablebase?

Unlike traditional forced mate tablebases (adversarial), helpmate tablebases assume **cooperative play** where both sides work together to reach checkmate.

| Aspect | Forced Mate | True Helpmate |
|--------|-------------|---------------|
| **Goal** | Force mate against best defense | Cooperate to reach mate |
| **Players** | Adversarial | Cooperative |
| **Algorithm** | min/max search | any-move search |
| **Solutions** | ONE optimal path | MULTIPLE cooperative paths |
| **Use Cases** | Chess engines, endgame theory | Helpmate puzzles, compositions |

## Quick Start

### Generate a Tablebase

```python
from tablebase import MaterialSignature, PositionIndexer, TablebaseStorage
from tablebase.retrograde_helpmate import HelpmateRetrogradeAnalyzer

# Setup for KPvK (King+Pawn vs King)
material = MaterialSignature.from_pieces([5, 0], [5])
indexer = PositionIndexer(material)

# Create storage file
storage = TablebaseStorage(
    "KPvK.cmgtb",
    material,
    indexer.max_index(),
    mode='w'
)

# Generate tablebase
analyzer = HelpmateRetrogradeAnalyzer(material, indexer)
stats = analyzer.generate_tablebase(
    storage,
    max_depth=10,
    target_color=1  # Mate Black king
)

print(f"Generated {stats['helpmate_positions']:,} helpmate positions")
print(f"Max DTM: {stats['max_dtm']}")

storage.close()
```

### Probe a Position

```python
from tablebase import TablebaseProbe
from chessmg import ChessPosition

# Initialize probe
probe = TablebaseProbe("./tablebases")

# Probe position
pos = ChessPosition("8/8/8/8/8/5k2/4P3/5K2 w - - 0 1")
value = probe.probe(pos)

if value and value.is_helpmate():
    print(f"Helpmate in {value.moves_to_helpmate()} moves")
else:
    print("Not a helpmate position")
```

## CLI Usage

The `cmgtb` command-line tool provides a complete interface:

```bash
# Generate tablebase
cmgtb generate KPvK --output ./tb --depth 10

# Probe position
cmgtb probe "8/8/8/8/8/5k2/4P3/5K2 w - - 0 1" --dir ./tb

# Search for specific positions
cmgtb search --material KPvK --dtm 5 --dir ./tb --limit 10

# Show statistics
cmgtb stats KPvK --dir ./tb

# List available tablebases
cmgtb list --dir ./tb
```

## API Reference

### MaterialSignature

Represents a material configuration (piece set).

```python
# Create from piece lists
material = MaterialSignature.from_pieces(
    white=[5, 0],  # King, Pawn
    black=[5]      # King
)

print(material)  # "KPvK"
print(material.total_pieces())  # 3
```

### PositionIndexer

Maps positions to unique indices using combinatorial encoding.

```python
indexer = PositionIndexer(material)

# Encode position to index
index = indexer.encode(
    white_squares=[4, 12],    # e1, e2
    black_squares=[60],        # e8
    side_to_move=0,           # White to move
    ep_file=0                 # No en passant
)

# Decode index to position
white_sq, black_sq, stm, ep = indexer.decode(index)

print(f"Total positions: {indexer.max_index():,}")
```

### TablebaseStorage

Manages binary tablebase files with memory-mapped I/O.

```python
# Create new tablebase
storage = TablebaseStorage(
    "KPvK.cmgtb",
    material,
    table_size,
    mode='w'
)

# Set position value
storage.set_value(index, PositionValue.HELPMATE_IN_3)

# Read position value
value = storage.get_value(index)

storage.close()

# Open existing tablebase (auto-detects material!)
storage = TablebaseStorage.open("KPvK.cmgtb", mode='r')
print(storage.material)      # Loaded from file header
print(storage.table_size)    # Loaded from file header
```

### HelpmateRetrogradeAnalyzer

Generates helpmate tablebases using cooperative retrograde analysis.

```python
analyzer = HelpmateRetrogradeAnalyzer(material, indexer)

stats = analyzer.generate_tablebase(
    storage,
    max_depth=10,
    target_color=1,  # 0=mate White, 1=mate Black
    progress_callback=lambda ply, count: print(f"Ply {ply}: {count:,}")
)

# Statistics returned:
print(stats['total_positions'])
print(stats['helpmate_positions'])
print(stats['max_dtm'])
print(stats['positions_by_dtm'])  # Distribution
```

### TablebaseProbe

Fast O(1) position probing with caching.

```python
probe = TablebaseProbe("./tablebases")

# Probe ChessPosition
from chessmg import ChessPosition
pos = ChessPosition(fen)
value = probe.probe(pos)

# Probe FEN string
value = probe.probe_fen("8/8/8/8/8/5k2/4P3/5K2 w - - 0 1")

# Check for helpmate
dtm = probe.is_helpmate(pos)
if dtm:
    print(f"Helpmate in {dtm} moves")
```

## File Format

Tablebase files (`.cmgtb`) use a compact binary format:

**Header (128 bytes):**
```
Bytes 0-4:    Magic "CMGTB"
Byte 5:       Version (2)
Bytes 6-13:   Table size (uint64)
Byte 14:      Number of white pieces
Bytes 15-30:  White piece types
Byte 31:      Number of black pieces
Bytes 32-47:  Black piece types
Bytes 48-127: Reserved
```

**Data Section:**
- 4 bits per position (2 positions per byte)
- Memory-mapped for fast access
- Values: UNKNOWN, HELPMATE_IN_N, DRAW, ILLEGAL

**Size Examples:**
- KvK: 32 KB
- KPvK: 2.0 MB
- KQvK: 1.7 MB

## Position Values

```python
class PositionValue(IntEnum):
    UNKNOWN = 0               # Not yet computed
    HELPMATE_IN_1 = 1         # Checkmate position
    HELPMATE_IN_2 = 2         # 2 ply to mate
    HELPMATE_IN_3 = 3         # 3 ply to mate
    # ...
    HELPMATE_IN_7 = 7
    HELPMATE_IN_8_PLUS = 8    # 8 or more ply
    DRAW = 9                  # No helpmate possible
    ILLEGAL = 10              # Illegal position
```

## Performance

Tablebase generation performance on AMD Ryzen 9 5900X @ 3.7GHz:

| Material | Positions | Time | Throughput |
|----------|-----------|------|------------|
| KvK | 62K | < 1s | 62K pos/s |
| KPvK | 507K | 38 min | 222 pos/s |
| KQvK | 444K | 24 min | 308 pos/s |

**Optimizations:**
- Direct Position API (100x faster than FEN)
- Memory-mapped I/O for storage
- Efficient combinatorial indexing
- Side-to-move encoding (2x size, essential for correctness)

## Examples

### Material Signatures

```python
# Piece type codes: P=0, N=1, B=2, R=3, Q=4, K=5

KvK = MaterialSignature.from_pieces([5], [5])
KPvK = MaterialSignature.from_pieces([5, 0], [5])
KQvK = MaterialSignature.from_pieces([5, 4], [5])
KRvK = MaterialSignature.from_pieces([5, 3], [5])
KBBvK = MaterialSignature.from_pieces([5, 2, 2], [5])
```

### Batch Generation

```python
materials = [
    ('KvK', [5], [5]),
    ('KPvK', [5, 0], [5]),
    ('KQvK', [5, 4], [5]),
]

for name, white, black in materials:
    material = MaterialSignature.from_pieces(white, black)
    indexer = PositionIndexer(material)

    storage = TablebaseStorage(f"{name}.cmgtb", material, indexer.max_index(), 'w')
    analyzer = HelpmateRetrogradeAnalyzer(material, indexer)

    stats = analyzer.generate_tablebase(storage, max_depth=10)
    print(f"{name}: {stats['helpmate_positions']:,} helpmates")

    storage.close()
```

## See Also

- [Main README](../README.md) - Project overview
- [chessmg README](../chessmg/README.md) - Core move generation
- [docs/TABLEBASE_GUIDE.md](../docs/TABLEBASE_GUIDE.md) - Detailed documentation
- [docs/HELPMATE_CLARIFICATION.md](../docs/HELPMATE_CLARIFICATION.md) - Forced vs helpmate
