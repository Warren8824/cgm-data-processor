"""Abstract base for readers with automatic reader selection.

This module provides the base reader functionality and automatic reader selection based on
file types. It supports timestamp processing, data validation, and resource management
while allowing automatic mapping of file types to their appropriate readers.
"""

import logging
import re
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
from src.core.exceptions import ReaderError, TimestampProcessingError

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
        """Detect timestamp format using a small deterministic heuristic.

        Strategy (simple & fast):
        - sample up to 50 non-null values
        - detect numeric epochs first
        - look for obvious ISO-like markers (T, Z, timezone offsets)
        - for hyphen/slash date starts try explicit day-first formats if day>12 found
        - attempt a compact list of explicit formats with a high-acceptance threshold
        - fallback to pandas inference (utc=True) if explicit formats fail

        Returns (TimestampType, parse_kwargs) where parse_kwargs is suitable for
        passing to pd.to_datetime (e.g., {'format': ..., 'utc': True} or {'dayfirst': True,'utc':True}).
        """
        try:
            sample = series.dropna().astype(str).str.strip().head(50)
            if sample.empty:
                logger.warning("No non-null timestamps found in sample")
                return TimestampType.UNKNOWN, {}

            # numeric epochs
            numeric = pd.to_numeric(sample, errors="coerce")
            if numeric.notna().any():
                nums = numeric.dropna().astype(float)
                if (nums > 1e8).all() and (nums < 1e12).all():
                    return TimestampType.UNIX_SECONDS, {"unit": "s", "utc": True}
                if (nums > 1e11).all() and (nums < 1e15).all():
                    return TimestampType.UNIX_MILLISECONDS, {"unit": "ms", "utc": True}

            # quick ISO-like heuristic
            joined = " ".join(sample.head(10).tolist()).upper()
            if "T" in joined and ("Z" in joined or "+" in joined):
                return TimestampType.ISO_8601, {"utc": True}

            # Check for hyphen/slash date leading pattern (d/m/Y or m/d/Y)
            dayfirst_candidate = False
            sep_match = sample.str.match(r"^\s*\d{1,2}[-/]\d{1,2}[-/]\d{2,4}")
            if sep_match.any():
                # If any day > 12 then dayfirst is almost certainly correct
                for v in sample:
                    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})", v)
                    if m:
                        day = int(m.group(1))
                        if day > 12:
                            dayfirst_candidate = True
                            break

            # Small explicit formats list (keep compact)
            explicit = [
                "%d-%m-%Y %H:%M",
                "%d/%m/%Y %H:%M",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%d-%m-%Y %H:%M:%S",
                "%m/%d/%Y %H:%M",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%SZ",
                "%d-%m-%Y %I:%M %p",
            ]

            sample_norm = sample.str.replace(r"\s+UTC$|\s+GMT$", "", regex=True)
            sample_norm = sample_norm.str.replace(r"\s+", " ", regex=True)

            # If dayfirst is obvious, try day-first explicit formats first
            if dayfirst_candidate:
                for fmt in ["%d-%m-%Y %H:%M", "%d/%m/%Y %H:%M", "%d-%m-%Y %H:%M:%S"]:
                    parsed = pd.to_datetime(
                        sample_norm, format=fmt, errors="coerce", utc=True
                    )
                    if parsed.notna().mean() >= 0.95:
                        return TimestampType.ISO_8601, {"format": fmt, "utc": True}

            # Try compact explicit list
            for fmt in explicit:
                parsed = pd.to_datetime(
                    sample_norm, format=fmt, errors="coerce", utc=True
                )
                if parsed.notna().mean() >= 0.95:
                    return TimestampType.ISO_8601, {"format": fmt, "utc": True}

            # If we saw a hyphen/slash pattern but not decisive, prefer dayfirst inference
            if sep_match.any() and not dayfirst_candidate:
                parsed_dayfirst = pd.to_datetime(
                    sample, dayfirst=True, utc=True, errors="coerce"
                )
                if parsed_dayfirst.notna().mean() >= 0.9:
                    return TimestampType.ISO_8601, {"dayfirst": True, "utc": True}

            # Last resort: pandas inference
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message=(
                        "Could not infer format, so each element will be parsed individually, falling back to `dateutil`"
                    ),
                )
                inferred = pd.to_datetime(sample, utc=True, errors="coerce")
            if inferred.notna().mean() >= 0.9:
                return TimestampType.ISO_8601, {"utc": True}

            return TimestampType.UNKNOWN, {}

        except TimestampProcessingError as e:
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
            # Epoch handling
            if fmt in (TimestampType.UNIX_SECONDS, TimestampType.UNIX_MILLISECONDS):
                unit = parse_kwargs.get("unit", "s")
                df[timestamp_column] = pd.to_datetime(
                    df[timestamp_column], unit=unit, utc=True
                )
            elif fmt == TimestampType.ISO_8601:
                # If an explicit format was provided, try it first but with coercion
                if "format" in parse_kwargs:
                    parsed = pd.to_datetime(
                        df[timestamp_column].astype(str),
                        format=parse_kwargs["format"],
                        errors="coerce",
                        utc=True,
                    )
                    success = parsed.notna().mean()
                    if success >= 0.9:
                        df[timestamp_column] = parsed
                    else:
                        # fallback to pandas with any provided flags (dayfirst/utc)
                        kwargs = {
                            k: v for k, v in parse_kwargs.items() if k != "format"
                        }
                        df[timestamp_column] = pd.to_datetime(
                            df[timestamp_column].astype(str), errors="coerce", **kwargs
                        )
                else:
                    # use parse kwargs (e.g., dayfirst) or generic inference
                    df[timestamp_column] = pd.to_datetime(
                        df[timestamp_column].astype(str),
                        errors="coerce",
                        **parse_kwargs,
                    )

            # Ensure timezone-awareness and set index
            if df[timestamp_column].dt.tz is None:
                df[timestamp_column] = df[timestamp_column].dt.tz_localize("UTC")

            return df.set_index(timestamp_column).sort_index(), fmt

        except Exception as e:
            logger.error("Error converting timestamps: %s", e)
            raise TimestampProcessingError(
                f"Invalid timestamp column: {timestamp_column}"
            ) from e

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
