# Data Types API Reference

The `core.data_types` module provides the foundational type system for handling diabetes device data. It defines a comprehensive set of data structures and enums that enable type-safe processing of various diabetes-related data formats.

## Core Enums

### DataType

Defines the fundamental types of diabetes data that can be processed.

```python
from src.core.data_types import DataType

class DataType(Enum):
    CGM = auto()         # Continuous glucose monitoring readings
    BGM = auto()         # Blood glucose meter readings
    INSULIN = auto()     # Insulin doses
    INSULIN_META = auto() # Insulin metadata (e.g., brand, type)
    CARBS = auto()       # Carbohydrate intake
    NOTES = auto()       # Text notes/comments
```

### FileType

Specifies supported file formats for data imports.

```python
class FileType(Enum):
    SQLITE = "sqlite"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
```

### Unit

Defines standard units of measurement for diabetes data.

```python
class Unit(Enum):
    MGDL = "mg/dL"    # Blood glucose in milligrams per deciliter
    MMOL = "mmol/L"   # Blood glucose in millimoles per liter
    UNITS = "U"       # Insulin units
    GRAMS = "g"       # Carbohydrates in grams
```

### ColumnRequirement

Specifies validation and data requirements for columns.

```python
class ColumnRequirement(Enum):
    CONFIRMATION_ONLY = auto()   # Column must exist but data isn't read
    REQUIRED_WITH_DATA = auto()  # Column must exist with valid data
    REQUIRED_NULLABLE = auto()   # Column must exist but can have missing values
    OPTIONAL = auto()            # Column may or may not exist
```

## Data Structures

### ColumnMapping

Maps source data columns to standardized internal representations.

```python
@dataclass
class ColumnMapping:
    source_name: str
    data_type: Optional[DataType] = None
    unit: Optional[Unit] = None
    requirement: ColumnRequirement = ColumnRequirement.REQUIRED_WITH_DATA
    is_primary: bool = True
```

**Key Concepts:**
- `source_name`: Original column name in the source data
- `data_type`: Type of data contained in the column
- `unit`: Unit of measurement (if applicable)
- `requirement`: Validation requirements for the column
- `is_primary`: Indicates whether this is the primary column for its data type

### TableStructure

Defines the structure of a data table, including its columns and timestamp handling.

```python
@dataclass
class TableStructure:
    name: str
    timestamp_column: str
    columns: List[ColumnMapping]
```

**Validation Methods:**
- `validate_columns()`: Ensures at least one column is defined
- `validate_unique_source_names()`: Checks for duplicate column names
- `validate_primary_columns()`: Ensures each data type has at most one primary column

### FileConfig

Specifies the configuration for a single file within a device format.

```python
@dataclass
class FileConfig:
    name_pattern: str
    file_type: FileType
    tables: List[TableStructure]
```

**Validation Rules:**
- Must have at least one table defined
- CSV files are limited to one table with an empty name
- File patterns must match supported file types

### DeviceFormat

Defines the complete format specification for a diabetes device data export.

```python
@dataclass
class DeviceFormat:
    name: str
    files: List[FileConfig]
```

## Usage Example

Here's a complete example of defining an XDrip+ SQLite backup format:

```python
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

XDRIP_SQLITE_FORMAT = DeviceFormat(
    name="xdrip_sqlite",
    files=[
        FileConfig(
            name_pattern="*.sqlite",
            file_type=FileType.SQLITE,
            tables=[
                # BgReadings table with CGM data
                TableStructure(
                    name="BgReadings",
                    timestamp_column="timestamp",
                    columns=[
                        ColumnMapping(
                            source_name="calculated_value",
                            data_type=DataType.CGM,
                            unit=Unit.MGDL,
                        ),
                        ColumnMapping(
                            source_name="raw_data",
                            data_type=DataType.CGM,
                            is_primary=False,
                        ),
                    ],
                ),
                # Treatments table with insulin, carbs, and notes
                TableStructure(
                    name="Treatments",
                    timestamp_column="timestamp",
                    columns=[
                        ColumnMapping(
                            source_name="insulin",
                            data_type=DataType.INSULIN,
                            unit=Unit.UNITS,
                        ),
                        ColumnMapping(
                            source_name="carbs",
                            data_type=DataType.CARBS,
                            unit=Unit.GRAMS,
                        ),
                        ColumnMapping(
                            source_name="notes",
                            data_type=DataType.NOTES,
                            requirement=ColumnRequirement.REQUIRED_NULLABLE,
                        ),
                    ],
                ),
            ],
        )
    ],
)
```

## Best Practices

1. **Column Requirements**
   - Use `REQUIRED_WITH_DATA` for essential numeric data
   - Use `REQUIRED_NULLABLE` for optional metadata
   - Use `CONFIRMATION_ONLY` for format validation columns

2. **Primary Columns**
   - Each data type should have exactly one primary column
   - Secondary columns can provide additional context or raw data
   - Set `is_primary=False` for supporting data columns

3. **Units**
   - Always specify units for numeric data
   - Match units to the source data format
   - Unit conversion happens during processing

4. **Validation**
   - All data structures perform validation on initialization
   - Handle validation errors appropriately
   - Use consistent naming patterns across formats

## Error Handling

Data type-related errors are typically raised as `FormatValidationError` with detailed error messages and context:

```python
try:
    device_format = DeviceFormat(...)
except FormatValidationError as e:
    print(f"Validation failed: {str(e)}")
    print(f"Details: {e.details}")
```