"""Base interface for data exporters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd

from src.core.aligner import AlignmentResult
from src.core.data_types import DataType
from src.processors.base import ProcessedTypeData


class ColumnCategory(Enum):
    """Categories for organising columns in exports."""

    PRIMARY = auto()  # Primary value columns (e.g., bgm_primary)
    SECONDARY = auto()  # Secondary value columns
    METADATA = auto()  # Metadata columns (e.g., _clipped flags, is_basal)
    UNIT_CONVERT = auto()  # Unit conversion columns (e.g., _mmol)
    TYPE_INFO = auto()  # Type information (e.g., insulin type)
    DERIVED = auto()  # Calculated/derived columns
    OTHER = auto()  # Any other columns


@dataclass
class ExportConfig:
    """Configuration for data export."""

    output_dir: Path = Path("data/exports")  # Default exports directory
    split_by_month: bool = True
    include_processing_notes: bool = True
    date_in_filename: bool = True


class BaseExporter(ABC):
    """Abstract base class for data exporters."""

    def __init__(self, config: ExportConfig):
        self.config = config
        self.monthly_notes_cache = {}
        # Ensure attribute exists so linters don't complain when it's set later
        # This will be set per-run inside export_data()
        self._current_monthly_base = None

    def _generate_type_stats(
        self, data: pd.DataFrame, data_type: Optional[DataType] = None
    ) -> List[str]:
        """Generate statistics for a specific data type."""
        stats = []

        if data_type == DataType.CGM or "cgm_primary" in data.columns:
            missing_count = data.get("missing_cgm", data.get("missing", 0)).sum()
            total_readings = len(data)
            total_na = data["cgm_primary"].isna().sum()
            initial_completeness = (
                (total_readings - missing_count) / total_readings
            ) * 100
            remaining_completeness = (
                (total_readings - total_na) / total_readings
            ) * 100

            stats.extend(
                [
                    "CGM Processing Notes:",
                    f"  Processed {total_readings} total CGM readings",
                    f"  Found {missing_count} missing or interpolated values",
                    f"  Initial CGM completeness: {initial_completeness:.2f}%",
                    f"  CGM completeness after interpolation: {remaining_completeness:.2f}%",
                ]
            )

        if data_type == DataType.BGM or any(
            col.startswith("bgm_") for col in data.columns
        ):
            bgm_cols = [
                col
                for col in data.columns
                if col.startswith("bgm_") and not col.endswith(("_clipped", "_mmol"))
            ]
            for bgm_col in bgm_cols:
                clipped_col = f"{bgm_col}_clipped"
                total_readings = data[bgm_col].notna().sum()

                if clipped_col in data.columns:
                    clipped_readings = data[clipped_col].sum()
                    clipped_percent = (
                        (clipped_readings / total_readings * 100)
                        if total_readings > 0
                        else 0
                    )

                    stats.extend(
                        [
                            f"BGM Processing Notes ({bgm_col}):",
                            f"Processed {total_readings} total BGM readings",
                            f"Found {clipped_readings} clipped values ({clipped_percent:.1f}%)",
                        ]
                    )
                else:
                    stats.extend(
                        [
                            f"BGM Processing Notes ({bgm_col}):",
                            f"Processed {total_readings} total BGM readings",
                        ]
                    )

        if data_type == DataType.INSULIN or any(
            col in data.columns for col in ["dose", "basal_dose", "bolus_dose"]
        ):
            if data_type == DataType.INSULIN:
                basal_count = (
                    data["is_basal"].sum() if "is_basal" in data.columns else 0
                )
                bolus_count = (
                    data["is_bolus"].sum() if "is_bolus" in data.columns else 0
                )
                total_count = len(data)
                stats.extend(
                    [
                        "INSULIN Processing Notes:",
                        f"Found {total_count} total doses",
                        f"{basal_count} basal doses",
                        f"{bolus_count} bolus doses",
                    ]
                )
            else:
                basal_count = (data["basal_dose"] > 0).sum()
                bolus_count = (data["bolus_dose"] > 0).sum()
                stats.extend(
                    [
                        "INSULIN Processing Notes:",
                        f"Found {basal_count + bolus_count} total doses",
                        f"{basal_count} basal doses",
                        f"{bolus_count} bolus doses",
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

    def _handle_monthly_exports(
        self, data: ProcessedTypeData, data_type: DataType
    ) -> None:
        """Handle monthly data splits and exports."""
        # Use per-run monthly base if set (to avoid collisions between runs)
        monthly_base = getattr(self, "_current_monthly_base", None)
        if monthly_base is None:
            monthly_base = self.config.output_dir / "monthly"

        for timestamp, group in data.dataframe.groupby(pd.Grouper(freq="ME")):
            if group.empty:
                continue  # No rows at all — skip

            # ✅ Skip months where all non-index columns are empty, NaN, or zero
            non_empty_cols = group.select_dtypes(include=["number", "object", "bool"])
            if (
                non_empty_cols.isna().all().all()
                or (non_empty_cols.fillna(0) == 0).all().all()
            ):
                continue  # Nothing meaningful — skip export entirely

            month_str = pd.Timestamp(timestamp).strftime("%Y-%m")
            month_dir = monthly_base / month_str
            month_dir.mkdir(parents=True, exist_ok=True)

            # Generate fresh stats just for this month's data
            monthly_stats = [
                f"Period: {month_str}",
                f"Records: {len(group)}",
                *self._generate_type_stats(group, data_type),
            ]

            # Create monthly data with new stats, but keep original source_units
            monthly_data = ProcessedTypeData(
                dataframe=group,
                source_units=data.source_units,
                processing_notes=monthly_stats,  # Only using the fresh monthly stats
            )

            if self.config.include_processing_notes:
                self.export_processing_notes(monthly_data, month_dir)
            self.export_monthly_split(monthly_data, data_type, month_dir)

    def _handle_monthly_aligned_exports(self, data: AlignmentResult) -> None:
        """Handle monthly splits for aligned data."""
        monthly_base = getattr(self, "_current_monthly_base", None)
        if monthly_base is None:
            monthly_base = self.config.output_dir / "monthly"

        for timestamp, group in data.dataframe.groupby(pd.Grouper(freq="ME")):
            if group.empty:
                continue

            # Skip if all data columns are NaN or zero
            non_empty_cols = group.select_dtypes(include=["number", "object", "bool"])
            if (
                non_empty_cols.isna().all().all()
                or (non_empty_cols.fillna(0) == 0).all().all()
            ):
                continue

            month_str = pd.Timestamp(timestamp).strftime("%Y-%m")
            month_dir = monthly_base / month_str
            month_dir.mkdir(parents=True, exist_ok=True)

            monthly_notes = [
                f"Period: {month_str}",
                f"Records: {len(group)}",
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
            if self.config.include_processing_notes:
                self.export_processing_notes(monthly_aligned, month_dir)

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

        # Use a unique complete directory per run to avoid clobbering previous exports
        run_id = datetime.now().strftime("%Y%m%dT%H%M%S")
        complete_dir = self.config.output_dir / f"{date_range}_complete_{run_id}"
        complete_dir.mkdir(parents=True, exist_ok=True)

        # Place monthly exports inside the run's complete directory to keep exports self-contained
        self._current_monthly_base = complete_dir / "monthly"
        self._current_monthly_base.mkdir(parents=True, exist_ok=True)

        # Export individual datasets
        for data_type, type_data in processed_data.items():
            self.export_complete_dataset(type_data, data_type, complete_dir)
            if self.config.include_processing_notes:
                self.export_processing_notes(type_data, complete_dir)
            if self.config.split_by_month:
                self._handle_monthly_exports(type_data, data_type)

        # Export aligned data if available
        if aligned_data:
            self.export_aligned_complete_dataset(aligned_data, complete_dir)
            if self.config.include_processing_notes:
                self.export_processing_notes(aligned_data, complete_dir)
            if self.config.split_by_month:
                self._handle_monthly_aligned_exports(aligned_data)

    @staticmethod
    def get_date_range(data: Union[ProcessedTypeData, AlignmentResult]) -> str:
        """Get date range string from data, for folder name creation."""
        df = data.dataframe
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")
        start = df.index.min().strftime("%Y-%m-%d")
        end = df.index.max().strftime("%Y-%m-%d")
        return f"{start}_to_{end}"
