"""LibreView CSV format definition.

This format handles CSV exports from LibreView, specifically for FreeStyle Libre devices.
The CSV contains various types of diabetes data including CGM readings, insulin doses,
carbohydrates, and notes."""

from src.core.data_types import (
    ColumnMapping,
    ColumnRequirement,
    DeviceFormat,
    FileConfig,
    FileType,
    TableStructure,
)

LIBREVIEW_CSV_FORMAT = DeviceFormat(
    name="test_csv",
    files=[
        FileConfig(
            name_pattern="*.csv",
            file_type=FileType.CSV,
            tables=[
                TableStructure(
                    name="",  # CSV files use empty string for table name
                    timestamp_column="Device Timestamp",
                    header_row=1,
                    columns=[
                        # Device identification columns
                        ColumnMapping(
                            source_name="Device",
                            requirement=ColumnRequirement.CONFIRMATION_ONLY,
                        ),
                        ColumnMapping(
                            source_name="Serial Number",
                            requirement=ColumnRequirement.CONFIRMATION_ONLY,
                        ),
                    ],
                ),
            ],
        )
    ],
)
