"""Format Registry for Diabetes Device Data Formats.

This module provides functionality to discover and load device format definitions
from the devices directory. It supports dynamic loading of formats and
maintains a registry of available formats for use in format detection.

The registry:
    - Recursively scans the devices directory
    - Validates format definitions
    - Provides access to available formats
    - Handles format loading errors gracefully

Example:
    >>> registry = FormatRegistry()
    >>> formats = registry.formats
    >>> xdrip_format = registry.get_format("xdrip_sqlite")
"""

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

from src.core.data_types import DataType, DeviceFormat, FileType
from src.core.exceptions import FileAccessError, FormatError, FormatValidationError

# Configure logging
logger = logging.getLogger(__name__)


class FormatRegistry:
    """Registry for device formats that dynamically loads from devices directory.

    The registry maintains a collection of device formats and provides methods to:
        - Load formats from the devices directory
        - Validate format definitions
        - Access registered formats
        - Filter formats by file type or data type

    Attributes:
        formats (List[DeviceFormat]): List of all registered formats

    Example:
        >>> registry = FormatRegistry()
        >>> sqlite_formats = registry.get_formats_by_type(FileType.SQLITE)
        >>> cgm_formats = registry.get_formats_with_data_type(DataType.CGM)
    """

    def __init__(self):
        """Initialize the format registry and load available formats."""
        self._formats: Dict[str, DeviceFormat] = {}
        self._load_formats()
        logger.debug("Initialized FormatRegistry with %d formats", len(self._formats))

    def _load_formats(self) -> None:
        """Load all format definitions from the devices directory structure.

        Raises:
            FileAccessError: If manufacturers directory cannot be accessed
            FormatError: If there's an error loading format files
        """
        try:
            manufacturers_dir = Path(__file__).parent / "devices"
            if not manufacturers_dir.exists():
                raise FileAccessError(
                    "Manufacturers directory not found",
                    details={"directory": str(manufacturers_dir)},
                )

            # Recursively find all Python files
            for format_file in manufacturers_dir.rglob("*.py"):
                if format_file.stem == "__init__":
                    continue

                try:
                    self._load_format_file(format_file)
                except FormatError as e:
                    logger.error(
                        "Error loading format file: %s Details: %s", str(e), e.details
                    )
                    continue

        except Exception as e:
            raise FormatError(
                "Failed to load formats", details={"error": str(e)}
            ) from e

    def _load_format_file(self, path: Path) -> None:
        """Load and process a single format definition file.

        Args:
            path: Path to the format definition file

        Raises:
            FormatError: If there's an error loading the file
        """
        try:
            module_name = f"devices.{path.parent.name}.{path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, path)

            if spec is None or spec.loader is None:
                raise FormatError(
                    "Failed to create module spec", details={"path": str(path)}
                )

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Find and validate DeviceFormat instances
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, DeviceFormat):
                    self._validate_and_register_format(attr, path)

        except Exception as e:
            raise FormatError(f"Error loading {path}", details={"error": str(e)}) from e

    def _validate_and_register_format(
        self, format_def: DeviceFormat, source_file: Path
    ) -> None:
        """Validate and register a format definition.

        Args:
            format_def: The format definition to validate and register
            source_file: Path to the source file (for error reporting)

        Raises:
            FormatValidationError: If the format fails validation
        """
        try:
            # Format name validation
            if not format_def.name:
                raise FormatValidationError(
                    "Format name cannot be empty",
                    details={"source_file": str(source_file)},
                )

            # File configuration validation
            if not format_def.files:
                raise FormatValidationError(
                    f"No files defined in format {format_def.name}",
                    details={
                        "format_name": format_def.name,
                        "source_file": str(source_file),
                    },
                )

            for config in format_def.files:
                if not config.tables:
                    raise FormatValidationError(
                        f"No tables defined in file {config.name_pattern}",
                        details={
                            "format_name": format_def.name,
                            "file_pattern": config.name_pattern,
                        },
                    )

            # Register the format
            format_key = f"{format_def.name}_{format_def.files[0].file_type.value}"
            if format_key in self._formats:
                logger.warning("Overwriting existing format: %s", format_key)
            self._formats[format_key] = format_def
            logger.debug("Registered format: %s from %s", format_key, source_file)

        except FormatValidationError as e:
            logger.error(
                "Validation failed for format in %s: %s Details: %s",
                source_file,
                str(e),
                e.details,
            )
            raise

    @property
    def formats(self) -> List[DeviceFormat]:
        """Get list of all registered formats.

        Returns:
            List of all registered DeviceFormat instances
        """
        return list(self._formats.values())

    def get_format(self, name: str) -> Optional[DeviceFormat]:
        """Get a specific format by name.

        Args:
            name: Name of the format to retrieve

        Returns:
            The requested DeviceFormat or None if not found
        """
        return self._formats.get(name)

    def get_formats_by_type(self, file_type: FileType) -> List[DeviceFormat]:
        """Get all formats that handle a specific file type.

        Args:
            file_type: The file type to filter by

        Returns:
            List of formats that support the specified file type
        """
        return [
            fmt
            for fmt in self._formats.values()
            if any(f.file_type == file_type for f in fmt.files)
        ]

    def get_formats_for_file(self, path: Path) -> List[DeviceFormat]:
        """Get all formats that could match this file based on extension.

        Args:
            path: Path to the file to check

        Returns:
            List of potential matching formats

        Example:
            >>> registry = FormatRegistry()
            >>> formats = registry.get_formats_for_file(Path("data.sqlite"))
            >>> print([f.name for f in formats])
            ['xdrip_sqlite', 'other_sqlite_format']
        """
        try:
            file_type = FileType(path.suffix.lower()[1:])
            return self.get_formats_by_type(file_type)
        except ValueError:
            logger.warning("Unsupported file type: %s", path.suffix)
            return []

    def get_formats_with_data_type(self, data_type: DataType) -> List[DeviceFormat]:
        """Get all formats that contain a specific data type.

        Args:
            data_type: The data type to filter by

        Returns:
            List of formats that contain the specified data type
        """
        formats = []
        for config_fmt in self._formats.values():
            for config in config_fmt.files:
                for config_table in config.tables:
                    if any(col.data_type == data_type for col in config_table.columns):
                        formats.append(config_fmt)
                        break
        return formats

    def get_available_data_types(self) -> Set[DataType]:
        """Get all data types available across all formats.

        Returns:
            Set of all available data types
        """
        types = set()
        for config_fmt in self._formats.values():
            for config in config_fmt.files:
                for config_table in config.tables:
                    for config_col in config_table.columns:
                        if config_col.data_type:
                            types.add(config_col.data_type)
        return types


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Test Format Registry with a data file"
    )
    parser.add_argument("file_path", type=str, help="Path to the data file to test")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    try:
        registry = FormatRegistry()
        file_path = Path(args.file_path)

        logger.info("Checking file: %s", file_path)
        matching_formats = registry.get_formats_for_file(file_path)

        if not matching_formats:
            logger.error("No matching formats found")
            sys.exit(1)

        for fmt in matching_formats:
            logger.info("\nFormat: %s", fmt.name)
            logger.info("Primary data types:")
            for dtype in registry.get_available_data_types():
                logger.info("  - %s", dtype)

            for file_config in fmt.files:
                logger.info("\nFile pattern: %s", file_config.name_pattern)
                for table in file_config.tables:
                    logger.info("  Table: %s", table.name)
                    logger.info("    Timestamp column: %s", table.timestamp_column)
                    for col in table.columns:
                        if col.data_type:
                            # pylint: disable=invalid-name
                            status_of_primary = (
                                "primary" if col.is_primary else "secondary"
                            )
                            logger.info(
                                "    Column: %s (%s - %s)",
                                col.source_name,
                                col.data_type,
                                status_of_primary,
                            )
                        else:
                            logger.info(
                                "    Column: %s (validation only)", col.source_name
                            )

    except FormatValidationError as e:
        logger.error("Error: %s", str(e))
        sys.exit(1)
