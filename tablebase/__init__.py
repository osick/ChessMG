"""
ChessMG Tablebase Module

Efficient tablebase generation and probing for chess problems.
Supports helpmate and other stipulations with compact storage and fast lookups.
"""

from .indexing import PositionIndexer, MaterialSignature
from .generator import TablebaseGenerator
from .probe import TablebaseProbe
from .storage import TablebaseStorage

__all__ = [
    'PositionIndexer',
    'MaterialSignature',
    'TablebaseGenerator',
    'TablebaseProbe',
    'TablebaseStorage',
]
