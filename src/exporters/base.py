"""Base interface for data exporters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import pandas as pd

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
        self, data: ProcessedTypeData, output_path: Path
    ) -> None:
        """Export processing notes."""

    @staticmethod
    def get_date_range(data: ProcessedTypeData) -> str:
        """Get date range string from data."""
        df = data.dataframe
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")
        start = df.index.min().strftime("%Y-%m-%d")
        end = df.index.max().strftime("%Y-%m-%d")
        return f"{start}_to_{end}"

    def export_data(self, processed_data: Dict[DataType, ProcessedTypeData]) -> None:
        """Export all processed data."""
        if not processed_data:
            return

        date_range = self.get_date_range(next(iter(processed_data.values())))
        complete_dir = self.config.output_dir / "complete" / date_range
        complete_dir.mkdir(parents=True, exist_ok=True)

        for data_type, type_data in processed_data.items():
            # Export complete dataset
            self.export_complete_dataset(type_data, data_type, complete_dir)

            # Export monthly splits if configured
            if self.config.split_by_month:
                self._handle_monthly_exports(type_data, data_type)

    def _handle_monthly_exports(
        self, data: ProcessedTypeData, data_type: DataType
    ) -> None:
        """Handle monthly data splits and exports."""
        monthly_base = self.config.output_dir / "monthly"

        for timestamp, group in data.dataframe.groupby(pd.Grouper(freq="M")):
            if not group.empty:
                # Convert Timestamp to string format
                month_str = pd.Timestamp(timestamp).strftime("%Y-%m")
                month_dir = monthly_base / month_str
                month_dir.mkdir(parents=True, exist_ok=True)

                monthly_data = ProcessedTypeData(
                    dataframe=group,
                    source_units=data.source_units,
                    processing_notes=data.processing_notes,
                )

                self.export_monthly_split(monthly_data, data_type, month_dir)
