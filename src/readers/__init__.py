"""Reader initialization and registration."""

from .base import BaseReader
from .sqlite import SQLiteReader

# from .csv import CSVReader  # When created
# from .xml import XMLReader  # When created

__all__ = [
    "BaseReader",
    "SQLiteReader",
    # 'CSVReader',
    # 'XMLReader',
]
