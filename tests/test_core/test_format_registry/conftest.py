"""Format registry specific test fixtures.

Provides fixtures for:
- Format definitions (valid, complex, csv)
- Invalid format configurations
- File system mocking
- Format file creation
"""

# pylint: disable=redefined-outer-name
import pytest

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


@pytest.fixture
def valid_format():
    """Create minimal valid device format."""
    return DeviceFormat(
        name="test_device",
        files=[
            FileConfig(
                name_pattern="*.sqlite",
                file_type=FileType.SQLITE,
                tables=[
                    TableStructure(
                        name="readings",
                        timestamp_column="timestamp",
                        columns=[
                            ColumnMapping(
                                source_name="value",
                                data_type=DataType.CGM,
                                unit=Unit.MGDL,
                            )
                        ],
                    )
                ],
            )
        ],
    )


@pytest.fixture
def complex_format():
    """Create format with multiple data types and tables."""
    return DeviceFormat(
        name="complex_device",
        files=[
            FileConfig(
                name_pattern="*.sqlite",
                file_type=FileType.SQLITE,
                tables=[
                    TableStructure(
                        name="cgm_data",
                        timestamp_column="timestamp",
                        columns=[
                            ColumnMapping(
                                source_name="glucose",
                                data_type=DataType.CGM,
                                unit=Unit.MGDL,
                            ),
                            ColumnMapping(
                                source_name="raw",
                                data_type=DataType.CGM,
                                is_primary=False,
                            ),
                        ],
                    ),
                    TableStructure(
                        name="treatments",
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
                        ],
                    ),
                ],
            )
        ],
    )


@pytest.fixture
def csv_format():
    """Create valid CSV format for testing."""
    return DeviceFormat(
        name="csv_device",
        files=[
            FileConfig(
                name_pattern="*.csv",
                file_type=FileType.CSV,
                tables=[
                    TableStructure(
                        name="",  # CSV files should have empty table name
                        timestamp_column="time",
                        columns=[
                            ColumnMapping(
                                source_name="glucose",
                                data_type=DataType.CGM,
                                unit=Unit.MGDL,
                            ),
                        ],
                    )
                ],
            )
        ],
    )


@pytest.fixture
def invalid_formats():
    """Collection of invalid format configurations for testing validation."""
    return {
        "empty_name": DeviceFormat(
            name="",
            files=[
                FileConfig(
                    name_pattern="*.sqlite",
                    file_type=FileType.SQLITE,
                    tables=[
                        TableStructure(
                            name="readings",
                            timestamp_column="timestamp",
                            columns=[
                                ColumnMapping(
                                    source_name="value",
                                    data_type=DataType.CGM,
                                    unit=Unit.MGDL,
                                ),
                            ],
                        )
                    ],
                )
            ],
        ),
        "no_files": DeviceFormat(
            name="no_files",
            files=[],
        ),
        "duplicate_columns": DeviceFormat(
            name="duplicate_cols",
            files=[
                FileConfig(
                    name_pattern="*.sqlite",
                    file_type=FileType.SQLITE,
                    tables=[
                        TableStructure(
                            name="readings",
                            timestamp_column="timestamp",
                            columns=[
                                ColumnMapping(
                                    source_name="value",
                                    data_type=DataType.CGM,
                                    unit=Unit.MGDL,
                                ),
                                ColumnMapping(
                                    source_name="value",
                                    data_type=DataType.CGM,
                                    unit=Unit.MGDL,
                                ),
                            ],
                        )
                    ],
                )
            ],
        ),
        "multiple_primary": DeviceFormat(
            name="multi_primary",
            files=[
                FileConfig(
                    name_pattern="*.sqlite",
                    file_type=FileType.SQLITE,
                    tables=[
                        TableStructure(
                            name="readings",
                            timestamp_column="timestamp",
                            columns=[
                                ColumnMapping(
                                    source_name="value1",
                                    data_type=DataType.CGM,
                                    unit=Unit.MGDL,
                                ),
                                ColumnMapping(
                                    source_name="value2",
                                    data_type=DataType.CGM,
                                    unit=Unit.MGDL,
                                ),
                            ],
                        )
                    ],
                )
            ],
        ),
        "csv_with_tablename": DeviceFormat(
            name="bad_csv",
            files=[
                FileConfig(
                    name_pattern="*.csv",
                    file_type=FileType.CSV,
                    tables=[
                        TableStructure(
                            name="should_be_empty",
                            timestamp_column="timestamp",
                            columns=[
                                ColumnMapping(
                                    source_name="value",
                                    data_type=DataType.CGM,
                                    unit=Unit.MGDL,
                                ),
                            ],
                        )
                    ],
                )
            ],
        ),
    }


@pytest.fixture
def mock_file_system(mocker, device_dir):
    """Set up mocked filesystem with devices directory."""
    mocker.patch("src.core.format_registry.Path.parent", return_value=device_dir.parent)
    return device_dir


@pytest.fixture
def sample_format_file(mock_file_system, valid_format):
    """Create sample format file in the test directory."""
    manufacturer_dir = mock_file_system / "test_manufacturer"
    manufacturer_dir.mkdir()

    format_file = manufacturer_dir / "test_format.py"
    format_file.write_text(
        f"""
from src.core.data_types import *

TEST_FORMAT = {valid_format!r}
"""
    )
    return format_file


@pytest.fixture
def populated_registry(mock_file_system, valid_format, complex_format, csv_format):
    """Create registry with multiple formats for query testing."""
    for i, fmt in enumerate([valid_format, complex_format, csv_format]):
        format_dir = mock_file_system / f"manufacturer_{i}"
        format_dir.mkdir()
        format_file = format_dir / f"format_{i}.py"
        format_file.write_text(
            f"""
from src.core.data_types import *

FORMAT = {fmt!r}
"""
        )
    return mock_file_system


@pytest.fixture
def invalid_python_file(mock_file_system):
    """Create syntactically invalid Python file."""
    file_path = mock_file_system / "invalid.py"
    file_path.write_text("This is not valid Python { [ )")
    return file_path


@pytest.fixture
def module_import_error_file(mock_file_system):
    """Create file that raises ImportError."""
    file_path = mock_file_system / "import_error.py"
    file_path.write_text(
        """
from nonexistent_module import something
FORMAT = None
"""
    )
    return file_path


@pytest.fixture
def mixed_data_types_format():
    """Format with mixed data types for complex queries."""
    return DeviceFormat(
        name="mixed_types",
        files=[
            FileConfig(
                name_pattern="*.sqlite",
                file_type=FileType.SQLITE,
                tables=[
                    TableStructure(
                        name="readings",
                        timestamp_column="timestamp",
                        columns=[
                            ColumnMapping(
                                source_name="glucose",
                                data_type=DataType.CGM,
                                unit=Unit.MGDL,
                            ),
                            ColumnMapping(
                                source_name="notes",
                                data_type=DataType.NOTES,
                                requirement=ColumnRequirement.REQUIRED_NULLABLE,
                            ),
                        ],
                    ),
                ],
            ),
            FileConfig(
                name_pattern="treatments.csv",
                file_type=FileType.CSV,
                tables=[
                    TableStructure(
                        name="",
                        timestamp_column="time",
                        columns=[
                            ColumnMapping(
                                source_name="insulin",
                                data_type=DataType.INSULIN,
                                unit=Unit.UNITS,
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
