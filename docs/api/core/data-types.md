# Core API Reference

!!! note "Module Location"
    `src/core/data_types.py`

### Key Components

#### FileType

```python
class FileType(Enum):
    """Supported file types for diabetes data."""
    SQLITE = "sqlite"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
```

!!! info "Usage"
    Used to specify and validate input file types during format detection.
    
#### DataType

```python
class DataType(Enum):
    """Core diabetes data types."""
    CGM = auto()        # Continuous glucose monitoring data
    BGM = auto()        # Blood glucose meter readings
    INSULIN = auto()    # Insulin doses
    INSULIN_META = auto() # Insulin metadata
    CARBS = auto()      # Carbohydrate intake
    NOTES = auto()      # Text notes/comments
```

!!! example "Example"

    ```python
    from src.core.data_types import DataType
    
    # Check if data is CGM reading
    if column.data_type == DataType.CGM:
        process_cgm_data(column)
    ```

#### TimestampType

```python
class TimestampType(Enum):
    """Common types of timestamp format."""
    UNIX_SECONDS = "unix_seconds"
    UNIX_MILLISECONDS = "unix_milliseconds"
    UNIX_MICROSECONDS = "unix_microseconds"
    ISO_8601 = "iso_8601"
    UNKNOWN = "unknown"
```

!!! warning "Important"
    All timestamps are converted to UTC during processing.

#### ColumnRequirement

```python
class ColumnRequirement(Enum):
    """Defines column validation requirements."""
    CONFIRMATION_ONLY = auto()    # Just needs to exist
    REQUIRED_WITH_DATA = auto()   # Must exist with data
    REQUIRED_NULLABLE = auto()    # Can have missing values
    OPTIONAL = auto()             # May not exist
```

#### Unit

```python
class Unit(Enum):
    """Supported units of measurement."""
    MGDL = "mg/dL"    # Blood glucose
    MMOL = "mmol/L"   # Blood glucose
    UNITS = "U"       # Insulin
    GRAMS = "g"       # Carbohydrates
```

#### ColumnMapping

```python
@dataclass
class ColumnMapping:
    """Maps source columns to standardized data types.
    
    Args:
        source_name: Original column name
        data_type: Column data type
        unit: Unit of measurement
        requirement: Validation requirement
        is_primary: Primary column flag
    """
    source_name: str
    data_type: Optional[DataType] = None
    unit: Optional[Unit] = None
    requirement: ColumnRequirement = ColumnRequirement.REQUIRED_WITH_DATA
    is_primary: bool = True
```

!!! example "ColumnMapping Example"
```python
    glucose = ColumnMapping(
        source_name="calculated_value",
        data_type=DataType.CGM,
        unit=Unit.MGDL
    )
```

#### TableStructure

```python
@dataclass
class TableStructure:
    """Defines data table structure.
    
    Args:
        name: Table name
        timestamp_column: Timestamp column name
        columns: Column mappings
    
    Methods:
        validate_columns(): Ensures table has columns
        validate_unique_source_names(): Checks for duplicates
        validate_primary_columns(): Validates primary columns
    """
    name: str
    timestamp_column: str
    columns: List[ColumnMapping]
```

!!! info "Validation Methods"
    All validation methods raise `FormatValidationError` on failure

#### FileConfig

```python
@dataclass
class FileConfig:
    """Configuration for device format file.
    
    Args:
        name_pattern: Filename pattern
        file_type: File type enum
        tables: Table structures
    
    Validates:
        - At least one table
        - CSV files have one unnamed table
    """
    name_pattern: str
    file_type: FileType
    tables: List[TableStructure]
```

#### DeviceFormat

```python
@dataclass
class DeviceFormat:
    """Complete device format specification.
    
    Args:
        name: Format name
        files: File configurations
    
    Methods:
        __str__: Returns format name and data types
    """
    name: str
    files: List[FileConfig]
```

!!! example "Complete Format Example"

```python
    xdrip_format = DeviceFormat(
        name="xdrip_sqlite",
        files=[
            FileConfig(
                name_pattern="*.sqlite",
                file_type=FileType.SQLITE,
                tables=[
                    TableStructure(
                        name="BgReadings",
                        timestamp_column="timestamp",
                        columns=[
                            ColumnMapping(
                                source_name="calculated_value",
                                data_type=DataType.CGM,
                                unit=Unit.MGDL
                            )
                        ]
                    )
                ]
            )
        ]
    )
```

## Complete Reference

::: src.core.data_types
    options:
      show_root_heading: true
      show_source: true