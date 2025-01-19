# Data Types API Reference

The `data_types` module defines the core data structures and types used throughout the CGM Data Processor. It provides a comprehensive type system for handling various kinds of diabetes-related data, file formats, and measurement units.

## Enums

### FileType

Defines supported file types for diabetes device data exports.

```python
class FileType(Enum):
    SQLITE = "sqlite"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
```

### DataType

Defines core diabetes data types supported by the processor.

```python
class DataType(Enum):
    CGM = auto()        # Continuous glucose monitoring data
    BGM = auto()        # Blood glucose meter readings
    INSULIN = auto()    # Insulin doses
    INSULIN_META = auto() # Insulin metadata (e.g., brand)
    CARBS = auto()      # Carbohydrate intake
    NOTES = auto()      # Text notes/comments
```

### TimestampType

Defines common timestamp formats to ensure correct conversion.

```python
class TimestampType(Enum):
    UNIX_SECONDS = "unix_seconds"
    UNIX_MILLISECONDS = "unix_milliseconds"
    UNIX_MICROSECONDS = "unix_microseconds"
    ISO_8601 = "iso_8601"
    UNKNOWN = "unknown"
```

### ColumnRequirement

Defines how columns should be validated and whether data reading is required.

```python
class ColumnRequirement(Enum):
    CONFIRMATION_ONLY = auto()   # Column must exist but data isn't read
    REQUIRED_WITH_DATA = auto()  # Column must exist with valid data
    REQUIRED_NULLABLE = auto()   # Column must exist but can have missing values
    OPTIONAL = auto()            # Column may or may not exist
```

### Unit

Defines supported units of measurement.

```python
class Unit(Enum):
    MGDL = "mg/dL"    # Blood glucose in mg/dL
    MMOL = "mmol/L"   # Blood glucose in mmol/L
    UNITS = "U"       # Insulin units
    GRAMS = "g"       # Carbohydrates in grams
```

## Data Classes

### ColumnMapping

Maps source columns to standardized data types.

```python
@dataclass
class ColumnMapping:
    source_name: str
    data_type: Optional[DataType] = None
    unit: Optional[Unit] = None
    requirement: ColumnRequirement = ColumnRequirement.REQUIRED_WITH_DATA
    is_primary: bool = True
```

**Parameters:**
- `source_name`: Original column name in the data source
- `data_type`: Type of data this column contains (optional)
- `unit`: Unit of measurement (optional)
- `requirement`: Type of requirement (defaults to REQUIRED_WITH_DATA)
- `is_primary`: Whether this is the primary column (defaults to True)

**Example:**
```python
# Define a glucose column mapping
glucose_column = ColumnMapping(
    source_name="calculated_value",
    data_type=DataType.CGM,
    unit=Unit.MGDL
)

# Define a secondary raw data column
raw_glucose = ColumnMapping(
    source_name="raw_data",
    data_type=DataType.CGM,
    requirement=ColumnRequirement.REQUIRED_NULLABLE,
    is_primary=False
)
```

### TableStructure

Defines the structure of a data table within a file.

```python
@dataclass
class TableStructure:
    name: str
    timestamp_column: str
    columns: List[ColumnMapping]
```

**Parameters:**
- `name`: Table name in the data source (empty string for CSV files)
- `timestamp_column`: Name of the timestamp column
- `columns`: List of column mappings

**Methods:**
- `validate_columns()`: Ensures table has at least one column defined
- `validate_unique_source_names()`: Ensures all column names are unique
- `validate_primary_columns()`: Ensures each data type has at most one primary column

**Example:**
```python
bgreadings = TableStructure(
    name="bgreadings",
    timestamp_column="timestamp",
    columns=[
        ColumnMapping(
            source_name="calculated_value",
            data_type=DataType.CGM,
            unit=Unit.MGDL
        ),
        ColumnMapping(
            source_name="raw_data",
            data_type=DataType.CGM,
            requirement=ColumnRequirement.REQUIRED_NULLABLE,
            is_primary=False
        )
    ]
)
```

### FileConfig

Configuration for a specific file in a device format.

```python
@dataclass
class FileConfig:
    name_pattern: str
    file_type: FileType
    tables: List[TableStructure]
```

**Parameters:**
- `name_pattern`: Pattern to match filename (e.g., "*.sqlite", "glucose.csv")
- `file_type`: Type of the data file
- `tables`: List of table structures in the file

**Validation:**
- Ensures at least one table is defined
- For CSV files:
  - Only one table structure allowed
  - Table name must be an empty string

**Example:**
```python
sqlite_file = FileConfig(
    name_pattern="*.sqlite",
    file_type=FileType.SQLITE,
    tables=[bgreadings]  # TableStructure from previous example
)
```

### DeviceFormat

Complete format specification for a diabetes device data export.

```python
@dataclass
class DeviceFormat:
    name: str
    files: List[FileConfig]
```

**Parameters:**
- `name`: Name of the device/format
- `files`: List of file configurations

**Methods:**
- `__str__`: Returns a string representation including available data types

**Example:**
```python
xdrip_format = DeviceFormat(
    name="xdrip_sqlite",
    files=[sqlite_file]  # FileConfig from previous example
)
```

## Usage Notes

1. All data structures include validation logic that runs during initialization
2. Validation ensures:
   - Required fields are present
   - Data consistency across related fields
   - Format-specific rules are followed
3. CSV files have special validation rules due to their single-table nature
4. Primary/secondary column designation allows for both calculated and raw data handling
5. The type system supports future expansion through enum extensions