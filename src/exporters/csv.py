"""CSV exporter implementation."""

import json
from pathlib import Path
from typing import Union

import pandas as pd

from src.core.aligner import AlignmentResult
from src.core.data_types import DataType

from .base import BaseExporter, ExportConfig, ProcessedTypeData


class CSVExporter(BaseExporter):
    """CSV implementation of data exporter."""

    def export_complete_dataset(
        self, data: ProcessedTypeData, data_type: DataType, output_dir: Path
    ) -> None:
        """Export complete dataset as CSV."""
        filename = f"{data_type.name.lower()}.csv"
        data.dataframe.to_csv(output_dir / filename)

        if self.config.include_processing_notes:
            self.export_processing_notes(data, output_dir)

    def export_monthly_split(
        self, data: ProcessedTypeData, data_type: DataType, month_dir: Path
    ) -> None:
        """Export monthly split as CSV."""
        filename = f"{data_type.name.lower()}.csv"
        data.dataframe.to_csv(month_dir / filename)

    def export_aligned_complete_dataset(
        self, data: AlignmentResult, output_dir: Path
    ) -> None:
        """Export complete aligned dataset as CSV."""
        data.dataframe.to_csv(output_dir / "aligned_data.csv")

    def export_aligned_monthly_split(
        self, data: AlignmentResult, month_dir: Path
    ) -> None:
        """Export monthly split of aligned data as CSV."""
        data.dataframe.to_csv(month_dir / "aligned_data.csv")
        if self.config.include_processing_notes:
            self.export_processing_notes(data, month_dir)

    def export_processing_notes(
        self, data: Union[ProcessedTypeData, AlignmentResult], output_path: Path
    ) -> None:
        """Export processing notes as JSON."""
        common_data = {
            "export_date": pd.Timestamp.now().isoformat(),
            "date_range": f"{data.dataframe.index.min().strftime('%Y-%m-%d')} to {data.dataframe.index.max().strftime('%Y-%m-%d')}",
            "record_count": len(data.dataframe),
            "notes": data.processing_notes,
        }

        if isinstance(data, ProcessedTypeData):
            common_data["source_units"] = {
                k: v.value for k, v in data.source_units.items()
            }
        else:  # AlignmentResult
            common_data["frequency"] = data.frequency
            common_data["completeness"] = {
                col: f"{(data.dataframe[col].notna().mean() * 100):.1f}%"
                for col in data.dataframe.columns
            }

        with open(output_path / "processing_notes.json", "w", encoding="utf-8") as f:
            json.dump(common_data, f, indent=2)


def create_csv_exporter(output_dir: str | Path) -> CSVExporter:
    """Factory function for CSV exporter."""
    config = ExportConfig(output_dir=Path(output_dir))
    return CSVExporter(config)
