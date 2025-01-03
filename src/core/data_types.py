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


class FileType(Enum):
    """Supported file types for diabetes data."""

    SQLITE = "sqlite"
    CSV = "csv"
    JSON = "json"
    XML = "xml"


class DataType(Enum):
    """Core diabetes data types."""

    CGM = auto()  # Continuous glucose monitoring data
    BGM = auto()  # Blood glucose meter readings
    INSULIN = auto()  # Insulin doses
    INSULIN_META = auto()  # Insulin metadata eg brand
    CARBS = auto()  # Carbohydrate intake
    NOTES = auto()  # Text notes/comments


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
        data_type: Type of data this column contains (if applicable - Any column can be
        used for confirming device.)
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

    def validate_columns(self):
        if not self.columns:
            raise ValueError(f"Table {self.name} must have at least one column defined")

    def validate_unique_source_names(self):
        column_names = [col.source_name for col in self.columns]
        if len(column_names) != len(set(column_names)):
            raise ValueError(f"Duplicate column names in table {self.name}")

    def validate_primary_columns(self):
        for data_type in DataType:
            primary_columns = [
                col.source_name
                for col in self.columns
                if col.data_type == data_type and col.is_primary
            ]
            if len(primary_columns) > 1:
                raise ValueError(
                    f"Multiple primary columns for {data_type.value} in table {self.name}"
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
        """Validate file configuration after initialization."""
        if not self.tables:
            raise ValueError(
                f"File {self.name_pattern} must have at least one table defined"
            )

        # For CSV files, ensure only one table with empty name
        if self.file_type == FileType.CSV and len(self.tables) > 1:
            raise ValueError("CSV files can only have one table structure")
        if self.file_type == FileType.CSV and self.tables[0].name != "":
            raise ValueError("CSV file table name should be empty string")


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
        """Validate device format after initialization."""
        if not self.files:
            raise ValueError(
                f"Device format {self.name} must have at least one file defined"
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
