import pytest

from src.core.data_types import (
    ColumnMapping,
    ColumnRequirement,
    DataType,
    DeviceFormat,
    FileConfig,
    FileType,
    FormatValidationError,
    TableStructure,
    Unit,
)


# ------------------- ENUM TESTS ------------------- #
def test_filetype_enum_values():
    assert FileType.SQLITE.value == "sqlite"
    assert FileType.CSV.value == "csv"


def test_datatype_enum_auto_names():
    # auto() means values aren't stable, but names are
    assert DataType.CGM.name == "CGM"
    assert DataType.INSULIN.name == "INSULIN"


def test_unit_enum_values():
    assert Unit.MGDL.value == "mg/dL"
    assert Unit.UNITS.value == "U"


# ------------------- COLUMNMAPPING TESTS ------------------- #
def test_columnmapping_defaults():
    col = ColumnMapping(source_name="glucose")
    assert col.data_type is None
    assert col.unit is None
    assert col.requirement == ColumnRequirement.REQUIRED_WITH_DATA
    assert col.is_primary is True


def test_columnmapping_custom_values():
    col = ColumnMapping(
        source_name="glucose",
        data_type=DataType.CGM,
        unit=Unit.MGDL,
        requirement=ColumnRequirement.REQUIRED_NULLABLE,
        is_primary=False,
    )
    assert col.data_type == DataType.CGM
    assert col.unit == Unit.MGDL
    assert col.requirement == ColumnRequirement.REQUIRED_NULLABLE
    assert col.is_primary is False


# ------------------- TABLESTRUCTURE TESTS ------------------- #
def test_tablestructure_valid_initialization():
    col = ColumnMapping(source_name="glucose", data_type=DataType.CGM)
    table = TableStructure(name="readings", timestamp_column="timestamp", columns=[col])
    assert table.name == "readings"
    assert table.columns[0].source_name == "glucose"


def test_tablestructure_no_columns_raises():
    with pytest.raises(FormatValidationError):
        TableStructure(name="readings", timestamp_column="timestamp", columns=[])


def test_tablestructure_duplicate_source_names_raises():
    col1 = ColumnMapping(source_name="glucose", data_type=DataType.CGM)
    col2 = ColumnMapping(source_name="glucose", data_type=DataType.CGM)
    with pytest.raises(FormatValidationError):
        TableStructure(
            name="readings", timestamp_column="timestamp", columns=[col1, col2]
        )


def test_tablestructure_single_primary_per_datatype_valid():
    """Test that having one or zero primary columns per data type is valid."""
    col1 = ColumnMapping(source_name="glucose", data_type=DataType.CGM, is_primary=True)
    col2 = ColumnMapping(
        source_name="insulin", data_type=DataType.INSULIN, is_primary=True
    )
    col3 = ColumnMapping(
        source_name="raw_glucose", data_type=DataType.CGM, is_primary=False
    )
    # Should not raise - different data types can each have a primary
    table = TableStructure(
        name="readings", timestamp_column="timestamp", columns=[col1, col2, col3]
    )
    assert table.name == "readings"


def test_tablestructure_multiple_primary_for_same_datatype_raises():
    col1 = ColumnMapping(
        source_name="glucose1", data_type=DataType.CGM, is_primary=True
    )
    col2 = ColumnMapping(
        source_name="glucose2", data_type=DataType.CGM, is_primary=True
    )
    with pytest.raises(FormatValidationError):
        TableStructure(
            name="readings", timestamp_column="timestamp", columns=[col1, col2]
        )


def test_tablestructure_one_primary_one_non_primary_same_datatype_valid():
    """Test that having one primary and one non-primary of same data type is valid."""
    col1 = ColumnMapping(source_name="glucose", data_type=DataType.CGM, is_primary=True)
    col2 = ColumnMapping(
        source_name="raw_glucose", data_type=DataType.CGM, is_primary=False
    )
    # Should not raise - only one primary CGM column
    table = TableStructure(
        name="readings", timestamp_column="timestamp", columns=[col1, col2]
    )
    assert table.name == "readings"


# ------------------- FILECONFIG TESTS ------------------- #
def test_fileconfig_valid_initialization():
    col = ColumnMapping(source_name="glucose", data_type=DataType.CGM)
    table = TableStructure(name="readings", timestamp_column="timestamp", columns=[col])
    file_config = FileConfig(
        name_pattern="*.sqlite", file_type=FileType.SQLITE, tables=[table]
    )
    assert file_config.file_type == FileType.SQLITE


def test_fileconfig_csv_with_empty_name_valid():
    """Test that CSV files can have a table with an empty name (valid case)."""
    col = ColumnMapping(source_name="glucose", data_type=DataType.CGM)
    table = TableStructure(
        name="",  # Empty string is valid for CSV
        timestamp_column="timestamp",
        columns=[col],
    )

    # Should not raise - this is the correct way to configure CSV
    file_config = FileConfig(
        name_pattern="glucose.csv",
        file_type=FileType.CSV,
        tables=[table],
    )
    assert file_config.file_type == FileType.CSV


def test_fileconfig_no_tables_raises():
    with pytest.raises(FormatValidationError):
        FileConfig(name_pattern="*.sqlite", file_type=FileType.SQLITE, tables=[])


def test_fileconfig_csv_with_multiple_tables_raises():
    col = ColumnMapping(source_name="glucose", data_type=DataType.CGM)
    table = TableStructure(name="", timestamp_column="timestamp", columns=[col])

    with pytest.raises(FormatValidationError):
        FileConfig(
            name_pattern="glucose.csv",
            file_type=FileType.CSV,
            tables=[table, table],
        )


def test_fileconfig_csv_with_non_empty_name_raises():
    col = ColumnMapping(source_name="glucose", data_type=DataType.CGM)
    table = TableStructure(
        name="not_empty", timestamp_column="timestamp", columns=[col]
    )

    with pytest.raises(FormatValidationError):
        FileConfig(
            name_pattern="glucose.csv",
            file_type=FileType.CSV,
            tables=[table],
        )


# ------------------- DEVICEFORMAT TESTS ------------------- #
def test_deviceformat_valid():
    col = ColumnMapping(source_name="glucose", data_type=DataType.CGM)
    table = TableStructure(name="readings", timestamp_column="timestamp", columns=[col])
    file_config = FileConfig(
        name_pattern="*.sqlite", file_type=FileType.SQLITE, tables=[table]
    )
    device_format = DeviceFormat(name="my_device", files=[file_config])
    assert device_format.name == "my_device"


def test_deviceformat_no_files_raises():
    with pytest.raises(FormatValidationError):
        DeviceFormat(name="my_device", files=[])


# ------------------- __str__ TEST ------------------- #
def test_deviceformat_str_includes_primary_data_types():
    col1 = ColumnMapping(source_name="glucose", data_type=DataType.CGM)
    col2 = ColumnMapping(source_name="insulin", data_type=DataType.INSULIN)
    table = TableStructure(
        name="readings", timestamp_column="timestamp", columns=[col1, col2]
    )
    file_config = FileConfig(
        name_pattern="*.sqlite", file_type=FileType.SQLITE, tables=[table]
    )
    device_format = DeviceFormat(name="my_device", files=[file_config])

    output = str(device_format)
    assert "CGM" in output
    assert "INSULIN" in output


def test_deviceformat_str_excludes_non_primary_data_types():
    """Test that __str__ only includes primary columns in output."""
    col1 = ColumnMapping(source_name="glucose", data_type=DataType.CGM, is_primary=True)
    col2 = ColumnMapping(
        source_name="raw_glucose", data_type=DataType.BGM, is_primary=False
    )
    table = TableStructure(
        name="readings", timestamp_column="timestamp", columns=[col1, col2]
    )
    file_config = FileConfig(
        name_pattern="*.sqlite", file_type=FileType.SQLITE, tables=[table]
    )
    device_format = DeviceFormat(name="my_device", files=[file_config])

    output = str(device_format)
    assert "CGM" in output
    assert "BGM" not in output  # Should not appear because is_primary=False
