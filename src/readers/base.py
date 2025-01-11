"""Abstract base for readers"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from src.core.data_types import (
    ColumnMapping,
    ColumnRequirement,
    FileConfig,
    TableStructure,
    TimestampType,
)
from src.core.exceptions import DataProcessingError, TimestampProcessingError

logger = logging.getLogger(__name__)


@dataclass
class TableData:
    """Holds processed data for a single table."""

    name: str
    dataframe: pd.DataFrame
    missing_required_columns: List[str]
    timestamp_type: Optional[TimestampType] = None


class BaseReader(ABC):
    """Abstract base class for all file format readers."""

    def __init__(self, path: Path, file_config: FileConfig):
        if not path.exists():
            raise ValueError(f"File not found: {path}")

        self.file_path = path
        self.file_config = file_config

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources if needed."""
        self._cleanup()

    def _cleanup(self):
        """Override this method in derived classes if cleanup is needed."""

    @abstractmethod
    def read_table(self, table_structure: TableStructure) -> Optional[TableData]:
        """Read and process a single table according to its structure.

        This method must be implemented by each specific reader.
        """

    def read_all_tables(self) -> Dict[str, TableData]:
        """Read and process all tables defined in the file configuration."""
        results = {}
        for table_config in self.file_config.tables:
            table_data = self.read_table(table_config)
            if table_data is not None:
                if table_data.missing_required_columns:
                    logger.warning(
                        "Table %s missing required data in columns: %s",
                        table_data.name,
                        table_data.missing_required_columns,
                    )
                results[table_data.name] = table_data
            else:
                logger.error("Failed to process table: %s", table_config.name)

        return results

    def detect_timestamp_format(self, series: pd.Series) -> TimestampType:
        """Detect the format of timestamp data, assuming chronological order."""
        try:
            # Sample timestamps without sorting
            sample = series.dropna().head(10)
            if sample.empty:
                logger.warning("No non-null timestamps found in sample")
                return TimestampType.UNKNOWN

            # Check if values are monotonically increasing
            if not sample.is_monotonic_increasing:
                logger.warning("Timestamps are not in chronological order")
                return TimestampType.UNKNOWN

            # pylint: disable=R1705
            # Supress pylint warning and use elif functionality for efficiency
            # Check for UNIX epoch formats
            if all(sample.astype(float) < 1e10):  # Seconds
                logger.debug("Detected timestamp type: UNIX_SECONDS")
                return TimestampType.UNIX_SECONDS
            elif all(sample.astype(float) < 1e13):  # Milliseconds
                logger.debug("Detected timestamp type: UNIX_MILLISECONDS")
                return TimestampType.UNIX_MILLISECONDS
            elif all(sample.astype(float) < 1e16):  # Microseconds
                logger.debug("Detected timestamp type: UNIX_MICROSECONDS")
                return TimestampType.UNIX_MICROSECONDS

            # Try ISO 8601 for string timestamps
            try:
                pd.to_datetime(sample, utc=True)
                logger.debug("Detected timestamp type: ISO_8601")
                return TimestampType.ISO_8601
            except TimestampProcessingError:
                pass

            logger.warning("Could not determine timestamp format")
            return TimestampType.UNKNOWN

        except TimestampProcessingError as e:
            logger.error("Error during timestamp detection: %s", e)
            return TimestampType.UNKNOWN

    def _convert_timestamp_to_utc(
        self, df: pd.DataFrame, timestamp_column: str
    ) -> Tuple[pd.DataFrame, TimestampType]:
        """Convert timestamp column to UTC datetime and set as index."""
        fmt = self.detect_timestamp_format(df[timestamp_column])

        if fmt == TimestampType.UNKNOWN:
            raise TimestampProcessingError(
                f"Could not detect timestamp format for column {timestamp_column}"
            )

        try:
            if fmt == TimestampType.UNIX_SECONDS:
                df[timestamp_column] = pd.to_datetime(
                    df[timestamp_column], unit="s", utc=True
                )
            elif fmt == TimestampType.UNIX_MILLISECONDS:
                df[timestamp_column] = pd.to_datetime(
                    df[timestamp_column], unit="ms", utc=True
                )
            elif fmt == TimestampType.UNIX_MICROSECONDS:
                df[timestamp_column] = pd.to_datetime(
                    df[timestamp_column], unit="us", utc=True
                )
            elif fmt == TimestampType.ISO_8601:
                df[timestamp_column] = pd.to_datetime(df[timestamp_column], utc=True)

            return df.set_index(timestamp_column).sort_index(), fmt

        except DataProcessingError as e:
            logger.error("Error converting timestamps: %s", e)
            raise DataProcessingError(f"Invalid value: {timestamp_column}") from e

    def _validate_required_data(
        self, df: pd.DataFrame, columns: List[ColumnMapping]
    ) -> List[str]:
        """Check for missing data in required columns."""
        missing_required = []
        for col in columns:
            if (
                col.requirement == ColumnRequirement.REQUIRED_WITH_DATA
                and col.source_name in df.columns
                and df[col.source_name].isna().all()
            ):
                missing_required.append(col.source_name)
        return missing_required

    @staticmethod
    def _validate_identifier(identifier: str) -> bool:
        """Validate that an identifier only contains safe characters."""
        return all(c.isalnum() or c in ["_", "."] for c in identifier)
