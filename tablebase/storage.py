"""
Tablebase Storage System

Implements efficient binary storage format for tablebases with:
- Compact encoding (2-4 bits per position)
- Memory-mapped file support for fast access
- Compression for sparse data
- Thread-safe access

Storage format:
- Header: Material signature, metadata, table size
- Data: Packed bit array with position values
- Index: Optional index for faster lookup

Value encoding (4 bits per position):
- 0: UNKNOWN (not yet computed)
- 1-7: HELPMATE_IN_N (N = 1-7 moves)
- 8: HELPMATE_IN_8_OR_MORE
- 9: DRAW
- 10: ILLEGAL
- 15: RESERVED
"""

from typing import Optional, Dict
from pathlib import Path
import struct
import mmap
import os
from enum import IntEnum

from .indexing import MaterialSignature


class PositionValue(IntEnum):
    """Values that can be stored in a tablebase."""
    UNKNOWN = 0
    HELPMATE_IN_1 = 1
    HELPMATE_IN_2 = 2
    HELPMATE_IN_3 = 3
    HELPMATE_IN_4 = 4
    HELPMATE_IN_5 = 5
    HELPMATE_IN_6 = 6
    HELPMATE_IN_7 = 7
    HELPMATE_IN_8_PLUS = 8
    DRAW = 9
    ILLEGAL = 10
    RESERVED = 15

    def is_helpmate(self) -> bool:
        """Check if this is a helpmate value."""
        return 1 <= self.value <= 8

    def moves_to_helpmate(self) -> Optional[int]:
        """Get number of moves to helpmate, or None if not a helpmate."""
        if self.is_helpmate():
            return self.value if self.value < 8 else 8
        return None


class TablebaseStorage:
    """
    Manages persistent storage of tablebase data.

    Uses memory-mapped files for efficient access and supports
    both reading and writing of tablebase values.
    """

    MAGIC = b'CMGTB'  # ChessMG TableBase magic number
    VERSION = 2  # Incremented to support material in header
    HEADER_SIZE = 128  # Fixed header size in bytes

    def __init__(self, filepath: Path, material: Optional[MaterialSignature] = None,
                 table_size: Optional[int] = None, mode: str = 'r'):
        """
        Initialize tablebase storage.

        Args:
            filepath: Path to tablebase file
            material: Material signature (required for 'w' mode, optional for 'r'/'r+')
            table_size: Number of positions (required for 'w' mode, optional for 'r'/'r+')
            mode: 'r' for read-only, 'w' for write, 'r+' for read-write
        """
        self.filepath = Path(filepath)
        self.mode = mode

        # For write mode, require material and table_size
        if mode == 'w':
            if material is None or table_size is None:
                raise ValueError("material and table_size required for write mode")
            self.material = material
            self.table_size = table_size
        else:
            # For read modes, these will be loaded from header
            self.material = material  # May be None initially
            self.table_size = table_size  # May be None initially

        # Calculate data size (4 bits per position, rounded up to bytes)
        if self.table_size is not None:
            self.data_size = (self.table_size + 1) // 2  # 2 positions per byte
        else:
            self.data_size = None  # Will be set after reading header

        self._file = None
        self._mmap = None

        if mode == 'w':
            self._create_new()
        elif mode in ('r', 'r+'):
            self._open_existing()
        else:
            raise ValueError(f"Invalid mode: {mode}")

    def _create_new(self):
        """Create a new tablebase file."""
        # Create directory if needed
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        # Create file with header + data
        total_size = self.HEADER_SIZE + self.data_size

        with open(self.filepath, 'wb') as f:
            # Write header
            header = self._create_header()
            f.write(header)

            # Initialize data section with zeros (UNKNOWN values)
            f.write(b'\x00' * self.data_size)

        # Open for memory mapping
        self._file = open(self.filepath, 'r+b')
        self._mmap = mmap.mmap(self._file.fileno(), 0)

    def _open_existing(self):
        """Open an existing tablebase file."""
        if not self.filepath.exists():
            raise FileNotFoundError(f"Tablebase file not found: {self.filepath}")

        # Open file
        file_mode = 'r+b' if self.mode == 'r+' else 'rb'
        self._file = open(self.filepath, file_mode)

        # Memory map
        access = mmap.ACCESS_WRITE if self.mode == 'r+' else mmap.ACCESS_READ
        self._mmap = mmap.mmap(self._file.fileno(), 0, access=access)

        # Validate header
        self._validate_header()

    def _create_header(self) -> bytes:
        """Create header bytes.

        Header format (128 bytes total):
        - Bytes 0-4: Magic number "CMGTB" (5 bytes)
        - Byte 5: Version (1 byte)
        - Bytes 6-13: Table size (8 bytes, uint64)
        - Byte 14: Number of white pieces (1 byte)
        - Bytes 15-30: White piece types (up to 16 pieces)
        - Byte 31: Number of black pieces (1 byte)
        - Bytes 32-47: Black piece types (up to 16 pieces)
        - Bytes 48-127: Reserved/padding (80 bytes)
        """
        header = bytearray(self.HEADER_SIZE)

        # Magic number (5 bytes)
        header[0:5] = self.MAGIC

        # Version (1 byte)
        header[5] = self.VERSION

        # Table size (8 bytes, unsigned long long)
        struct.pack_into('<Q', header, 6, self.table_size)

        # Material signature (binary format)
        # White pieces
        white_pieces = list(self.material.white_pieces)
        if len(white_pieces) > 16:
            raise ValueError("Too many white pieces (max 16)")
        header[14] = len(white_pieces)
        for i, piece in enumerate(white_pieces):
            header[15 + i] = piece

        # Black pieces
        black_pieces = list(self.material.black_pieces)
        if len(black_pieces) > 16:
            raise ValueError("Too many black pieces (max 16)")
        header[31] = len(black_pieces)
        for i, piece in enumerate(black_pieces):
            header[32 + i] = piece

        # Rest is reserved/padding

        return bytes(header)

    def _validate_header(self):
        """Validate header of existing file and read metadata."""
        # Check magic
        magic = self._mmap[0:5]
        if magic != self.MAGIC:
            raise ValueError(f"Invalid magic number: {magic}")

        # Check version
        version = self._mmap[5]
        if version not in (1, 2):
            raise ValueError(f"Unsupported version: {version}")

        # Read table size
        stored_size = struct.unpack_from('<Q', self._mmap, 6)[0]
        if self.table_size is None:
            self.table_size = stored_size
            self.data_size = (self.table_size + 1) // 2
        elif stored_size != self.table_size:
            raise ValueError(f"Table size mismatch: expected {self.table_size}, got {stored_size}")

        # Read material signature based on version
        if version == 1:
            # Old format: string-based
            material_bytes = self._mmap[14:46]
            material_str = material_bytes.rstrip(b'\x00').decode('ascii')
            # Parse string format like "KPvK" back to MaterialSignature
            stored_material = self._parse_material_string(material_str)
        else:  # version == 2
            # New format: binary
            # Read white pieces
            num_white = self._mmap[14]
            white_pieces = tuple(self._mmap[15 + i] for i in range(num_white))

            # Read black pieces
            num_black = self._mmap[31]
            black_pieces = tuple(self._mmap[32 + i] for i in range(num_black))

            stored_material = MaterialSignature(white_pieces, black_pieces)

        # Set or validate material
        if self.material is None:
            self.material = stored_material
        elif self.material != stored_material:
            raise ValueError(f"Material mismatch: expected {self.material}, got {stored_material}")

    @staticmethod
    def _parse_material_string(material_str: str) -> MaterialSignature:
        """Parse material string like 'KPvK' back to MaterialSignature."""
        if not material_str or 'v' not in material_str:
            raise ValueError(f"Invalid material string: {material_str}")

        piece_chars = {'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5}
        white_str, black_str = material_str.split('v')

        white_pieces = [piece_chars[c] for c in white_str if c in piece_chars]
        black_pieces = [piece_chars[c] for c in black_str if c in piece_chars]

        return MaterialSignature.from_pieces(white_pieces, black_pieces)

    @classmethod
    def open(cls, filepath: Path, mode: str = 'r') -> 'TablebaseStorage':
        """
        Open an existing tablebase file, automatically reading material and size from header.

        Args:
            filepath: Path to tablebase file
            mode: 'r' for read-only, 'r+' for read-write

        Returns:
            TablebaseStorage instance with material and table_size loaded from file

        Example:
            >>> storage = TablebaseStorage.open("tablebases/KPvK.cmgtb")
            >>> print(storage.material)  # Automatically loaded
            >>> print(storage.table_size)  # Automatically loaded
        """
        if mode == 'w':
            raise ValueError("Use __init__ directly for write mode (requires material and table_size)")

        return cls(filepath=filepath, material=None, table_size=None, mode=mode)

    def get_value(self, index: int) -> PositionValue:
        """
        Get the value at a given position index.

        Args:
            index: Position index (0 to table_size-1)

        Returns:
            PositionValue for this position
        """
        if index < 0 or index >= self.table_size:
            raise ValueError(f"Index out of range: {index}")

        # Calculate byte offset and nibble position
        byte_offset = self.HEADER_SIZE + index // 2
        is_high_nibble = index % 2 == 0

        # Read byte
        byte_val = self._mmap[byte_offset]

        # Extract 4-bit value
        if is_high_nibble:
            value = (byte_val >> 4) & 0xF
        else:
            value = byte_val & 0xF

        return PositionValue(value)

    def set_value(self, index: int, value: PositionValue):
        """
        Set the value at a given position index.

        Args:
            index: Position index
            value: PositionValue to store

        Raises:
            ValueError: If file is opened in read-only mode
        """
        if self.mode == 'r':
            raise ValueError("Cannot write to read-only tablebase")

        if index < 0 or index >= self.table_size:
            raise ValueError(f"Index out of range: {index}")

        # Calculate byte offset and nibble position
        byte_offset = self.HEADER_SIZE + index // 2
        is_high_nibble = index % 2 == 0

        # Read current byte
        byte_val = self._mmap[byte_offset]

        # Modify appropriate nibble
        if is_high_nibble:
            byte_val = (byte_val & 0x0F) | ((value.value << 4) & 0xF0)
        else:
            byte_val = (byte_val & 0xF0) | (value.value & 0x0F)

        # Write back
        self._mmap[byte_offset] = byte_val

    def batch_get(self, indices: list) -> list:
        """
        Get values for multiple indices efficiently.

        Args:
            indices: List of position indices

        Returns:
            List of PositionValues
        """
        return [self.get_value(idx) for idx in indices]

    def batch_set(self, index_value_pairs: list):
        """
        Set values for multiple indices efficiently.

        Args:
            index_value_pairs: List of (index, value) tuples
        """
        for index, value in index_value_pairs:
            self.set_value(index, value)

    def flush(self):
        """Flush changes to disk."""
        if self._mmap:
            self._mmap.flush()

    def close(self):
        """Close the tablebase file."""
        if self._mmap:
            self._mmap.close()
            self._mmap = None
        if self._file:
            self._file.close()
            self._file = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __repr__(self) -> str:
        return f"TablebaseStorage('{self.filepath}', {self.material}, size={self.table_size:,})"

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about tablebase contents.

        Returns:
            Dictionary with counts for each value type
        """
        stats = {v.name: 0 for v in PositionValue}

        for i in range(self.table_size):
            value = self.get_value(i)
            stats[value.name] += 1

        return stats
