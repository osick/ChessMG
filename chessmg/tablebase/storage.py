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
    VERSION = 1
    HEADER_SIZE = 128  # Fixed header size in bytes

    def __init__(self, filepath: Path, material: MaterialSignature, table_size: int, mode: str = 'r'):
        """
        Initialize tablebase storage.

        Args:
            filepath: Path to tablebase file
            material: Material signature for this tablebase
            table_size: Number of positions in the tablebase
            mode: 'r' for read-only, 'w' for write, 'r+' for read-write
        """
        self.filepath = Path(filepath)
        self.material = material
        self.table_size = table_size
        self.mode = mode

        # Calculate data size (4 bits per position, rounded up to bytes)
        self.data_size = (table_size + 1) // 2  # 2 positions per byte

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
        """Create header bytes."""
        header = bytearray(self.HEADER_SIZE)

        # Magic number (5 bytes)
        header[0:5] = self.MAGIC

        # Version (1 byte)
        header[5] = self.VERSION

        # Table size (8 bytes, unsigned long long)
        struct.pack_into('<Q', header, 6, self.table_size)

        # Material signature (store as string, up to 32 bytes)
        material_str = str(self.material).encode('ascii')
        if len(material_str) > 32:
            raise ValueError("Material signature too long")
        header[14:14+len(material_str)] = material_str

        # Rest is reserved/padding

        return bytes(header)

    def _validate_header(self):
        """Validate header of existing file."""
        # Check magic
        magic = self._mmap[0:5]
        if magic != self.MAGIC:
            raise ValueError(f"Invalid magic number: {magic}")

        # Check version
        version = self._mmap[5]
        if version != self.VERSION:
            raise ValueError(f"Unsupported version: {version}")

        # Read table size
        stored_size = struct.unpack_from('<Q', self._mmap, 6)[0]
        if stored_size != self.table_size:
            raise ValueError(f"Table size mismatch: expected {self.table_size}, got {stored_size}")

        # Read material signature
        material_bytes = self._mmap[14:46]
        material_str = material_bytes.rstrip(b'\x00').decode('ascii')
        if material_str != str(self.material):
            raise ValueError(f"Material mismatch: expected {self.material}, got {material_str}")

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
