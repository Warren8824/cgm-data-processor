"""Processor for insulin dose data with metadata classification."""

import json
import logging
from typing import List, Optional, Tuple

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


@DataProcessor.register_processor(DataType.INSULIN)
class InsulinProcessor(BaseTypeProcessor):
    """Processes insulin dose data with classification from meta data if available."""

    def _extract_meta_info(self, meta_value: str) -> Tuple[bool, bool, Optional[str]]:
        """Extract insulin type information from meta JSON.

        Returns:
            Tuple of (is_bolus, is_basal, insulin_type)
        """
        try:
            meta_data = json.loads(meta_value)
            if meta_data and isinstance(meta_data, list):
                insulin = meta_data[0].get("insulin", "").lower()
                if "novorapid" in insulin:
                    return True, False, "novorapid"
                if "levemir" in insulin:
                    return False, True, "levemir"
        except (json.JSONDecodeError, IndexError, KeyError, AttributeError):
            pass

        return False, False, None

    def process_type(
        self,
        columns: List[ColumnData],
        bolus_limit: float = 8.0,
        max_limit: float = 15.0,
    ) -> ProcessedTypeData:
        """Process insulin data and classify doses.

        Args:
            columns: List of ColumnData containing insulin data and metadata
            bolus_limit: Maximum insulin units to classify as bolus
            max_limit: Maximum valid insulin dose
        """
        processing_notes = []

        try:
            # Find insulin dose and meta columns
            dose_cols = [col for col in columns if col.data_type == DataType.INSULIN]
            meta_cols = [
                col for col in columns if col.data_type == DataType.INSULIN_META
            ]

            if not any(col.is_primary for col in dose_cols):
                raise ProcessingError("No primary insulin dose column found")

            # Initialize result DataFrame with dose data
            result_df = pd.DataFrame()
            result_units = {}

            # Process dose data first
            for col in dose_cols:
                df = col.dataframe.copy()

                # Keep only positive doses
                valid_mask = df["value"] > 0.0
                df = df[valid_mask]

                if len(df) > 0:
                    processing_notes.append(f"Found {len(df)} positive doses")

                    # Add dose column
                    result_df["dose"] = df["value"]
                    result_units["dose"] = col.unit

                    # Initial classification based on dose
                    result_df["is_bolus"] = df["value"] <= bolus_limit
                    result_df["is_basal"] = (df["value"] > bolus_limit) & (
                        df["value"] <= max_limit
                    )
                    result_df["type"] = ""  # Will be filled by metadata if available

                    # Track classification stats
                    processing_notes.extend(
                        [
                            "Initial dose-based classification:",
                            f"- {result_df['is_bolus'].sum()} doses classified as bolus (≤{bolus_limit}U)",
                            f"- {result_df['is_basal'].sum()} doses classified as basal (>{bolus_limit}U)",
                            f"- Dropped {(df['value'] > max_limit).sum()} doses exceeding {max_limit}U",
                        ]
                    )

            # Update classification with metadata if available
            if meta_cols and not result_df.empty:
                meta_updates = 0
                for col in meta_cols:
                    for idx, meta_value in col.dataframe["value"].items():
                        if idx in result_df.index:
                            is_bolus, is_basal, insulin_type = self._extract_meta_info(
                                meta_value
                            )
                            if insulin_type:
                                result_df.loc[idx, "is_bolus"] = is_bolus
                                result_df.loc[idx, "is_basal"] = is_basal
                                result_df.loc[idx, "type"] = insulin_type
                                meta_updates += 1

                if meta_updates > 0:
                    processing_notes.append(
                        f"Updated {meta_updates} classifications using metadata"
                    )

            # Final stats
            processing_notes.append(
                f"Final dataset contains {len(result_df)} insulin records"
            )

            return ProcessedTypeData(
                dataframe=result_df,
                source_units=result_units,
                processing_notes=processing_notes,
            )

        except Exception as e:
            raise ProcessingError(f"Error processing insulin data: {str(e)}") from e
