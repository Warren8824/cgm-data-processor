"""Processor for Blood Glucose Meter (BGM) data."""

import logging
from typing import List

import pandas as pd

from src.core.data_types import DataType, Unit
from src.core.exceptions import ProcessingError
from src.processors.base import (
    BaseTypeProcessor,
    ColumnData,
    DataProcessor,
    ProcessedTypeData,
)

logger = logging.getLogger(__name__)


@DataProcessor.register_processor(DataType.BGM)
class BGMProcessor(BaseTypeProcessor):
    """Processes BGM data with validation and cleaning."""

    def process_type(
        self,
        columns: List[ColumnData],
    ) -> ProcessedTypeData:
        """Process all BGM data from various sources.

        Args:
            columns: List of ColumnData containing all BGM data columns

        Returns:
            ProcessedTypeData containing combined and cleaned BGM data
        """
        processing_notes = []

        try:
            # Validate we have at least one primary column
            if not any(col.is_primary for col in columns):
                raise ProcessingError("No primary BGM column found")

            # Create initial dataframe
            combined_df = pd.DataFrame(index=pd.DatetimeIndex([]))
            column_units = {}

            # First pass - combine all data and convert units
            for idx, col_data in enumerate(
                sorted(columns, key=lambda x: (not x.is_primary))
            ):
                # Convert to mg/dL if needed
                df = col_data.dataframe.copy()

                # Filter out invalid/zero values before unit conversion
                valid_mask = df["value"] > 0.0
                invalid_count = (~valid_mask).sum()
                if invalid_count > 0:
                    processing_notes.append(
                        f"Removed {invalid_count} invalid/zero values from column {idx + 1}"
                    )
                df = df[valid_mask]

                if col_data.unit == Unit.MMOL:
                    df["value"] = df["value"] * 18.0182
                    processing_notes.append(
                        f"Converted BGM column {idx + 1} from {Unit.MMOL.value} to {Unit.MGDL.value}"
                    )

                # Generate column name
                new_name = self._generate_column_name(
                    DataType.BGM, col_data.is_primary, idx
                )
                df.columns = [new_name]

                # Add clipped flag column before any clipping occurs
                clipped_name = f"{new_name}_clipped"
                df[clipped_name] = False

                # Identify values outside valid range
                below_range = df[new_name] < 39.64
                above_range = df[new_name] > 360.36

                # Update clipped flags
                df.loc[below_range | above_range, clipped_name] = True

                # Clip values to valid range
                df[new_name] = df[new_name].clip(lower=39.64, upper=360.36)

                # Log clipping statistics
                clipped_count = (below_range | above_range).sum()
                if clipped_count > 0:
                    processing_notes.append(
                        f"Clipped {clipped_count} values in column {new_name} "
                        f"({below_range.sum()} below range, {above_range.sum()} above range)"
                    )

                # Merge with existing data
                if combined_df.empty:
                    combined_df = df
                else:
                    combined_df = combined_df.join(df, how="outer")

                column_units[new_name] = Unit.MGDL

            # Handle duplicate timestamps by keeping the last value
            duplicates = combined_df.index.duplicated(keep="last")
            if duplicates.any():
                dup_count = duplicates.sum()
                processing_notes.append(
                    f"Found {dup_count} duplicate timestamps - keeping last values"
                )
                combined_df = combined_df[~duplicates]

            # Create mmol/L columns for each mg/dL column (excluding clipped flag columns)
            value_columns = [
                col for col in combined_df.columns if not col.endswith("_clipped")
            ]
            for col in value_columns:
                mmol_col = f"{col}_mmol"
                combined_df[mmol_col] = combined_df[col] * 0.0555
                column_units[mmol_col] = Unit.MMOL

            # Track stats about the processed data
            total_readings = len(combined_df)
            readings_per_day = (
                total_readings
                / (
                    (combined_df.index.max() - combined_df.index.min()).total_seconds()
                    / 86400
                )
                if total_readings > 0
                else 0
            )

            processing_notes.extend(
                [
                    f"Processed {total_readings} total BGM readings",
                    f"Average of {readings_per_day:.1f} readings per day",
                    f"Date range: {combined_df.index.min()} to {combined_df.index.max()}",
                ]
            )

            return ProcessedTypeData(
                dataframe=combined_df,
                source_units=column_units,
                processing_notes=processing_notes,
            )

        except Exception as e:
            raise ProcessingError(f"Error processing BGM data: {str(e)}") from e
