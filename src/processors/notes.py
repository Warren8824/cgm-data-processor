"""Processor for diabetes-related notes and comments."""

import logging
from typing import List

import pandas as pd

from src.core.data_types import DataType
from src.core.exceptions import ProcessingError
from src.processors.base import (
    BaseTypeProcessor,
    ColumnData,
    DataProcessor,
    ProcessedTypeData,
)

logger = logging.getLogger(__name__)


@DataProcessor.register_processor(DataType.NOTES)
class NotesProcessor(BaseTypeProcessor):
    """Processes text notes/comments data."""

    def process_type(
        self,
        columns: List[ColumnData],
    ) -> ProcessedTypeData:
        """Process notes data ensuring safe string storage.

        Args:
            columns: List of ColumnData containing notes columns

        Returns:
            ProcessedTypeData containing processed notes
        """
        processing_notes = []

        try:
            # Validate we have at least one primary column
            if not any(col.is_primary for col in columns):
                raise ProcessingError("No primary notes column found")

            # Sort columns to ensure primary first
            sorted_columns = sorted(columns, key=lambda x: (not x.is_primary))

            # Initialize result dataframe
            result_df = pd.DataFrame(index=pd.DatetimeIndex([]))

            # Process each column
            for idx, col_data in enumerate(sorted_columns):
                # Generate column name
                col_name = self._generate_column_name(
                    DataType.NOTES, col_data.is_primary, idx
                )

                # Get the notes series
                notes_series = col_data.dataframe["value"]

                # Replace None with pd.NA for better handling
                notes_series = notes_series.replace([None], pd.NA)

                # Convert non-NA values to string and strip whitespace
                notes_series = notes_series.apply(
                    lambda x: x.strip() if pd.notna(x) else pd.NA
                )

                # Remove empty strings
                notes_series = notes_series.replace({"": pd.NA})

                # Add to result DataFrame only if we have any valid notes
                if not notes_series.isna().all():
                    result_df[col_name] = notes_series

                    # Track stats
                    valid_notes = notes_series.notna()
                    processing_notes.append(
                        f"Column {col_name}: found {valid_notes.sum()} valid notes"
                    )

            # Drop rows where all values are NA
            if not result_df.empty:
                result_df = result_df.dropna(how="all")

            processing_notes.append(
                f"Final dataset contains {len(result_df)} notes entries"
            )

            return ProcessedTypeData(
                dataframe=result_df,
                source_units={},  # No units for text data
                processing_notes=processing_notes,
            )

        except Exception as e:
            raise ProcessingError(f"Error processing notes data: {str(e)}") from e
