# Creating Device Formats

## Overview

This guide explains how to create device format definitions for diabetes data sources. The format system supports:

- Single or multiple file formats
- SQLite databases or CSV files
- Multiple data types per file
- Format-specific validation columns

## Data Types

Available data types for diabetes data:

- `CGM` - Continuous glucose monitoring data
- `BGM` - Blood glucose meter readings
- `INSULIN` - Insulin doses
- `INSULIN_META` - Insulin metadata (brand, type)
- `CARBS` - Carbohydrate intake
- `NOTES` - Text notes/comments

## Units

Supported units of measurement:

- `MGDL` - Blood glucose in mg/dL
- `MMOL` - Blood glucose in mmol/L
- `UNITS` - Insulin units
- `GRAMS` - Carbohydrates in grams

## Basic Examples

### Single SQLite File Format

Example of XDrip+ format with CGM data and treatments:

```python
XDRIP_SQLITE_FORMAT = DeviceFormat(
    name="xdrip_sqlite",
    files=[
        FileConfig(
            name_pattern="*.sqlite",
            file_type=FileType.SQLITE,
            tables=[
                TableStructure(
                    name="bgreadings",
                    timestamp_column="timestamp",
                    columns=[
                        ColumnMapping(
                            source_name="calculated_value",
                            data_type=DataType.CGM,
                            unit=Unit.MGDL
                        ),
                        # Secondary raw data column
                        ColumnMapping(
                            source_name="raw_data",
                            data_type=DataType.CGM,
                            is_primary=False,
                            required=False
                        ),
                        # Format validation column
                        ColumnMapping(
                            source_name="device",
                            required=True  # Required for format validation
                        )
                    ]
                ),
                TableStructure(
                    name="treatments",
                    timestamp_column="timestamp",
                    columns=[
                        ColumnMapping(
                            source_name="insulin",
                            data_type=DataType.INSULIN,
                            unit=Unit.UNITS
                        ),
                        ColumnMapping(
                            source_name="insulinJSON",
                            data_type=DataType.INSULIN_META
                        ),
                        ColumnMapping(
                            source_name="carbs",
                            data_type=DataType.CARBS,
                            unit=Unit.GRAMS
                        ),
                        ColumnMapping(
                            source_name="notes",
                            data_type=DataType.NOTES,
                            required=False
                        )
                    ]
                )
            ]
        )
    ]
)
```

### Multiple CSV Files Format

Example of a device that exports separate files for glucose and treatments:

```python
MULTI_CSV_FORMAT = DeviceFormat(
    name="multi_csv_device",
    files=[
        FileConfig(
            name_pattern="glucose.csv",
            file_type=FileType.CSV,
            tables=[
                TableStructure(
                    name="",  # CSV files use empty table name
                    timestamp_column="Time",
                    columns=[
                        ColumnMapping(
                            source_name="Glucose Value",
                            data_type=DataType.CGM,
                            unit=Unit.MMOL
                        ),
                        # Format-specific validation column
                        ColumnMapping(
                            source_name="Serial Number",
                            required=True
                        )
                    ]
                )
            ]
        ),
        FileConfig(
            name_pattern="treatments.csv",
            file_type=FileType.CSV,
            tables=[
                TableStructure(
                    name="",
                    timestamp_column="DateTime",
                    columns=[
                        ColumnMapping(
                            source_name="Insulin Amount",
                            data_type=DataType.INSULIN,
                            unit=Unit.UNITS
                        ),
                        ColumnMapping(
                            source_name="Insulin Type",
                            data_type=DataType.INSULIN_META
                        ),
                        ColumnMapping(
                            source_name="Carbs",
                            data_type=DataType.CARBS,
                            unit=Unit.GRAMS
                        )
                    ]
                )
            ]
        )
    ]
)
```

## Advanced Features

### Format Validation Columns
Use columns without data types to validate specific formats:

```python
ColumnMapping(
    source_name="device_model",
    required=True  # Must exist to confirm format
)
```

### Secondary Data Sources
Mark non-primary data sources with `is_primary=False`:

```python
ColumnMapping(
    source_name="raw_value",
    data_type=DataType.CGM,
    is_primary=False,
    required=False
)
```

### Optional Columns
Mark optional columns with `required=False`:

```python
ColumnMapping(
    source_name="notes",
    data_type=DataType.NOTES,
    required=False
)
```

## Directory Structure

Place your format definitions in the appropriate manufacturer directory:

```
src/
└── core/
    └── devices/
        ├── dexcom/
        │   ├── g6_csv.py
        │   └── g7_csv.py
        ├── xdrip/
        │   ├── sqlite_backup.py
        │   └── csv_backup.py
        └── libre/
            └── libre2_csv.py
```

## Key Points

1. Default Values:
   - `required=True`
   - `is_primary=True`
   - Only specify these when you need different behavior

2. CSV Files:
   - Must use empty string (`""`) for table name
   - One table per file

3. Timestamps:
   - Every table requires a timestamp column
   - Can have different names in different tables

4. Format Validation:
   - Use columns without data types for format-specific validation
   - These columns are checked during format detection

5. Insulin Data:
   - Use INSULIN for dose values
   - Use INSULIN_META for type/brand information
   - Both can be used for basal/bolus classification

## Best Practices

1. Use clear, descriptive names for formats and columns
2. Include all required columns for format validation
3. Mark optional columns explicitly
4. Use insulin metadata for proper dose classification
5. Include format-specific validation columns when needed