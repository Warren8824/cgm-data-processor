"""CSV Reader for confirmed configuration with CSV FileType.

This module provides CSV file reading capabilities for the data processing system,
treating each CSV file as a single table of data.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from src.core.data_types import ColumnRequirement, FileConfig, FileType, TableStructure
from src.core.exceptions import (
    DataExistsError,
    DataProcessingError,
    DataValidationError,
    FileAccessError,
    ProcessingError,
)

from .base import BaseReader, TableData

logger = logging.getLogger(__name__)


@BaseReader.register(FileType.CSV)
class CSVReader(BaseReader):
    """Reads and processes CSV files according to the provided format configuration."""

    def __init__(self, path: Path, file_config: FileConfig):
        super().__init__(path, file_config)
        self._data = None

    def _cleanup(self):
        """Cleanup any held resources."""
        self._data = None

    def read_table(self, table_structure: TableStructure) -> Optional[TableData]:
        """Read and process a single table according to its structure.

        For CSV files, we treat each file as a single table, reading all data at once
        and caching it for subsequent operations if needed.
        """
        try:
            # Read data if not already cached
            if self._data is None:
                try:
                    self._data = pd.read_csv(
                        self.file_path,
                        encoding="utf-8",
                        low_memory=False,  # Prevent mixed type inference warnings
                    )
                except Exception as e:
                    raise FileAccessError(f"Failed to read CSV file: {e}") from e

            if self._data.empty:
                raise DataExistsError(f"No data found in CSV file {self.file_path}")

            # Get required columns
            columns_to_read = [
                col.source_name
                for col in table_structure.columns
                if col.requirement != ColumnRequirement.CONFIRMATION_ONLY
            ]
            columns_to_read.append(table_structure.timestamp_column)

            # Check for missing columns
            missing_columns = [
                col for col in columns_to_read if col not in self._data.columns
            ]
            if missing_columns:
                logger.error(
                    "Required columns missing from CSV: %s", ", ".join(missing_columns)
                )
                return None

            # Select only needed columns and make a copy
            df = self._data[columns_to_read].copy()

            # Process timestamps
            df, fmt = self._convert_timestamp_to_utc(
                df, table_structure.timestamp_column
            )

            # Validate required data
            missing_required = self._validate_required_data(df, table_structure.columns)

            return TableData(
                name=table_structure.name,
                dataframe=df,
                missing_required_columns=missing_required,
                timestamp_type=fmt,
            )

        except DataValidationError as e:
            logger.error("Validation error: %s", e)
            return None
        except DataExistsError as e:
            logger.error("No data error: %s", e)
            return None
        except DataProcessingError as e:
            logger.error("Processing error: %s", e)
            return None
        except ProcessingError as e:
            logger.error("Unexpected error processing CSV: %s", e)
            return None
