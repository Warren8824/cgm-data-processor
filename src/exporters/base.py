"""Base interface for data exporters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd

from src.core.aligner import AlignmentResult
from src.core.data_types import DataType
from src.processors.base import ProcessedTypeData


@dataclass
class ExportConfig:
    """Configuration for data export."""

    output_dir: Path
    split_by_month: bool = True
    include_processing_notes: bool = True
    date_in_filename: bool = True


class BaseExporter(ABC):
    """Abstract base class for data exporters."""

    def __init__(self, config: ExportConfig):
        self.config = config
        self._ensure_directories()
        self.monthly_notes_cache = {}

    def _ensure_directories(self) -> None:
        """Create necessary directory structure."""
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        if self.config.split_by_month:
            (self.config.output_dir / "monthly").mkdir(exist_ok=True)
        (self.config.output_dir / "complete").mkdir(exist_ok=True)

    @abstractmethod
    def export_complete_dataset(
        self, data: ProcessedTypeData, data_type: DataType, output_dir: Path
    ) -> None:
        """Export complete dataset for a specific data type."""

    @abstractmethod
    def export_monthly_split(
        self, data: ProcessedTypeData, data_type: DataType, month_dir: Path
    ) -> None:
        """Export monthly split for a specific data type."""

    @abstractmethod
    def export_processing_notes(
        self, data: Union[ProcessedTypeData, AlignmentResult], output_path: Path
    ) -> None:
        """Export processing notes."""

    @abstractmethod
    def export_aligned_complete_dataset(
        self, data: AlignmentResult, output_dir: Path
    ) -> None:
        """Export complete aligned dataset."""

    @abstractmethod
    def export_aligned_monthly_split(
        self, data: AlignmentResult, month_dir: Path
    ) -> None:
        """Export monthly split for aligned data."""

    def _generate_type_stats(
        self, data: pd.DataFrame, data_type: Optional[DataType] = None
    ) -> List[str]:
        """Generate statistics for a specific data type."""
        stats = []

        if data_type == DataType.CGM or "cgm_primary" in data.columns:
            missing_count = data.get("missing_cgm", data.get("missing", 0)).sum()
            stats.extend(
                [
                    "CGM Processing Notes:",
                    f"  Processed {len(data)} total CGM readings",
                    f"  Found {missing_count} missing or interpolated values",
                ]
            )

        if data_type == DataType.INSULIN or "basal_dose" in data.columns:
            if data_type == DataType.INSULIN:
                basal_count = data["is_basal"].sum()
                bolus_count = data["is_bolus"].sum()
            else:
                basal_count = (data["basal_dose"] > 0).sum()
                bolus_count = (data["bolus_dose"] > 0).sum()
            stats.extend(
                [
                    "INSULIN Processing Notes:",
                    f"  Found {basal_count + bolus_count} total doses",
                    f"  {basal_count} basal doses",
                    f"  {bolus_count} bolus doses",
                ]
            )

        if data_type == DataType.CARBS or "carbs_primary" in data.columns:
            carb_entries = (
                (data["carbs_primary"] > 0).sum()
                if "carbs_primary" in data.columns
                else (data > 0).sum()
            )
            stats.extend(
                ["CARBS Processing Notes:", f"  Found {carb_entries} carb entries"]
            )

        if data_type == DataType.NOTES or "notes_primary" in data.columns:
            note_count = (
                data["notes_primary"].notna().sum()
                if "notes_primary" in data.columns
                else data.notna().sum()
            )
            stats.extend(
                ["NOTES Processing Notes:", f"  Found {note_count} notes entries"]
            )

        return stats

    def _accumulate_monthly_stats(
        self, month_str: str, group: pd.DataFrame, data_type: DataType
    ) -> None:
        """Accumulate statistics for a month across all data types."""
        if month_str not in self.monthly_notes_cache:
            self.monthly_notes_cache[month_str] = {
                "period": month_str,
                "record_count": len(group),
                "stats": [],
            }

        type_stats = self._generate_type_stats(group, data_type)
        if type_stats:
            self.monthly_notes_cache[month_str]["stats"].extend(type_stats)

    def _handle_monthly_exports(
        self, data: ProcessedTypeData, data_type: DataType
    ) -> None:
        """Handle monthly data splits and exports."""
        monthly_base = self.config.output_dir / "monthly"

        for timestamp, group in data.dataframe.groupby(pd.Grouper(freq="ME")):
            if not group.empty:
                month_str = pd.Timestamp(timestamp).strftime("%Y-%m")
                month_dir = monthly_base / month_str
                month_dir.mkdir(parents=True, exist_ok=True)

                self._accumulate_monthly_stats(month_str, group, data_type)

                monthly_notes = [
                    f"Period: {month_str}",
                    f"Records: {len(group)}",
                    f"Columns present: {', '.join(group.columns)}",
                    *self.monthly_notes_cache[month_str]["stats"],
                ]

                monthly_data = ProcessedTypeData(
                    dataframe=group,
                    source_units=data.source_units,
                    processing_notes=monthly_notes,
                )

                if self.config.include_processing_notes:
                    self.export_processing_notes(monthly_data, month_dir)
                self.export_monthly_split(monthly_data, data_type, month_dir)

    def _handle_monthly_aligned_exports(self, data: AlignmentResult) -> None:
        """Handle monthly splits for aligned data."""
        monthly_base = self.config.output_dir / "monthly"

        for timestamp, group in data.dataframe.groupby(pd.Grouper(freq="ME")):
            if not group.empty:
                month_str = pd.Timestamp(timestamp).strftime("%Y-%m")
                month_dir = monthly_base / month_str
                month_dir.mkdir(parents=True, exist_ok=True)

                monthly_notes = [
                    f"Period: {month_str}",
                    f"Records: {len(group)}",
                    f"Columns present: {', '.join(group.columns)}",
                    *self._generate_type_stats(group),
                ]

                monthly_aligned = AlignmentResult(
                    dataframe=group,
                    start_time=group.index.min(),
                    end_time=group.index.max(),
                    frequency=data.frequency,
                    processing_notes=monthly_notes,
                    source_units=data.source_units,
                )

                self.export_aligned_monthly_split(monthly_aligned, month_dir)

    def export_data(
        self,
        processed_data: Dict[DataType, ProcessedTypeData],
        aligned_data: Optional[AlignmentResult] = None,
    ) -> None:
        """Export all processed data and aligned data if available."""
        if not processed_data and not aligned_data:
            return

        # Reset monthly notes cache
        self.monthly_notes_cache = {}

        # Get date range from either source
        date_range = self.get_date_range(
            next(iter(processed_data.values())) if processed_data else aligned_data
        )
        complete_dir = self.config.output_dir / "complete" / date_range
        complete_dir.mkdir(parents=True, exist_ok=True)

        # Export individual datasets
        for data_type, type_data in processed_data.items():
            self.export_complete_dataset(type_data, data_type, complete_dir)
            if self.config.split_by_month:
                self._handle_monthly_exports(type_data, data_type)

        # Export aligned data if available
        if aligned_data:
            self._export_aligned_data(aligned_data, complete_dir)
            if self.config.split_by_month:
                self._handle_monthly_aligned_exports(aligned_data)

    def _export_aligned_data(
        self, aligned_data: AlignmentResult, output_dir: Path
    ) -> None:
        """Export aligned dataset."""
        self.export_aligned_complete_dataset(aligned_data, output_dir)
        if self.config.include_processing_notes:
            self.export_processing_notes(aligned_data, output_dir)

    @staticmethod
    def get_date_range(data: Union[ProcessedTypeData, AlignmentResult]) -> str:
        """Get date range string from data."""
        df = data.dataframe
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")
        start = df.index.min().strftime("%Y-%m-%d")
        end = df.index.max().strftime("%Y-%m-%d")
        return f"{start}_to_{end}"
