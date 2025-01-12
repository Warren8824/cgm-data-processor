"""Processor for Continuous Glucose Monitor (CGM) data."""

import logging
from typing import List

import numpy as np
import pandas as pd

from src.core.data_types import DataType, Unit
from src.core.exceptions import ProcessingError

from .base import BaseTypeProcessor, ColumnData, DataProcessor, ProcessedTypeData

logger = logging.getLogger(__name__)


@DataProcessor.register_processor(DataType.CGM)
class CGMProcessor(BaseTypeProcessor):
    """Processes CGM data with validation and cleaning."""

    def process_type(
        self,
        columns: List[ColumnData],
        interpolation_limit: int = 4,
    ) -> ProcessedTypeData:
        """Process all CGM data from various sources.

        Args:
            columns: List of ColumnData containing all CGM data columns
            interpolation_limit: Maximum number of consecutive missing values to interpolate
                               (default: 4, equivalent to 20 minutes at 5-min intervals)

        Returns:
            ProcessedTypeData containing combined and cleaned CGM data
        """
        processing_notes = []

        try:
            # Validate we have at least one primary column
            if not any(col.is_primary for col in columns):
                raise ProcessingError("No primary CGM column found")

            # Sort columns to ensure primary is first
            sorted_columns = sorted(columns, key=lambda x: (not x.is_primary))

            # Create initial dataframe
            combined_df = pd.DataFrame(index=pd.DatetimeIndex([]))
            column_units = {}

            # First pass - combine all data and convert units
            for idx, col_data in enumerate(sorted_columns):
                # Convert to mg/dL if needed
                df = col_data.dataframe.copy()
                if col_data.unit == Unit.MMOL:
                    df["value"] = df["value"] * 18.0182
                    processing_notes.append(
                        f"Converted CGM column {idx + 1} from {Unit.MMOL.value} to {Unit.MGDL.value}"
                    )

                # Generate column name
                new_name = self._generate_column_name(
                    DataType.CGM, col_data.is_primary, idx
                )
                df.columns = [new_name]

                # Merge with existing data
                if combined_df.empty:
                    combined_df = df
                else:
                    combined_df = combined_df.join(df, how="outer")

                column_units[new_name] = col_data.unit

            # Round all timestamps to nearest 5 minute interval
            combined_df.index = combined_df.index.round("5min")

            # Handle duplicate times by taking mean
            combined_df = combined_df.groupby(level=0).mean()

            # Create complete 5-minute interval index
            full_index = pd.date_range(
                start=combined_df.index.min(), end=combined_df.index.max(), freq="5min"
            )

            # Reindex to include all intervals
            combined_df = combined_df.reindex(full_index)

            # Get primary column name
            primary_col = next(col for col in combined_df.columns if "primary" in col)

            # Create missing flags for each column
            missing_flags = pd.DataFrame(index=combined_df.index)
            missing_flags["missing"] = combined_df[primary_col].isna()

            # Handle interpolation for each column
            for col in combined_df.columns:
                # Create groups of consecutive missing values
                gap_groups = (~combined_df[col].isna()).cumsum()

                # Within each False group (where missing=True), count the group size
                gap_size = (
                    combined_df[combined_df[col].isna()].groupby(gap_groups).size()
                )

                # Identify gap groups that are larger than interpolation_limit
                large_gaps = gap_size[gap_size > interpolation_limit].index

                # Interpolate all gaps initially
                combined_df[col] = combined_df[col].interpolate(
                    method="linear",
                    limit=interpolation_limit,
                    limit_direction="forward",
                )

                # Reset interpolated values back to NaN for large gaps
                for gap_group in large_gaps:
                    mask = (gap_groups == gap_group) & combined_df[col].isna()
                    combined_df.loc[mask, col] = np.nan

                # Clip values to valid range
                combined_df[col] = combined_df[col].clip(lower=39.64, upper=360.36)

            # Create mmol/L columns for each mg/dL column
            for col in combined_df.columns.copy():
                mmol_col = f"{col}_mmol"
                combined_df[mmol_col] = combined_df[col] * 0.0555
                column_units[mmol_col] = Unit.MMOL
                column_units[col] = Unit.MGDL

            # Add the missing flags
            combined_df["missing"] = missing_flags["missing"]

            # Track stats about the processed data
            total_readings = len(combined_df)
            missing_primary = combined_df["missing"].sum()
            processing_notes.extend(
                [
                    f"Processed {total_readings} total CGM readings",
                    f"Found {missing_primary} missing or interpolated values in primary data",
                ]
            )

            return ProcessedTypeData(
                dataframe=combined_df,
                source_units=column_units,
                processing_notes=processing_notes,
            )

        except Exception as e:
            raise ProcessingError(f"Error processing CGM data: {str(e)}") from e
