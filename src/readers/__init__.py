"""Reader initialization and registration."""

from .base import BaseReader
from .csv import CSVReader
from .sqlite import SQLiteReader

# from .xml import XMLReader  # When created

__all__ = [
    "BaseReader",
    "SQLiteReader",
    "CSVReader",
    # 'XMLReader',
]
