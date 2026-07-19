# ♞ ChessMG

<div align="center">

[![CI](https://github.com/osick/ChessMG/actions/workflows/ci.yml/badge.svg)](https://github.com/osick/ChessMG/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/Version-0.5.0-blue.svg)](https://github.com/osick/ChessMG/releases)
[![Performance](https://img.shields.io/badge/Performance-200M%2B%20moves%2Fsec-brightgreen.svg)](#-performance)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![C++](https://img.shields.io/badge/C%2B%2B-20-00599C.svg)](https://en.cppreference.com/w/cpp/20)
[![Perft](https://img.shields.io/badge/Perft-verified-success.svg)](#-performance)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENCE)

**Blazing-fast chess move generation for Python, powered by a C++20 bitboard engine.**

*One `pip install`. 200 million moves per second. A Python API that stays out of your way.*

</div>

---

## Why ChessMG?

|  |  |
|---|---|
| **Fast** | Magic bitboards + zero-copy Cython bindings — roughly **50× faster** than pure-Python move generators |
| **Pythonic** | A clean `ChessPosition` / `Move` API with type annotations, UCI notation and rich move metadata |
| **Complete** | Castling, en passant, promotions, check / checkmate / stalemate detection, legality checks |
| **Verified** | Move generation validated against the standard [perft reference values](https://www.chessprogramming.org/Perft_Results) up to depth 8 |
| **Lean** | No runtime dependencies beyond NumPy — and less than 1 MB per position |

Typical uses: engine prototyping, puzzle solvers, dataset generation for ML, move validation backends, perft research — anywhere Python convenience meets the need for raw speed.

---

## 🚀 Quick Start

### Install

```bash
pip install chessmg
```

Prebuilt wheels cover Linux (x86_64, aarch64) and macOS (Intel, Apple Silicon) for Python 3.9–3.13. On other platforms pip falls back to building from source.

Or install the latest development version from source:

```bash
git clone https://github.com/osick/ChessMG.git
cd ChessMG
pip install .
```

> Building from source requires a C++20 compiler (g++/clang), `Cython` and `numpy`.

### Play

```python
from chessmg import ChessPosition

pos = ChessPosition()                # standard starting position (or pass any FEN)

for move in pos.legal_moves():       # 20 legal moves, as rich Move objects
    print(move.uci)                  # "e2e4", "g1f3", ...

pos.make_move("e2e4")                # UCI strings or Move objects
pos.make_move("e7e5")
print(pos.fen)                       # rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2

pos.undo_move()                      # take it back

print(pos.turn)                      # Color.BLACK
print(pos.is_checkmate)              # False

print(ChessPosition().perft(6))      # 119060324 — in about half a second
```

Promotions, castling and en passant just work:

```python
pos = ChessPosition("8/4P1k1/8/8/8/8/8/4K3 w - - 0 1")
pos.make_move("e7e8q")               # promote to queen
print(pos.fen)                       # 4Q3/6k1/8/8/8/8/8/4K3 b - - 0 1
```

---

## 📖 API at a Glance

### `ChessPosition`

| Member | Description |
|--------|-------------|
| `ChessPosition(fen)` | Create position from FEN — raises `ValueError` on invalid or illegal input |
| `legal_moves()` | List of legal `Move` objects |
| `make_move(move)` | Play a move (UCI string or `Move`); full move semantics |
| `undo_move()` | Undo the last move |
| `fen` | Current position as a complete 6-field FEN string |
| `turn` | Side to move (`Color.WHITE` / `Color.BLACK`) |
| `is_check` / `is_checkmate` / `is_stalemate` / `is_game_over` | Game state |
| `perft(depth)` | Count leaf nodes at the given depth |
| `copy()` | Independent copy of the position |

### `Move`

| Property | Description |
|----------|-------------|
| `from_square` / `to_square` | Square indices (0–63) |
| `from_square_name` / `to_square_name` | Algebraic notation (`"e2"`) |
| `uci` | UCI notation (`"e2e4"`, `"e7e8q"`) |
| `promotion` | `PieceType` for promotions, else `None` |
| `Move.from_uci("e2e4")` | Construct from a UCI string |

<details>
<summary><b>Legacy low-level API</b> (click to expand)</summary>

For backward compatibility, the lower-level API remains available:

```python
from chessmg import ChessMoveGenerator, perft, moves

gen = ChessMoveGenerator("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
arr = gen.moves()          # numpy array of shape (n_moves, 3): [from, to, flags]
n   = perft(fen, depth)    # one-shot perft; returns 0 for illegal positions
```

See [chessmg/README.md](chessmg/README.md) for details.

</details>

---

## 🏁 Performance

Perft from the starting position, single-threaded (AMD Ryzen, g++ -O2):

| Depth | Nodes | Time | Speed |
|------:|------:|-----:|------:|
| 5 | 4,865,609 | < 0.1 s | ~166M NPS |
| 6 | 119,060,324 | 0.5 s | ~218M NPS |
| 7 | 3,195,901,860 | 12.9 s | ~247M NPS |
| 8 | 84,998,978,956 | 6.7 min | ~213M NPS |

All results match the published [perft reference values](https://www.chessprogramming.org/Perft_Results) exactly.

**How it's fast:** magic bitboards for sliding pieces, pre-computed attack tables, perfect-hash lookups, cache-friendly data layout in the C++20 core — and Cython bindings that avoid copying on the way into Python.

Reproduce it yourself:

```bash
python tests/benchmark_perft.py
python tests/test_perft_start_fen.py 7 verbose
```

---

## 🗂️ Project Structure

```
ChessMG/
├── chessmg/              # Python package
│   ├── position.py       #   High-level API (ChessPosition, Move)
│   ├── libchessmg.pyx    #   Cython bindings
│   └── libcmg/           #   C++20 engine
│       ├── libcmg.*      #     Position wrapper, game states, perft
│       ├── libsurge.*    #     Bitboard core (based on surge)
│       └── tests/        #     C++ unit tests
├── tests/                # Python test suite + benchmarks
├── examples/             # Example scripts
└── docs/                 # Technical documentation
```

---

## 🛠️ Development

```bash
# Editable install with dev tools (pytest, black, mypy, pytest-cov)
pip install -e ".[dev]"

# Rebuild the extension in place after C++/Cython changes
python setup.py build_ext --inplace

# Run the test suite
pytest tests/

# Script-style correctness / perft tests (also run by `make test`)
python tests/test_correctness.py verbose
python tests/test_perft_start_fen.py 6 verbose
python tests/test_set_position.py verbose
```

Further reading:

- [chessmg/README.md](chessmg/README.md) — module-level API documentation
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — engine internals: bitboards, move encoding, binding layers

---

## 📄 License

MIT License — see [LICENCE](LICENCE) for details.

### Acknowledgments

- [surge](https://github.com/nkarve/surge) — the C++ bitboard engine ChessMG's core is based on

---

<div align="center">

**ChessMG** — *chess move generation at engine speed, with Python comfort.*

[Report an issue](https://github.com/osick/ChessMG/issues) · [Documentation](docs/)

</div>
