"""Format detection for diabetes device data files.

This module provides functionality to detect device formats by examining file structure.
It validates only the presence of required tables and columns, without checking data content.
"""

import json
import logging
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import create_engine, inspect

from src.core.data_types import ColumnRequirement, DeviceFormat, FileType
from src.core.exceptions import (
    FileAccessError,
    FormatDetectionError,
    FormatValidationError,
)
from src.file_parser.format_registry import FormatRegistry

logger = logging.getLogger(__name__)


class ValidationResult:
    """Container for structure validation results."""

    def __init__(self):
        self.missing_tables: List[str] = []
        self.missing_columns: Dict[str, List[str]] = {}  # table: [columns]

    def has_errors(self) -> bool:
        """Check if any validation errors exist."""
        return bool(self.missing_tables or self.missing_columns)

    def __str__(self) -> str:
        """Format validation errors as string."""
        errors = []
        if self.missing_tables:
            errors.append(f"Missing tables: {', '.join(self.missing_tables)}")
        if self.missing_columns:
            for current_table, columns in self.missing_columns.items():
                errors.append(
                    f"Missing required columns in {current_table}: {', '.join(columns)}"
                )
        return "\n".join(errors)


class FormatDetector:
    """Detects device formats by examining file structure."""

    def __init__(self, format_registry: FormatRegistry):
        """Initialize detector with format registry."""
        self._registry = format_registry

    def detect_format(
        self, path: Path
    ) -> Tuple[Optional[DeviceFormat], Optional[str], Dict[str, ValidationResult]]:
        """Detect format of provided file.

        Args:
            file_path: Path to the file to check

        Returns:
            Tuple containing:
                - Matched format (or None)
                - Error message (or None)
                - Dictionary of validation results per format tried

        Example:
            >>> detector = FormatDetector(registry)
            >>> fmt, error, results = detector.detect_format(Path("data.sqlite"))
            >>> if fmt:
            ...     print(f"Matched format: {fmt.name}")
            ... else:
            ...     print(f"No match: {error}")
        """
        logger.debug("Starting format detection for: %s", path)
        val_results = {}

        try:
            # Validate file exists and is readable
            if not self._validate_file_exists(path):
                return None, f"File not found or not accessible: {path}", {}

            # Get potential formats based on file extension
            potential_formats = self._registry.get_formats_for_file(path)
            if not potential_formats:
                return None, f"No formats available for {path.suffix} files", {}

            # Try each format
            for fmt in potential_formats:
                try:
                    val_test_result = ValidationResult()
                    if self._validate_format(path, fmt, val_test_result):
                        logger.debug("Successfully matched format: %s", fmt.name)
                        return fmt, None, val_results
                    val_results[fmt.name] = val_test_result
                except FormatValidationError as e:
                    logger.debug("Error validating format %s: %s", fmt.name, str(e))
                    continue

            return None, "No matching format found", val_results

        except FileAccessError as e:
            logger.error("Unexpected error during format detection: %s", str(e))
            return None, f"Detection error: {str(e)}", {}

    def _validate_file_exists(self, path: Path) -> bool:
        """Validate file exists and is accessible."""
        try:
            return path.exists() and path.is_file()
        except Exception as e:
            raise FileAccessError(f"Error occurred: {str(e)}") from e

    def _validate_format(
        self, path: Path, fmt: DeviceFormat, validation_result: ValidationResult
    ) -> bool:
        """Validate if file matches format definition."""
        for config in fmt.files:
            validator = self._get_validator(config.file_type)
            if validator is None:
                logger.warning("No validator available for %s", config.file_type.value)
                return False
            try:
                if not validator(path, config, validation_result):
                    return False
            except FormatValidationError as e:
                logger.debug("Validation failed: %s", {str(e)})
                return False
        return True

    def _get_validator(self, file_type: FileType):
        """Get appropriate validation function for file type."""
        validators = {
            FileType.SQLITE: self._validate_sqlite,
            FileType.CSV: self._validate_csv,
            FileType.JSON: self._validate_json,
            FileType.XML: self._validate_xml,
        }
        return validators.get(file_type)

    def _validate_sqlite(
        self, path: Path, config, val_result: ValidationResult
    ) -> bool:
        """Validate SQLite file structure."""
        try:
            engine = create_engine(f"sqlite:///{path}")
            inspector = inspect(engine)

            # Get all tables (case sensitive)
            actual_tables = {name: name for name in inspector.get_table_names()}

            # Check each required table
            for required_table in config.tables:
                table_name = required_table.name
                if table_name not in actual_tables:
                    val_result.missing_tables.append(required_table.name)
                    continue

                # Check columns
                columns = inspector.get_columns(table_name)
                column_names = {col["name"] for col in columns}

                # Check required columns exist in file
                required_columns = {
                    col.source_name
                    for col in required_table.columns
                    if col.requirement != ColumnRequirement.OPTIONAL
                }
                missing = required_columns - column_names
                if missing:
                    val_result.missing_columns[required_table.name] = [
                        col.source_name
                        for col in required_table.columns
                        if col.requirement != ColumnRequirement.OPTIONAL
                        and col.source_name in missing
                    ]

            return not val_result.has_errors()

        except FormatValidationError as e:
            logger.debug("SQLite validation error: %s", str(e))
            return False

    def _validate_csv(self, path: Path, config, val_result: ValidationResult) -> bool:
        """Validate CSV file structure."""
        try:
            # Read CSV headers only
            df = pd.read_csv(path, nrows=0)
            columns = {col.lower() for col in df.columns}

            # CSV should have exactly one table
            csv_table = config.tables[0]

            # Check required columns
            required_columns = {
                col.source_name.lower() for col in csv_table.columns if col.required
            }
            missing = required_columns - columns
            if missing:
                val_result.missing_columns[""] = [
                    col
                    for col in csv_table.columns
                    if col.required and col.source_name.lower() in missing
                ]

            return not val_result.has_errors()

        except FormatValidationError as e:
            logger.debug("CSV validation error: %s", str(e))
            return False

    def _validate_json(self, path: Path, config, val_result: ValidationResult) -> bool:
        """Validate JSON file structure."""
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            for json_table in config.tables:
                if isinstance(data, list):
                    if not data:
                        val_result.missing_tables.append(json_table.name)
                        continue
                    record = data[0]
                else:
                    if json_table.name not in data:
                        val_result.missing_tables.append(json_table.name)
                        continue
                    record = (
                        data[json_table.name][0]
                        if isinstance(data[json_table.name], list)
                        else data[json_table.name]
                    )

                # Check required fields
                fields = {k.lower() for k in record.keys()}
                required_fields = {
                    col.source_name.lower()
                    for col in json_table.columns
                    if col.required
                }
                missing = required_fields - fields
                if missing:
                    val_result.missing_columns[json_table.name] = [
                        col
                        for col in json_table.columns
                        if col.required and col.source_name.lower() in missing
                    ]

            return not val_result.has_errors()

        except FormatValidationError as e:
            logger.debug("JSON validation error: %s", str(e))
            return False

    def _validate_xml(self, path: Path, config, val_result: ValidationResult) -> bool:
        """Validate XML file structure."""
        try:
            tree = ET.parse(path)
            root = tree.getroot()

            for xml_table in config.tables:
                elements = root.findall(f".//{xml_table.name}")
                if not elements:
                    val_result.missing_tables.append(xml_table.name)
                    continue

                # Check first element
                element = elements[0]
                fields = set()
                fields.update(element.attrib.keys())
                fields.update(child.tag for child in element)
                fields = {f.lower() for f in fields}

                required_fields = {
                    col.source_name.lower() for col in xml_table.columns if col.required
                }
                missing = required_fields - fields
                if missing:
                    val_result.missing_columns[xml_table.name] = [
                        col
                        for col in xml_table.columns
                        if col.required and col.source_name.lower() in missing
                    ]

            return not val_result.has_errors()

        except FormatValidationError as e:
            logger.debug("XML validation error: %s", str(e))
            return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Diabetes Data Format Detection Tool")
    parser.add_argument("file_path", type=str, help="Path to the file to analyze")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(message)s",
    )

    try:
        file_path = Path(args.file_path)
        logger.debug("\nAnalyzing file: %s", file_path)

        registry = FormatRegistry()
        detector = FormatDetector(registry)

        detected_format, error, validation_results = detector.detect_format(file_path)

        if detected_format:
            logger.info("\n✓ Format detected: %s", detected_format.name)
            logger.info("\nFormat specification:")
            for file_config in detected_format.files:
                logger.info("  File type: %s", file_config.file_type.value)
                for table in file_config.tables:
                    logger.info("  Table: %s", table.name)
                    logger.info("    Column Requirements:")
                    for col in table.columns:
                        logger.info(
                            "      %s - %s", col.source_name, col.requirement.name
                        )
        else:
            logger.error("\n✗ Format detection failed: %s", error)
            if validation_results:
                for format_name, result in validation_results.items():
                    if result.has_errors():
                        logger.info("\nValidation failures for %s:", format_name)
                        logger.info(str(result))

    except FormatDetectionError as e:
        logger.error("Error: %s", str(e))
        if args.debug:
            logger.exception("Detailed error:")
        sys.exit(1)
