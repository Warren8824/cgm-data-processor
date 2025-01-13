"""Abstract base for data aligners with automatic aligner selection."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Type

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


class BaseAligner(ABC):
    """Abstract base class for all data aligners."""

    _aligners: Dict[DataType, Type["BaseAligner"]] = {}

    @classmethod
    def register(cls, reference_type: DataType):
        """Register an aligner class for a specific reference type."""

        def wrapper(aligner_cls):
            cls._aligners[reference_type] = aligner_cls
            return wrapper

        return wrapper

    @classmethod
    def get_aligner_for_type(cls, reference_type: DataType) -> "BaseAligner":
        """Get appropriate aligner instance for the reference type."""
        aligner_cls = cls._aligners.get(reference_type)
        if aligner_cls is None:
            raise AlignmentError(
                f"No aligner registered for reference type: {reference_type.value}"
            )
        return aligner_cls()

    def _validate_reference(self, reference_data: pd.DataFrame, freq: str) -> None:
        """Validate reference data structure and frequency."""
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

    @abstractmethod
    def align_dataframe(
        self,
        df: pd.DataFrame,
        data_type: DataType,
        reference_index: pd.DatetimeIndex,
        freq: str,
    ) -> pd.DataFrame:
        """Align a single DataFrame to the reference timeline."""

    def align(
        self,
        data: Dict[DataType, ProcessedTypeData],
        reference_type: DataType,
        freq: str = "5min",
    ) -> AlignmentResult:
        """Align all data to a reference timeline."""
        # Get and validate reference data
        reference_data = data.get(reference_type)
        if not reference_data or reference_data.dataframe.empty:
            raise AlignmentError(
                f"No {reference_type.name} data available for alignment"
            )

        # Validate reference data structure and frequency
        self._validate_reference(reference_data.dataframe, freq)

        # Create list to track processing notes
        processing_notes = []
        aligned_dfs = []

        # Align each data type
        for data_type, processed_data in data.items():
            try:
                aligned_df = self.align_dataframe(
                    processed_data.dataframe,
                    data_type,
                    reference_data.dataframe.index,
                    freq,
                )
                aligned_dfs.append(aligned_df)
                processing_notes.append(f"Successfully aligned {data_type.name} data")
            except AlignmentError as e:
                logger.error("Error aligning %s: %s", data_type.name, str(e))
                processing_notes.append(
                    "Failed to align %s: %s", data_type.name, str(e)
                )

        # Combine all aligned data
        combined_df = pd.concat(aligned_dfs, axis=1)

        return AlignmentResult(
            dataframe=combined_df,
            start_time=combined_df.index[0],
            end_time=combined_df.index[-1],
            frequency=freq,
            processing_notes=processing_notes,
        )
