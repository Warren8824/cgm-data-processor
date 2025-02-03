"""LibreView CSV format definition.

This format handles CSV exports from LibreView, specifically for FreeStyle Libre devices.
The CSV contains various types of diabetes data including CGM readings, insulin doses,
carbohydrates, and notes."""

from src.core.data_types import (
    ColumnMapping,
    ColumnRequirement,
    DataType,
    DeviceFormat,
    FileConfig,
    FileType,
    TableStructure,
    Unit,
)

LIBREVIEW_CSV_FORMAT = DeviceFormat(
    name="libreview_csv",
    files=[
        FileConfig(
            name_pattern="*.csv",
            file_type=FileType.CSV,
            tables=[
                TableStructure(
                    name="",  # CSV files use empty string for table name
                    timestamp_column="Device Timestamp",
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
                        # Glucose readings
                        ColumnMapping(
                            source_name="Historic Glucose mg/dL",
                            data_type=DataType.CGM,
                            unit=Unit.MGDL,
                        ),
                        ColumnMapping(
                            source_name="Scan Glucose mg/dL",
                            data_type=DataType.CGM,
                            unit=Unit.MGDL,
                            is_primary=False,
                        ),
                        ColumnMapping(
                            source_name="Strip Glucose mg/dL",
                            data_type=DataType.BGM,
                            unit=Unit.MGDL,
                            requirement=ColumnRequirement.REQUIRED_NULLABLE,
                        ),
                        # Insulin data
                        ColumnMapping(
                            source_name="Rapid-Acting Insulin (units)",
                            data_type=DataType.INSULIN,
                            unit=Unit.UNITS,
                            requirement=ColumnRequirement.REQUIRED_NULLABLE,
                        ),
                        ColumnMapping(
                            source_name="Long-Acting Insulin (units)",
                            data_type=DataType.INSULIN,
                            unit=Unit.UNITS,
                            requirement=ColumnRequirement.REQUIRED_NULLABLE,
                            is_primary=False,
                        ),
                        ColumnMapping(
                            source_name="Meal Insulin (units)",
                            data_type=DataType.INSULIN,
                            unit=Unit.UNITS,
                            requirement=ColumnRequirement.REQUIRED_NULLABLE,
                            is_primary=False,
                        ),
                        ColumnMapping(
                            source_name="Correction Insulin (units)",
                            data_type=DataType.INSULIN,
                            unit=Unit.UNITS,
                            requirement=ColumnRequirement.REQUIRED_NULLABLE,
                            is_primary=False,
                        ),
                        ColumnMapping(
                            source_name="User Change Insulin (units)",
                            data_type=DataType.INSULIN,
                            unit=Unit.UNITS,
                            requirement=ColumnRequirement.REQUIRED_NULLABLE,
                            is_primary=False,
                        ),
                        # Carbohydrate data
                        ColumnMapping(
                            source_name="Carbohydrates (grams)",
                            data_type=DataType.CARBS,
                            unit=Unit.GRAMS,
                            requirement=ColumnRequirement.REQUIRED_NULLABLE,
                        ),
                        # Notes
                        ColumnMapping(
                            source_name="Notes",
                            data_type=DataType.NOTES,
                            requirement=ColumnRequirement.REQUIRED_NULLABLE,
                        ),
                    ],
                ),
            ],
        )
    ],
)
