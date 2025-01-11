"""Abstract base for data processors.

This module defines the base processor class and common functionality for processing
different types of diabetes data (CGM, insulin, carbs, etc.). It provides:
    - Abstract interface for specific data type processors
    - Common validation and processing methods
    - Standardized data quality checks
    - Processing status tracking and reporting
    - Time series handling utilities
    - Unit conversion support
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Union

import pandas as pd

from src.core.data_types import DataType, Unit
from src.core.exceptions import (
    DataProcessingError,
    DataValidationError,
    UnitConversionError,
)

logger = logging.getLogger(__name__)


@dataclass
class ProcessingMetadata:
    """Metadata about the processing operation."""

    data_type: DataType
    original_rows: int
    processed_rows: int
    dropped_rows: Dict[str, int]  # Reason: count
    quality_metrics: Dict[str, float]
    warnings: List[str]
    source_units: Optional[Unit] = None
    target_units: Optional[Unit] = None

    # Time series specific metrics
    time_range: Optional[Tuple[pd.Timestamp, pd.Timestamp]] = None
    gap_statistics: Optional[Dict[str, Union[int, float]]] = None

    # Classification metrics
    classification_confidence: Optional[Dict[str, float]] = None

    # Processing configuration
    applied_rules: Dict[str, Union[str, int, float]] = None


class BaseProcessor(ABC):
    """Abstract base class for all data type processors."""

    def __init__(
        self,
        data_type: DataType,
        source_unit: Optional[Unit] = None,
        target_unit: Optional[Unit] = None,
    ):
        """Initialize processor for specific data type.

        Args:
            data_type: The type of data this processor handles
            source_unit: Unit of the input data (if applicable)
            target_unit: Desired output unit (if applicable)
        """
        self.data_type = data_type
        self.source_unit = source_unit
        self.target_unit = target_unit
        self._processed_data: Optional[pd.DataFrame] = None
        self._metadata: Optional[ProcessingMetadata] = None
        self._required_columns: Set[str] = set()
        self._optional_columns: Set[str] = set()

        # Initialize required/optional columns
        self._initialize_column_requirements()

    @abstractmethod
    def _initialize_column_requirements(self) -> None:
        """Define required and optional columns for this processor."""
        raise NotImplementedError

    @property
    def processed_data(self) -> Optional[pd.DataFrame]:
        """Get the processed data if available."""
        return self._processed_data

    @property
    def metadata(self) -> Optional[ProcessingMetadata]:
        """Get processing metadata if available."""
        return self._metadata

    def _round_timestamps(
        self, df: pd.DataFrame, freq: str = "5min", handle_duplicates: str = "mean"
    ) -> pd.DataFrame:
        """Round timestamps to specified frequency and handle duplicates.

        Args:
            df: Input DataFrame
            freq: Frequency to round to (default: '5min')
            handle_duplicates: How to handle duplicate timestamps ('mean', 'first', or 'last')

        Returns:
            DataFrame with rounded timestamps
        """
        df = df.copy()
        df.index = df.index.round(freq)

        if handle_duplicates:
            if handle_duplicates == "mean":
                df = df.groupby(level=0).mean()
            else:
                df = df[~df.index.duplicated(keep=handle_duplicates)]

        return df

    def _interpolate_gaps(
        self, df: pd.DataFrame, column: str, max_gap: int, method: str = "linear"
    ) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Interpolate gaps in time series data.

        Args:
            df: Input DataFrame
            column: Column to interpolate
            max_gap: Maximum number of consecutive values to interpolate
            method: Interpolation method

        Returns:
            Tuple of (processed DataFrame, gap statistics)
        """
        df = df.copy()

        # Flag missing values
        df["missing"] = df[column].isna()

        # Create groups of consecutive missing values
        df["gap_group"] = (~df["missing"]).cumsum()

        # Calculate gap statistics
        gap_sizes = df[df["missing"]].groupby("gap_group").size()
        gap_stats = {
            "total_gaps": len(gap_sizes),
            "max_gap_size": gap_sizes.max() if not gap_sizes.empty else 0,
            "mean_gap_size": gap_sizes.mean() if not gap_sizes.empty else 0,
            "interpolated_gaps": len(gap_sizes[gap_sizes <= max_gap]),
            "unfilled_gaps": len(gap_sizes[gap_sizes > max_gap]),
        }

        # Interpolate within limit
        df[column] = df[column].interpolate(
            method=method, limit=max_gap, limit_direction="both"
        )

        return df, gap_stats

    def _validate_range(
        self, series: pd.Series, min_val: float, max_val: float, clip: bool = True
    ) -> Tuple[pd.Series, int]:
        """Validate and optionally clip values to specified range.

        Args:
            series: Input series
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            clip: Whether to clip values to range (True) or drop them (False)

        Returns:
            Tuple of (processed series, number of out-of-range values)
        """
        out_of_range = ((series < min_val) | (series > max_val)).sum()

        if clip:
            series = series.clip(lower=min_val, upper=max_val)
        else:
            series = series[(series >= min_val) & (series <= max_val)]

        return series, out_of_range

    def _convert_units(
        self,
        series: pd.Series,
        from_unit: Unit,
        to_unit: Unit,
        conversion_factor: float,
    ) -> pd.Series:
        """Convert values between units.

        Args:
            series: Input series
            from_unit: Source unit
            to_unit: Target unit
            conversion_factor: Multiplication factor for conversion

        Returns:
            Series with converted values

        Raises:
            UnitConversionError: If units are incompatible
        """
        if from_unit == to_unit:
            return series

        try:
            return series * conversion_factor
        except Exception as e:
            raise UnitConversionError(
                f"Error converting from {from_unit.value} to {to_unit.value}"
            ) from e

    def validate_input(self, df: pd.DataFrame) -> None:
        """Validate input data meets minimum requirements."""
        # Check required columns exist
        missing_required = self._required_columns - set(df.columns)
        if missing_required:
            raise DataValidationError(
                f"Missing required columns for {self.data_type.name}",
                details={"missing_columns": list(missing_required)},
            )

        # Ensure DataFrame is time-indexed
        if not isinstance(df.index, pd.DatetimeIndex):
            raise DataValidationError(
                f"Input data for {self.data_type.name} must have DatetimeIndex"
            )

        # Check index is UTC
        if df.index.tz is None or str(df.index.tz) != "UTC":
            raise DataValidationError(
                f"Input data for {self.data_type.name} must have UTC timezone"
            )

        # Validate units if specified
        if self.source_unit and "unit" in df.columns:
            invalid_units = df["unit"] != self.source_unit.value
            if invalid_units.any():
                raise DataValidationError(
                    f"Invalid units found. Expected {self.source_unit.value}"
                )

    def _initialize_metadata(self, df: pd.DataFrame) -> None:
        """Initialize processing metadata."""
        self._metadata = ProcessingMetadata(
            data_type=self.data_type,
            original_rows=len(df),
            processed_rows=0,
            dropped_rows={},
            quality_metrics={},
            warnings=[],
            source_units=self.source_unit,
            target_units=self.target_unit,
            time_range=(df.index.min(), df.index.max()),
            gap_statistics={},
            classification_confidence={},
            applied_rules={},
        )

    @abstractmethod
    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process the input data according to processor rules."""
        raise NotImplementedError

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run the complete processing pipeline."""
        try:
            # Validate input
            self.validate_input(df)

            # Initialize metadata
            self._initialize_metadata(df)

            # Run processing
            self._processed_data = self.process(df)

            # Final validation
            if self._processed_data is None:
                raise DataProcessingError(
                    f"Processing {self.data_type.name} produced no output"
                )

            return self._processed_data

        except Exception as e:
            logger.error("Error processing %s data: %s", self.data_type.name, str(e))
            raise

    def get_processing_summary(self) -> str:
        """Get a human-readable summary of the processing results."""
        if self._metadata is None:
            return "No processing metadata available"

        summary = [
            f"\nProcessing Summary for {self._metadata.data_type.name}:",
            f"Original rows: {self._metadata.original_rows}",
            f"Processed rows: {self._metadata.processed_rows}",
            f"\nTime range: {self._metadata.time_range[0]} to {self._metadata.time_range[1]}",
        ]

        if self._metadata.gap_statistics:
            summary.append("\nGap Statistics:")
            for metric, value in self._metadata.gap_statistics.items():
                summary.append(f"  - {metric}: {value}")

        if self._metadata.classification_confidence:
            summary.append("\nClassification Confidence:")
            for (
                category,
                confidence,
            ) in self._metadata.classification_confidence.items():
                summary.append(f"  - {category}: {confidence:.2%}")

        if self._metadata.dropped_rows:
            summary.append("\nDropped rows:")
            for reason, count in self._metadata.dropped_rows.items():
                summary.append(f"  - {reason}: {count}")

        if self._metadata.quality_metrics:
            summary.append("\nQuality metrics:")
            for metric, value in self._metadata.quality_metrics.items():
                summary.append(f"  - {metric}: {value:.2f}")

        if self._metadata.warnings:
            summary.append("\nWarnings:")
            for warning in self._metadata.warnings:
                summary.append(f"  - {warning}")

        return "\n".join(summary)
