"""CSV exporter implementation."""

import json
from pathlib import Path

import pandas as pd

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

        if self.config.include_processing_notes:
            self.export_processing_notes(data, month_dir)

    def export_processing_notes(
        self, data: ProcessedTypeData, output_path: Path
    ) -> None:
        """Export processing notes as JSON."""
        notes_data = {
            "notes": data.processing_notes,
            "source_units": {k: v.value for k, v in data.source_units.items()},
            "export_date": pd.Timestamp.now().isoformat(),
        }

        with open(output_path / "processing_notes.json", "w", encoding="utf-8") as f:
            json.dump(notes_data, f, indent=2)


def create_csv_exporter(output_dir: str | Path) -> CSVExporter:
    """Factory function for CSV exporter."""

    config = ExportConfig(output_dir=Path(output_dir))
    return CSVExporter(config)
