Contributing device formats — detailed guide

This document explains exactly how to add or update device format definitions for
cgm-data-processor. It covers how formats are discovered, validated, and used at
runtime and by the format detector. Follow this carefully when adding CSV or
SQLite formats so they pass validation and work with the readers.

Contents
- Format discovery (FormatRegistry)
- Format keys and naming
- CSV format specifics (TableStructure, timestamp_column, header_row)
- SQLite format specifics (table names, quoted identifiers)
- Timestamp handling and detection
- Examples (LibreView CSV, XDrip SQLite) — copy/paste-ready
- Tests and PR checklist

Format discovery (FormatRegistry)

- The registry is implemented in `src/core/format_registry.py`.
- At startup the registry recursively imports every `.py` under `src/core/devices/`.
  - Files named `__init__.py` are ignored.
  - Each imported module is inspected for `DeviceFormat` instances. Any
    instance found is validated and registered.
- Registered formats are stored under a key: `format_name + '_' + file_type.value`.
  - Example: `xdrip_sqlite_sqlite` for the `xdrip_sqlite` format whose first file
    has `file_type=FileType.SQLITE`.
- Keep device modules declarative (data-only). Import-time side-effects will run
  during registry loading and may break CI or CLI tools.

Format key and API

- Use `FormatRegistry()` to access formats programmatically.
  - `registry.formats` returns all registered `DeviceFormat` objects.
  - `registry.get_format(name)` returns the format registered under `name`.
  - `registry.get_formats_for_file(path)` filters formats by the file extension
    (maps extension to `FileType`).
  - `registry.get_formats_with_data_type(DataType.CGM)` returns formats that
    declare that data type.

Format detection (FormatDetector)

- Implemented in `src/file_parser/format_detector.py`.
- Detection steps:
  1. Ensure file exists.
  2. Get potential formats for the file extension via `FormatRegistry.get_formats_for_file()`.
  3. For each potential `DeviceFormat`, call a validator based on `FileType`.
  4. Validator checks the presence of required tables/columns (case-insensitive
     normalisation for CSV/JSON/XML) and returns a `ValidationResult`.
  5. First format that passes validation is chosen.
- If no header_row is provided for a CSV format, the detector reads the first
  4 rows and treats the first row that contains all required columns as the
  header.

CSV formats (concrete rules)

- `FileConfig` for CSV must have exactly one `TableStructure`.
- The table's `name` MUST be an empty string (`""`). This is enforced by
  `FileConfig.__post_init__`.
- `TableStructure.timestamp_column` is REQUIRED. The CSV reader will try to
  convert this column to UTC datetimes and set it as the DataFrame index.
- `TableStructure.header_row` is optional and is a 0-based index. If provided,
  the CSV reader will read the file and skip rows up to `header_row`, treating
  that row as the header. If not provided, detection tries to find a header row
  within the first 4 rows.
- Column names in `ColumnMapping.source_name` must match CSV headers after
  normalization (strip whitespace). The detector and reader compare headers in
  lower-case when auto-detecting, but the reader uses the exact header strings
  when selecting columns after reading (it strips whitespace but keeps case).
- Use `ColumnRequirement` to control required fields:
  - `CONFIRMATION_ONLY`: used to assert presence but not loaded into DataFrame
  - `REQUIRED_WITH_DATA`: must exist and contain data
  - `REQUIRED_NULLABLE`: must exist but may be all-null
  - `OPTIONAL`: not required

CSV example (LibreView — real example in repo)

See `src/core/devices/libreview/csv.py` in the repository. Key points:
- `header_row=1` means skip row 0 and treat row 1 as header.
- Timestamp column is `Device Timestamp`.
- Uses `ColumnRequirement.CONFIRMATION_ONLY` for device ID columns.

SQLite formats (concrete rules)

- Each `TableStructure.name` is used as the exact (case-sensitive) table name in
  the SQLite file. The SQLite reader validates the identifier using
  `BaseReader._validate_identifier` (alphanumeric, underscore, dot allowed).
- `TableStructure.timestamp_column` is REQUIRED.
- The reader constructs a SQL query using quoted identifiers (double quotes) to
  read only the required columns and orders by the timestamp column.
- Column names are matched exactly (case-sensitive) against `inspector.get_columns(table_name)` during detection.

Timestamp handling

- The BaseReader implements a deterministic timestamp detector (`detect_timestamp_format`) that:
  - samples up to 50 non-null values
  - detects numeric epochs (seconds vs milliseconds)
  - looks for ISO-like strings (T, Z, +/- offsets)
  - tries a short list of explicit formats
  - falls back to pandas inference if needed
- If detection returns UNKNOWN the reader raises `TimestampProcessingError`.
- Epochs are handled (unit 's' for seconds, 'ms' for milliseconds) and parsed
  to timezone-aware UTC datetimes. If parsed datetimes are naive they are
  localized to UTC.

Example format definitions (copy/paste)

- XDrip SQLite (already in repo): `src/core/devices/xdrip/sqlite.py`

```py
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
                TableStructure(
                    name="BgReadings",
                    timestamp_column="timestamp",
                    columns=[
                        ColumnMapping(source_name="calculated_value", data_type=DataType.CGM, unit=Unit.MGDL),
                        ColumnMapping(source_name="raw_data", data_type=DataType.CGM, is_primary=False),
                    ],
                ),
                TableStructure(
                    name="Treatments",
                    timestamp_column="timestamp",
                    columns=[
                        ColumnMapping(source_name="insulin", data_type=DataType.INSULIN, unit=Unit.UNITS),
                        ColumnMapping(source_name="insulinJSON", data_type=DataType.INSULIN_META, requirement=ColumnRequirement.REQUIRED_NULLABLE),
                        ColumnMapping(source_name="carbs", data_type=DataType.CARBS, unit=Unit.GRAMS),
                        ColumnMapping(source_name="notes", data_type=DataType.NOTES, requirement=ColumnRequirement.REQUIRED_NULLABLE),
                    ],
                ),
            ],
        )
    ],
)
```

- LibreView CSV (already in repo): `src/core/devices/libreview/csv.py`

```py
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
                    name="",
                    timestamp_column="Device Timestamp",
                    header_row=1,
                    columns=[
                        ColumnMapping(source_name="Device", requirement=ColumnRequirement.CONFIRMATION_ONLY),
                        ColumnMapping(source_name="Serial Number", requirement=ColumnRequirement.CONFIRMATION_ONLY),
                        ColumnMapping(source_name="Historic Glucose mmol/L", data_type=DataType.CGM, unit=Unit.MMOL),
                        ColumnMapping(source_name="Scan Glucose mmol/L", data_type=DataType.CGM, unit=Unit.MMOL, is_primary=False),
                        ColumnMapping(source_name="Strip Glucose mmol/L", data_type=DataType.BGM, unit=Unit.MMOL, requirement=ColumnRequirement.REQUIRED_NULLABLE),
                        ColumnMapping(source_name="Rapid-Acting Insulin (units)", data_type=DataType.INSULIN, unit=Unit.UNITS, requirement=ColumnRequirement.REQUIRED_NULLABLE),
                        ColumnMapping(source_name="Carbohydrates (grams)", data_type=DataType.CARBS, unit=Unit.GRAMS, requirement=ColumnRequirement.REQUIRED_NULLABLE),
                        ColumnMapping(source_name="Notes", data_type=DataType.NOTES, requirement=ColumnRequirement.REQUIRED_NULLABLE),
                    ],
                ),
            ],
        )
    ],
)
```

Testing & PR checklist

Before opening a PR:

- Ensure your device module has no runtime side-effects — the registry imports it.
- Include at least one sample file under `tests/data/sample_formats/<vendor>/` that matches your `name_pattern`.
- Add a unit test in `tests/test_file_parser/` that uses the FormatDetector to assert your sample file is detected and validated.
- Run tests locally with Poetry (`poetry install --with dev && poetry run pytest -q`).
- In the PR description include:
  - `name_pattern` used
  - example file path(s)
  - `timestamp_column` used and whether epoch/ISO
  - whether `header_row` is non-default and its 0-based index
  - note if a new reader was required (CSV/SQLite/JSON/XML)

If you want, give me a vendor name and a small CSV header + 3 rows and I will scaffold:
- `src/core/devices/<vendor>/csv.py` (DeviceFormat)
- `tests/data/sample_formats/<vendor>/sample.csv`
- `tests/test_file_parser/test_<vendor>_detection.py`

I will then run the test suite and report results.
