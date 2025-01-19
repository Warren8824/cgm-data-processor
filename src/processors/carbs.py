"""Processor for carbohydrate intake data."""

import logging
from typing import List

from src.core.data_types import DataType
from src.core.exceptions import ProcessingError
from src.processors.base import (
    BaseTypeProcessor,
    ColumnData,
    DataProcessor,
    ProcessedTypeData,
)

logger = logging.getLogger(__name__)


@DataProcessor.register_processor(DataType.CARBS)
class CarbsProcessor(BaseTypeProcessor):
    """Processes carbohydrate intake data with validation and cleaning."""

    def process_type(
        self,
        columns: List[ColumnData],
    ) -> ProcessedTypeData:
        """Process all carbohydrate data from various sources.

        Args:
            columns: List of ColumnData containing all carb data columns

        Returns:
            ProcessedTypeData containing combined and cleaned carb data
        """
        processing_notes = []

        try:
            # Validate we have at least one primary column
            if not any(col.is_primary for col in columns):
                raise ProcessingError("No primary carbohydrate column found")

            # Sort columns to ensure primary is first
            sorted_columns = sorted(columns, key=lambda x: (not x.is_primary))

            # Combine all columns with standardized names
            combined_df, column_units = self._combine_and_rename_columns(
                sorted_columns, DataType.CARBS
            )

            if combined_df.empty:
                raise ProcessingError("No carbohydrate data to process")

            # Log what we're processing
            processing_notes.append(
                f"Processing {len(combined_df.columns)} carb columns: {', '.join(combined_df.columns)}"
            )

            # Track original row count
            original_count = len(combined_df)

            # Process each carb column
            for col in combined_df.columns:
                # Keep only rows where carbs is >= 1.0 grams
                mask = combined_df[col] >= 1.0
                combined_df.loc[~mask, col] = None

                filtered_count = mask.sum()
                processing_notes.append(
                    f"Column {col}: Kept {filtered_count} entries ≥1g "
                    f"({filtered_count / original_count * 100:.1f}%)"
                )

            # Drop rows where all values are null (no significant carbs in any column)
            combined_df = combined_df.dropna(how="all")

            # Handle duplicate timestamps by keeping the first occurrence
            duplicates = combined_df.index.duplicated()
            if duplicates.any():
                dup_count = duplicates.sum()
                processing_notes.append(f"Removed {dup_count} duplicate timestamps")
                combined_df = combined_df[~duplicates]

            # Final stats
            processing_notes.append(
                f"Final dataset contains {len(combined_df)} entries "
                f"from {original_count} original records"
            )

            return ProcessedTypeData(
                dataframe=combined_df,
                source_units=column_units,
                processing_notes=processing_notes,
            )

        except Exception as e:
            raise ProcessingError(
                f"Error processing carbohydrate data: {str(e)}"
            ) from e
