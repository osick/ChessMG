"""
Tablebase Probing Interface

Provides fast O(1) lookups for position evaluations in generated tablebases.

Features:
- In-memory caching of frequently accessed tablebases
- Automatic tablebase file discovery
- Support for multiple material configurations
- Thread-safe access
"""

from typing import Optional, Dict
from pathlib import Path
import threading

from ..position import ChessPosition
from .indexing import PositionIndexer, MaterialSignature
from .storage import TablebaseStorage, PositionValue


class TablebaseProbe:
    """
    Provides fast lookups into tablebase files.

    Manages a collection of tablebases and provides a simple
    interface for probing positions.
    """

    def __init__(self, tablebase_dir: Path):
        """
        Initialize tablebase probe.

        Args:
            tablebase_dir: Directory containing tablebase files
        """
        self.tablebase_dir = Path(tablebase_dir)
        self._cache: Dict[str, TablebaseStorage] = {}
        self._indexers: Dict[str, PositionIndexer] = {}
        self._lock = threading.Lock()

        # Discover available tablebases
        self._discover_tablebases()

    def _discover_tablebases(self):
        """Scan directory for available tablebase files."""
        if not self.tablebase_dir.exists():
            return

        # Look for .cmgtb files
        for filepath in self.tablebase_dir.glob('*.cmgtb'):
            # Material signature is encoded in filename
            # Format: KPvK.cmgtb, KQvKR.cmgtb, etc.
            material_str = filepath.stem
            # We'll load these on-demand

    def probe(self, position: ChessPosition) -> Optional[PositionValue]:
        """
        Probe a position in the tablebase.

        Args:
            position: ChessPosition to evaluate

        Returns:
            PositionValue if found in tablebase, None otherwise
        """
        # Extract material signature from position
        material = self._extract_material(position)
        if not material:
            return None

        # Get or load tablebase
        storage = self._get_tablebase(material)
        if not storage:
            return None

        # Get indexer
        indexer = self._get_indexer(material)
        if not indexer:
            return None

        # Convert position to index
        index = self._position_to_index(position, indexer)
        if index is None:
            return None

        # Lookup value
        try:
            return storage.get_value(index)
        except Exception:
            return None

    def probe_fen(self, fen: str) -> Optional[PositionValue]:
        """
        Probe a position given as FEN string.

        Args:
            fen: FEN string

        Returns:
            PositionValue if found, None otherwise
        """
        try:
            position = ChessPosition(fen)
            return self.probe(position)
        except Exception:
            return None

    def is_helpmate(self, position: ChessPosition) -> Optional[int]:
        """
        Check if position is a helpmate and return DTM (distance to mate).

        Args:
            position: ChessPosition to check

        Returns:
            Number of moves to helpmate, or None if not a helpmate
        """
        value = self.probe(position)
        if value and value.is_helpmate():
            return value.moves_to_helpmate()
        return None

    def _get_tablebase(self, material: MaterialSignature) -> Optional[TablebaseStorage]:
        """Get or load tablebase for a material configuration."""
        material_str = str(material)

        with self._lock:
            # Check cache
            if material_str in self._cache:
                return self._cache[material_str]

            # Try to load from disk
            filepath = self.tablebase_dir / f"{material_str}.cmgtb"
            if not filepath.exists():
                return None

            try:
                # Get table size from indexer
                indexer = self._get_indexer(material)
                if not indexer:
                    return None

                # Open storage
                storage = TablebaseStorage(
                    filepath,
                    material,
                    indexer.max_index(),
                    mode='r'
                )

                # Cache
                self._cache[material_str] = storage
                return storage

            except Exception as e:
                print(f"Error loading tablebase {filepath}: {e}")
                return None

    def _get_indexer(self, material: MaterialSignature) -> Optional[PositionIndexer]:
        """Get or create indexer for a material configuration."""
        material_str = str(material)

        with self._lock:
            if material_str in self._indexers:
                return self._indexers[material_str]

            # Create new indexer
            indexer = PositionIndexer(material)
            self._indexers[material_str] = indexer
            return indexer

    def _extract_material(self, position: ChessPosition) -> Optional[MaterialSignature]:
        """
        Extract material signature from a position.

        Args:
            position: ChessPosition

        Returns:
            MaterialSignature or None
        """
        # Parse FEN to get piece positions
        fen = position.fen
        board_part = fen.split()[0]

        white_pieces = []
        black_pieces = []

        # Map FEN characters to piece types
        piece_types = {
            'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
            'p': 0, 'n': 1, 'b': 2, 'r': 3, 'q': 4, 'k': 5
        }

        for char in board_part:
            if char in piece_types:
                if char.isupper():
                    white_pieces.append(piece_types[char])
                else:
                    black_pieces.append(piece_types[char])

        try:
            return MaterialSignature.from_pieces(white_pieces, black_pieces)
        except Exception:
            return None

    def _position_to_index(
        self,
        position: ChessPosition,
        indexer: PositionIndexer
    ) -> Optional[int]:
        """
        Convert position to tablebase index.

        Args:
            position: ChessPosition
            indexer: PositionIndexer for this material

        Returns:
            Index or None
        """
        # Parse FEN to extract piece squares
        white_squares, black_squares = self._fen_to_squares(position.fen)
        if not white_squares or not black_squares:
            return None

        try:
            return indexer.encode(white_squares, black_squares)
        except Exception:
            return None

    def _fen_to_squares(self, fen: str) -> tuple:
        """
        Extract piece squares from FEN, ordered by piece type.

        Args:
            fen: FEN string

        Returns:
            (white_squares, black_squares) sorted by piece type
        """
        try:
            board_part = fen.split()[0]
            ranks = board_part.split('/')

            # Collect pieces with their types and squares
            white_pieces = []  # [(piece_type, square), ...]
            black_pieces = []

            piece_types = {
                'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
                'p': 0, 'n': 1, 'b': 2, 'r': 3, 'q': 4, 'k': 5
            }

            for rank_idx, rank_str in enumerate(ranks):
                rank = 7 - rank_idx
                file = 0

                for char in rank_str:
                    if char.isdigit():
                        file += int(char)
                    else:
                        square = rank * 8 + file
                        piece_type = piece_types.get(char)

                        if piece_type is not None:
                            if char.isupper():
                                white_pieces.append((piece_type, square))
                            else:
                                black_pieces.append((piece_type, square))

                        file += 1

            # Sort by piece type, then extract squares
            white_pieces.sort(key=lambda x: x[0])
            black_pieces.sort(key=lambda x: x[0])

            white_squares = [sq for _, sq in white_pieces]
            black_squares = [sq for _, sq in black_pieces]

            return white_squares, black_squares

        except Exception:
            return None, None

    def available_tablebases(self) -> list:
        """
        Get list of available material configurations.

        Returns:
            List of material signature strings
        """
        tablebases = []
        if self.tablebase_dir.exists():
            for filepath in self.tablebase_dir.glob('*.cmgtb'):
                tablebases.append(filepath.stem)
        return sorted(tablebases)

    def close_all(self):
        """Close all open tablebase files."""
        with self._lock:
            for storage in self._cache.values():
                storage.close()
            self._cache.clear()

    def __repr__(self) -> str:
        available = self.available_tablebases()
        return f"TablebaseProbe(dir='{self.tablebase_dir}', available={len(available)})"
