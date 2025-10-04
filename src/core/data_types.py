"""Core data type definitions for diabetes data processing.

This module defines the core data types and structures used for processing diabetes device
data exports. It supports multiple file formats, different units of measurement, and
various data types commonly found in diabetes management tools.

The structure allows for:
    - Multiple files in a single format
    - Multiple data types per table
    - Different file types (SQLite, CSV, etc.)
    - Flexible column mapping
    - Primary/secondary data distinction
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

from src.core.exceptions import FormatValidationError


class FileType(Enum):
    """Supported file types for diabetes data."""

    SQLITE = "sqlite"
    CSV = "csv"
    JSON = "json"
    XML = "xml"


class DataType(Enum):
    """Core diabetes data types."""

    # CGM Data
    CGM = auto()  # Continuous glucose monitoring data

    # BGM Data
    BGM = auto()  # Blood glucose meter readings

    # Treatment Data
    INSULIN = auto()  # Insulin doses
    INSULIN_META = auto()  # Insulin metadata eg brand
    CARBS = auto()  # Carbohydrate intake
    NOTES = auto()  # Text notes/comments


class TimestampType(Enum):
    """Common types of timestamp format, ensuring correct conversion"""

    UNIX_SECONDS = "unix_seconds"
    UNIX_MILLISECONDS = "unix_milliseconds"
    UNIX_MICROSECONDS = "unix_microseconds"
    ISO_8601 = "iso_8601"
    UNKNOWN = "unknown"


class ColumnRequirement(Enum):
    """Defines how column should be validated and if data reading is required"""

    CONFIRMATION_ONLY = auto()  # Just needs to exist - no data read
    REQUIRED_WITH_DATA = auto()  # Must exist - data read & fail if not
    REQUIRED_NULLABLE = auto()  # Must exist, can have all missing values - data read
    OPTIONAL = auto()  # May or may not exist - data read


class Unit(Enum):
    """Supported units of measurement."""

    MGDL = "mg/dL"  # Blood glucose in mg/dL
    MMOL = "mmol/L"  # Blood glucose in mmol/L
    UNITS = "U"  # Insulin units
    GRAMS = "g"  # Carbohydrates in grams


@dataclass
class ColumnMapping:
    """Maps source columns to standardized data types.

    Args:
        source_name: Original column name in the data source
        data_type: Type of data this column contains (if applicable - Any column can be used for confirming device.)
        unit: Unit of measurement (if applicable)
        requirement: Type of requirement - default = REQUIRED_WITH_DATA
        is_primary: Whether this is the primary column - default = True

    Examples:
        >>> glucose_column = ColumnMapping(
        ...     source_name="calculated_value",
        ...     data_type=DataType.CGM,
        ...     unit=Unit.MGDL,
        ... )
        >>> raw_glucose = ColumnMapping(
        ...     source_name="raw_data",
        ...     data_type=DataType.CGM,
        ...     requirement=ColumnRequirement.REQUIRED_NULLABLE,
        ...     is_primary=False
        ... )
    """

    source_name: str
    data_type: Optional[DataType] = None
    unit: Optional[Unit] = None
    requirement: ColumnRequirement = ColumnRequirement.REQUIRED_WITH_DATA
    is_primary: bool = True


@dataclass
class TableStructure:
    """Defines the structure of a data table.

    Args:
        name: Table name in the data source (empty string for CSV files)
        timestamp_column: Name of the timestamp column
        columns: List of column mappings

    Examples:
        >>> bgreadings = TableStructure(
        ...     name="bgreadings",
        ...     timestamp_column="timestamp",
        ...     columns=[
        ...         ColumnMapping(
        ...             source_name="calculated_value",
        ...             data_type=DataType.CGM,
        ...             unit=Unit.MGDL
        ...         ),
        ...         ColumnMapping(
        ...             source_name="raw_data",
        ...             data_type=DataType.CGM,
        ...             requirement=ColumnRequirement.REQUIRED_NULLABLE,
        ...             is_primary=False
        ...         )
        ...     ]
        ... )
    """

    name: str
    timestamp_column: str
    columns: List[ColumnMapping]
    header_row: Optional[int] = (
        None  # 0-based index of the header row in CSV files (None = auto-detect)
    )

    def validate_columns(self):
        """Validate that table has at least one column defined.

        Raises:
            FormatValidationError: If table has no columns defined
        """
        if not self.columns:
            raise FormatValidationError(
                f"Table {self.name} must have at least one column defined",
                details={"table_name": self.name, "columns_count": 0},
            )

    def validate_unique_source_names(self):
        """Validate that all column names are unique.

        Raises:
            FormatValidationError: If duplicate column names are found
        """
        column_names = [col.source_name for col in self.columns]
        unique_names = set(column_names)
        if len(column_names) != len(unique_names):
            duplicates = [name for name in unique_names if column_names.count(name) > 1]
            raise FormatValidationError(
                f"Duplicate column names in table {self.name}",
                details={"table_name": self.name, "duplicate_columns": duplicates},
            )

    def validate_primary_columns(self):
        """Validate that each data type has at most one primary column.

        Raises:
            FormatValidationError: If multiple primary columns exist for any data type
        """
        for data_type in DataType:
            primary_columns = [
                col.source_name
                for col in self.columns
                if col.data_type == data_type and col.is_primary
            ]
            if len(primary_columns) > 1:
                raise FormatValidationError(
                    f"Multiple primary columns for {data_type.value} in table {self.name}",
                    details={
                        "table_name": self.name,
                        "data_type": data_type.value,
                        "primary_columns": primary_columns,
                    },
                )

    def __post_init__(self):
        self.validate_columns()
        self.validate_unique_source_names()
        self.validate_primary_columns()


@dataclass
class FileConfig:
    """Configuration for a specific file in a device format.

    Args:
        name_pattern: Pattern to match filename (e.g., "*.sqlite", "glucose.csv")
        file_type: Type of the data file
        tables: List of table structures in the file

    Examples:
        >>> sqlite_file = FileConfig(
        ...     name_pattern="*.sqlite",
        ...     file_type=FileType.SQLITE,
        ...     tables=[bgreadings]  # TableStructure from previous example
        ... )
    """

    name_pattern: str
    file_type: FileType
    tables: List[TableStructure]

    def __post_init__(self):
        """Validate file configuration after initialization.

        Raises:
            FormatValidationError: If file configuration is invalid
        """
        if not self.tables:
            raise FormatValidationError(
                f"File {self.name_pattern} must have at least one table defined",
                details={"file_pattern": self.name_pattern},
            )

        # For CSV files, ensure only one table with empty name
        if self.file_type == FileType.CSV:
            if len(self.tables) > 1:
                raise FormatValidationError(
                    "CSV files can only have one table structure",
                    details={
                        "file_pattern": self.name_pattern,
                        "tables_count": len(self.tables),
                    },
                )
            if self.tables[0].name != "":
                raise FormatValidationError(
                    f"CSV file table name should be empty string for file {self.name_pattern}",
                    details={
                        "file_pattern": self.name_pattern,
                        "table_name": self.tables[0].name,
                    },
                )


@dataclass
class DeviceFormat:
    """Complete format specification for a diabetes device data export.

    Args:
        name: Name of the device/format
        files: List of file configurations

    Examples:
        >>> xdrip_format = DeviceFormat(
        ...     name="xdrip_sqlite",
        ...     files=[sqlite_file]  # FileConfig from previous example
        ... )
    """

    name: str
    files: List[FileConfig]

    def __post_init__(self):
        """Validate device format after initialization.

        Raises:
            FormatValidationError: If device format is invalid
        """
        if not self.files:
            raise FormatValidationError(
                f"Device format {self.name} must have at least one file defined",
                details={"format_name": self.name},
            )

    def __str__(self) -> str:
        """String representation including available data types."""
        types = set()
        for file_config in self.files:
            for table in file_config.tables:
                for column in table.columns:
                    if column.is_primary:
                        types.add(column.data_type.name)
        return f"{self.name} - Available data: {', '.join(sorted(types))}"
