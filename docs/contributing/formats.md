# Contributing New Formats

This guide will walk you through the process of adding support for new diabetes device data formats to the project. Our system is designed to be extensible, allowing for easy addition of new data formats while maintaining consistent data handling and validation.

## Overview

The format system consists of several key components:

1. **Device Formats**: Define how to read and interpret data from specific diabetes devices
2. **File Configurations**: Specify file types and patterns to match
3. **Table Structures**: Define the layout of data tables
4. **Column Mappings**: Map source columns to standardized data types

## Quick Start

Here's a basic example of adding support for a new CSV format:

```python
from src.core.data_types import (
    ColumnMapping,
    DataType,
    DeviceFormat,
    FileConfig,
    FileType,
    TableStructure,
    Unit,
)

MY_DEVICE_FORMAT = DeviceFormat(
    name="my_device_csv",
    files=[
        FileConfig(
            name_pattern="*.csv",
            file_type=FileType.CSV,
            tables=[
                TableStructure(
                    name="",  # CSV files use empty string
                    timestamp_column="Time",
                    columns=[
                        ColumnMapping(
                            source_name="Glucose",
                            data_type=DataType.CGM,
                            unit=Unit.MGDL,
                        ),
                    ],
                ),
            ],
        )
    ],
)
```

## Step-by-Step Guide

### 1. Create a New Format File

Create a new Python file in the appropriate manufacturer directory under `devices/`. For example:
- `devices/dexcom/g6_csv.py`
- `devices/medtronic/guardian_export.py`

### 2. Define Core Components

#### Device Format
```python
MY_DEVICE_FORMAT = DeviceFormat(
    name="unique_format_name",  # Use lowercase with underscores
    files=[...]  # List of FileConfig objects
)
```

#### File Configuration
```python
FileConfig(
    name_pattern="*.csv",  # Glob pattern to match files
    file_type=FileType.CSV,  # SQLITE, CSV, JSON, or XML
    tables=[...]  # List of TableStructure objects
)
```

#### Table Structure
```python
TableStructure(
    name="table_name",  # Empty string for CSV files
    timestamp_column="timestamp",  # Column containing timestamps
    columns=[...]  # List of ColumnMapping objects
)
```

#### Column Mapping
```python
ColumnMapping(
    source_name="original_column_name",
    data_type=DataType.CGM,  # Type of data in this column
    unit=Unit.MGDL,  # Unit of measurement (if applicable)
    requirement=ColumnRequirement.REQUIRED_WITH_DATA,  # Column requirement type
    is_primary=True  # Whether this is primary data for the type
)
```

### 3. Available Data Types

The system supports these core data types:

- `DataType.CGM`: Continuous glucose monitoring data
- `DataType.BGM`: Blood glucose meter readings
- `DataType.INSULIN`: Insulin doses
- `DataType.INSULIN_META`: Insulin metadata (e.g., brand)
- `DataType.CARBS`: Carbohydrate intake
- `DataType.NOTES`: Text notes/comments

### 4. Column Requirements

Define how each column should be validated:

- `CONFIRMATION_ONLY`: Column must exist but data isn't read
- `REQUIRED_WITH_DATA`: Column must exist and contain data
- `REQUIRED_NULLABLE`: Column must exist but can have missing values
- `OPTIONAL`: Column may or may not exist

### 5. Units of Measurement

Available units:

- `Unit.MGDL`: Blood glucose in mg/dL
- `Unit.MMOL`: Blood glucose in mmol/L
- `Unit.UNITS`: Insulin units
- `Unit.GRAMS`: Carbohydrates in grams

### 6. Multiple Data Types and Files

Your format can support multiple data types and files. For example:

```python
DeviceFormat(
    name="multi_file_format",
    files=[
        FileConfig(
            name_pattern="glucose.csv",
            file_type=FileType.CSV,
            tables=[
                TableStructure(
                    name="",
                    timestamp_column="Time",
                    columns=[
                        ColumnMapping(
                            source_name="Glucose",
                            data_type=DataType.CGM,
                            unit=Unit.MGDL,
                        ),
                    ],
                ),
            ],
        ),
        FileConfig(
            name_pattern="insulin.csv",
            file_type=FileType.CSV,
            tables=[
                TableStructure(
                    name="",
                    timestamp_column="Time",
                    columns=[
                        ColumnMapping(
                            source_name="Dose",
                            data_type=DataType.INSULIN,
                            unit=Unit.UNITS,
                        ),
                        ColumnMapping(
                            source_name="Type",
                            data_type=DataType.INSULIN_META,
                        ),
                    ],
                ),
            ],
        ),
    ],
)
```

### 7. Primary vs Secondary Data

For each data type, you can have one primary column and multiple secondary columns:

```python
TableStructure(
    name="",
    timestamp_column="Time",
    columns=[
        ColumnMapping(
            source_name="calculated_glucose",
            data_type=DataType.CGM,
            unit=Unit.MGDL,
            is_primary=True,  # Primary column
        ),
        ColumnMapping(
            source_name="raw_glucose",
            data_type=DataType.CGM,
            unit=Unit.MGDL,
            is_primary=False,  # Secondary column
        ),
    ],
)
```

### 8. Validation Requirements

Your format must pass these validations:

1. At least one file must be defined
2. Each file must have at least one table
3. Each table must have at least one column
4. Column names within a table must be unique
5. Each data type can have only one primary column per table
6. CSV files must have exactly one table with an empty name

### 9. Testing Your Format

Test your format by:

1. Adding it to the appropriate manufacturer directory
2. Running the cli script with an example data file and debug argument:
```bash
python -m src.cli your_test_file.csv --debug
```

### 10. Common Patterns and Best Practices

1. **Column Requirements**
    - Use `CONFIRMATION_ONLY` for device identification columns
    - Use `REQUIRED_NULLABLE` for optional data types
    - Use `REQUIRED_WITH_DATA` for essential columns

2. **Data Organization**
    - Group related columns in the same table
    - Keep primary/secondary relationships clear
    - Document any special handling requirements

3. **File Patterns**
    - Use specific patterns when possible (e.g., "export.csv")
    - Use wildcards carefully (e.g., "*.sqlite")

4. **Error Handling**
    - Define clear validation requirements
    - Document any format-specific quirks
    - Handle missing or nullable values appropriately

## Examples

See these existing format definitions for reference:

1. XDrip+ SQLite Format:
    - Handles multiple tables
    - Shows primary/secondary relationships
    - Demonstrates metadata handling

2. LibreView CSV Format:
    - Shows single CSV file handling
    - Demonstrates multiple data types
    - Shows device confirmation columns

## Making Your Format More Robust

### Handle Edge Cases

Add `REQUIRED_NULLABLE` for columns that might be empty
Document any special data formats or requirements
Consider adding validation columns when needed


### Improve Documentation

```python
MY_DEVICE_FORMAT = DeviceFormat(
    name="my_device_format",
    files=[
        FileConfig(
            name_pattern="*.csv",
            file_type=FileType.CSV,
            tables=[
                TableStructure(
                    name="",
                    timestamp_column="Time",
                    # Document special requirements
                    # Example: Time column format: "YYYY-MM-DD HH:mm:ss"
                    columns=[...]
                )
            ]
        )
    ]
)
```

## Format Verification Checklist

:octicons-check-16: All required columns mapped

:octicons-check-16: Units correctly specified

:octicons-check-16: Primary/secondary relationships clear

:octicons-check-16: Timestamp format documented

:octicons-check-16: Edge cases handled

:octicons-check-16: Requirements appropriate for each column

:octicons-check-16: Documentation complete

## Need Help?

If you need assistance:

1. Check existing format definitions for examples
2. Review the core data types documentation
3. Open an issue for format-specific questions
4. Submit a draft PR for feedback

Remember: Good format definitions are clear, well-documented, and handle edge cases appropriately.