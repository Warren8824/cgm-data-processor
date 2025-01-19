"""Aligner for diabetes data.

This module provides functionality to align different types of diabetes data to a
reference timeline, defaulting to CGM readings but supporting other reference types.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from src.core.data_types import DataType
from src.core.exceptions import AlignmentError
from src.processors.base import ProcessedTypeData

logger = logging.getLogger(__name__)


@dataclass
class AlignmentResult:
    """Results of the alignment process."""

    dataframe: pd.DataFrame  # The aligned timeseries data
    start_time: pd.Timestamp  # Start of aligned timeline
    end_time: pd.Timestamp  # End of aligned timeline
    frequency: str  # Alignment frequency
    processing_notes: List[str]  # Notes about the alignment process


class Aligner:
    """Aligns diabetes data to a reference timeline."""

    def _validate_timeline(self, reference_data: pd.DataFrame, freq: str) -> None:
        """Validate that reference data provides a valid timeline."""
        if reference_data.empty:
            raise AlignmentError("Reference data is empty")

        if not isinstance(reference_data.index, pd.DatetimeIndex):
            raise AlignmentError("Reference data must have DatetimeIndex")

        if not reference_data.index.is_monotonic_increasing:
            raise AlignmentError(
                "Reference data index must be monotonically increasing"
            )

        # Check if the data mostly follows the expected frequency
        time_diffs = reference_data.index.to_series().diff()
        modal_diff = time_diffs.mode()[0]
        expected_diff = pd.Timedelta(freq)

        if modal_diff != expected_diff:
            raise AlignmentError(
                f"Reference data frequency {modal_diff} does not match expected {freq}"
            )

    def _align_insulin(
        self, df: pd.DataFrame, reference_index: pd.DatetimeIndex, freq: str
    ) -> pd.DataFrame:
        """Align insulin data."""
        df = df.copy()
        df.index = df.index.round(freq)

        # Split and sum basal/bolus doses separately
        basal_doses = df["dose"].where(df["is_basal"], 0)
        bolus_doses = df["dose"].where(df["is_bolus"], 0)

        # Resample each type
        result = pd.DataFrame(
            {
                "basal_dose": basal_doses.resample(freq).sum(),
                "bolus_dose": bolus_doses.resample(freq).sum(),
            }
        )

        return result.reindex(reference_index).fillna(0)

    def _align_carbs(
        self, df: pd.DataFrame, reference_index: pd.DatetimeIndex, freq: str
    ) -> pd.DataFrame:
        """Align carbohydrate data."""
        df = df.copy()
        df.index = df.index.round(freq)

        result = df["carbs_primary"].resample(freq).sum()
        return (
            pd.DataFrame({"carbs_primary": result}).reindex(reference_index).fillna(0)
        )

    def _align_notes(
        self, df: pd.DataFrame, reference_index: pd.DatetimeIndex, freq: str
    ) -> pd.DataFrame:
        """Align notes data."""
        df = df.copy()
        df.index = df.index.round(freq)

        result = df["notes_primary"].resample(freq).last()
        return pd.DataFrame({"notes_primary": result}).reindex(reference_index)

    def align(
        self,
        processed_data: Dict[DataType, ProcessedTypeData],
        reference_df: pd.DataFrame = None,
        freq: str = "5min",
    ) -> AlignmentResult:
        """Align all data to a reference timeline.

        Args:
            processed_data: Dictionary of processed data by DataType
            reference_df: DataFrame to use as reference timeline. If None, uses CGM data.
            freq: Expected frequency of data

        Returns:
            AlignmentResult containing aligned data and metadata
        """
        # Get reference DataFrame (default to CGM if not specified)
        if reference_df is None:
            cgm_data = processed_data.get(DataType.CGM)
            if not cgm_data or cgm_data.dataframe.empty:
                raise AlignmentError("No CGM data available for alignment")
            reference_df = cgm_data.dataframe

        # Validate timeline
        self._validate_timeline(reference_df, freq)
        reference_index = reference_df.index

        # Track alignment process
        processing_notes = []
        aligned_dfs = []

        # Change 'missing' column to clearer name for combined data
        reference_df.rename(columns={"missing": "missing_cgm"}, inplace=True)

        # Always include reference data first
        aligned_dfs.append(reference_df)
        processing_notes.append("Reference timeline established")

        # Define alignment methods for each data type
        type_methods = {
            DataType.INSULIN: self._align_insulin,
            DataType.CARBS: self._align_carbs,
            DataType.NOTES: self._align_notes,
        }

        # Align other available data
        for data_type, processed in processed_data.items():
            if processed.dataframe is not reference_df:  # Skip reference data
                try:
                    align_method = type_methods.get(data_type)
                    if align_method:
                        aligned_df = align_method(
                            processed.dataframe, reference_index, freq
                        )
                        aligned_dfs.append(aligned_df)
                        processing_notes.append(
                            f"Successfully aligned {data_type.name} data"
                        )
                except AlignmentError as e:
                    logger.error("Error aligning %s: %s", data_type.name, str(e))
                    processing_notes.append(
                        f"Failed to align {data_type.name}: {str(e)}"
                    )

        # Combine all aligned data
        combined_df = pd.concat(aligned_dfs, axis=1)

        return AlignmentResult(
            dataframe=combined_df,
            start_time=reference_index[0],
            end_time=reference_index[-1],
            frequency=freq,
            processing_notes=processing_notes,
        )
