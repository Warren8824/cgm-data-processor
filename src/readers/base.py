"""Abstract base for readers with automatic reader selection.

This module provides the base reader functionality and automatic reader selection based on
file types. It supports timestamp processing, data validation, and resource management
while allowing automatic mapping of file types to their appropriate readers.
"""

import logging
import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Type, TypeVar

import pandas as pd

from src.core.data_types import (
    ColumnMapping,
    ColumnRequirement,
    DeviceFormat,
    FileConfig,
    FileType,
    TableStructure,
    TimestampType,
)
from src.core.exceptions import (
    DataProcessingError,
    ReaderError,
    TimestampProcessingError,
)

logger = logging.getLogger(__name__)

# Create a type variable for the reader class at module level
T = TypeVar("T")


@dataclass
class TableData:
    """Holds processed data for a single table."""

    name: str
    dataframe: pd.DataFrame
    missing_required_columns: List[str]
    timestamp_type: Optional[TimestampType] = None


class BaseReader(ABC):
    """Abstract base class for all file format readers.

    This class provides core functionality for reading diabetes device data files
    and automatic reader selection based on file types. It handles timestamp processing,
    data validation, and resource management.
    """

    _readers: Dict[FileType, Type["BaseReader"]] = {}

    @classmethod
    def register(cls, file_type: FileType) -> Callable[[Type[T]], Type[T]]:
        """Register a reader class for a specific file type.

        Args:
            file_type: FileType enum value to associate with the reader

        Returns:
            Callable: Decorator function that registers the reader class
        """

        def wrapper(reader_cls: Type[T]) -> Type[T]:
            cls._readers[file_type] = reader_cls
            return reader_cls

        return wrapper

    @classmethod
    def get_reader_for_format(cls, fmt: DeviceFormat, file_path: Path) -> "BaseReader":
        """Get appropriate reader instance for the detected format.

        Args:
            fmt: Detected device format specification
            file_path: Path to the data file

        Returns:
            Instance of appropriate reader class

        Raises:
            ReaderError: If no reader is registered for the file type
        """
        for file_config in fmt.files:
            if Path(file_path).match(file_config.name_pattern):
                reader_cls = cls._readers.get(file_config.file_type)
                if reader_cls is None:
                    raise ReaderError(
                        f"No reader registered for file type: {file_config.file_type.value}"
                    )
                return reader_cls(file_path, file_config)

        raise ReaderError(f"No matching file configuration found for {file_path}")

    def __init__(self, path: Path, file_config: FileConfig):
        """Initialize reader with file path and configuration.

        Args:
            path: Path to the data file
            file_config: Configuration for the file format

        Raises:
            ValueError: If file does not exist
        """
        if not path.exists():
            raise ValueError(f"File not found: {path}")

        self.file_path = path
        self.file_config = file_config

    def __enter__(self):
        """Context manager entry."""
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
                    logger.debug(
                        "Table %s missing required data in columns: %s",
                        table_data.name,
                        table_data.missing_required_columns,
                    )
                results[table_data.name] = table_data
            else:
                logger.error("Failed to process table: %s", table_config.name)

        return results

    def detect_timestamp_format(self, series: pd.Series) -> Tuple[TimestampType, dict]:
        """Detect the format of timestamp data, assuming chronological order."""
        try:
            # Sample timestamps without sorting
            sample = series.dropna().head(20)
            if sample.empty:
                logger.warning("No non-null timestamps found in sample")
                return TimestampType.UNKNOWN, {}

            # Warn if timestamps are not monotonic but continue - files may be unsorted
            if not sample.is_monotonic_increasing:
                logger.warning(
                    "Timestamps are not in chronological order; continuing with detection"
                )

            # First, attempt to safely coerce to numeric values to detect epoch timestamps
            numeric = pd.to_numeric(sample, errors="coerce")
            if numeric.notna().any():
                nums = numeric.dropna().astype(float)
                # Check for UNIX epoch formats using magnitude heuristics
                if (nums < 1e10).all():  # Seconds
                    logger.debug("Detected timestamp type: UNIX_SECONDS")
                    return TimestampType.UNIX_SECONDS, {"unit": "s", "utc": True}
                if (nums < 1e13).all():  # Milliseconds
                    logger.debug("Detected timestamp type: UNIX_MILLISECONDS")
                    return TimestampType.UNIX_MILLISECONDS, {"unit": "ms", "utc": True}
                if (nums < 1e16).all():  # Microseconds
                    logger.debug("Detected timestamp type: UNIX_MICROSECONDS")
                    return TimestampType.UNIX_MICROSECONDS, {"unit": "us", "utc": True}

            # Not numeric epochs; try parsing strategies for string datetimes.
            # 1) Try pandas' infer (fast if inferable)
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message=(
                        "Could not infer format, so each element will be parsed individually, falling back to `dateutil`"
                    ),
                )
                try:
                    parsed = pd.to_datetime(sample, utc=True)
                except ReaderError:
                    parsed = pd.to_datetime(sample, utc=True, errors="coerce")

            parsed_ratio = parsed.notna().mean()
            if parsed_ratio >= 0.8:
                logger.debug("Detected timestamp type: ISO_8601 (inferred)")
                return TimestampType.ISO_8601, {"utc": True}

            # 2) Try dayfirst parsing (common in dd/mm/yy files)
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message=(
                        "Could not infer format, so each element will be parsed individually, falling back to `dateutil`"
                    ),
                )
                parsed_df = pd.to_datetime(
                    sample, dayfirst=True, utc=True, errors="coerce"
                )
            parsed_ratio_df = parsed_df.notna().mean()
            if parsed_ratio_df >= 0.8:
                logger.debug("Detected timestamp type: ISO_8601 (dayfirst)")
                return TimestampType.ISO_8601, {"utc": True, "dayfirst": True}

            # 3) Try a small list of explicit formats (common patterns)
            common_formats = [
                "%d/%m/%y %H:%M",
                "%d/%m/%Y %H:%M",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%m/%d/%y %H:%M",
                "%m/%d/%Y %H:%M",
            ]
            for fmt in common_formats:
                parsed_fmt = pd.to_datetime(
                    sample, format=fmt, errors="coerce", utc=True
                )
                if parsed_fmt.notna().mean() >= 0.8:
                    logger.debug("Detected timestamp type: ISO_8601 (format=%s)", fmt)
                    return TimestampType.ISO_8601, {"format": fmt, "utc": True}

            logger.warning("Could not determine timestamp format")
            return TimestampType.UNKNOWN, {}

        except ReaderError as e:
            logger.error("Error during timestamp detection: %s", e)
            return TimestampType.UNKNOWN, {}

    def _convert_timestamp_to_utc(
        self, df: pd.DataFrame, timestamp_column: str
    ) -> Tuple[pd.DataFrame, TimestampType]:
        """Convert timestamp column to UTC datetime and set as index."""
        fmt, parse_kwargs = self.detect_timestamp_format(df[timestamp_column])

        if fmt == TimestampType.UNKNOWN:
            raise TimestampProcessingError(
                f"Could not detect timestamp format for column {timestamp_column}"
            )

        try:
            # Handle epoch numeric formats uniformly using parse_kwargs
            if fmt in (
                TimestampType.UNIX_SECONDS,
                TimestampType.UNIX_MILLISECONDS,
                TimestampType.UNIX_MICROSECONDS,
            ):
                df[timestamp_column] = pd.to_datetime(
                    df[timestamp_column], unit=parse_kwargs.get("unit", "s"), utc=True
                )
            elif fmt == TimestampType.ISO_8601:
                # Use the parse_kwargs discovered earlier to parse consistently.
                try:
                    with warnings.catch_warnings():
                        warnings.filterwarnings(
                            "ignore",
                            message=(
                                "Could not infer format, so each element will be parsed individually, falling back to `dateutil`"
                            ),
                        )
                        df[timestamp_column] = pd.to_datetime(
                            df[timestamp_column],
                            **{k: v for k, v in parse_kwargs.items() if k != "format"},
                        )
                except ReaderError:
                    # If parse_kwargs included a format string, try that explicitly
                    if "format" in parse_kwargs:
                        df[timestamp_column] = pd.to_datetime(
                            df[timestamp_column],
                            format=parse_kwargs["format"],
                            utc=True,
                        )
                    else:
                        # As a last resort try dayfirst=True
                        df[timestamp_column] = pd.to_datetime(
                            df[timestamp_column], dayfirst=True, utc=True
                        )
            # set index and return
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
