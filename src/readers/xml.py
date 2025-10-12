"""XML Reader for confirmed configuration with XML FileType.

This module provides XML file reading capabilities for the data processing system,
supporting multiple tables per file through XPath queries and handling both
attribute and element-based data storage.
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from src.core.data_types import ColumnRequirement, FileConfig, FileType, TableStructure
from src.core.exceptions import (
    DataExistsError,
    DataProcessingError,
    DataValidationError,
    ReaderError,
)

from .base import BaseReader, TableData

logger = logging.getLogger(__name__)


@BaseReader.register(FileType.XML)
class XMLReader(BaseReader):
    """Reads and processes XML files according to the provided format configuration."""

    def __init__(self, path: Path, file_config: FileConfig):
        super().__init__(path, file_config)
        self._tree = None
        self._root = None

    def _cleanup(self):
        """Cleanup any held resources."""
        self._tree = None
        self._root = None

    def _init_xml(self):
        """initialise XML parsing if not already done."""
        if self._root is None:
            try:
                self._tree = ET.parse(self.file_path)
                self._root = self._tree.getroot()
            except ET.ParseError as e:
                raise DataExistsError(f"Failed to parse XML file: {e}") from e
            except Exception as e:
                raise DataExistsError(f"Error reading XML file: {e}") from e

    @staticmethod
    def _extract_value(element: ET.Element, column: str) -> str:
        """Extract value from XML element, checking both attributes and text.

        Args:
            element: XML element to extract from
            column: Column name to look for

        Returns:
            Value from attribute or element text
        """
        # Check attributes first
        if column in element.attrib:
            return element.attrib[column]

        # Then check child elements
        child = element.find(column)
        if child is not None:
            return child.text if child.text else ""

        return ""

    def read_table(self, table_structure: TableStructure) -> Optional[TableData]:
        """Read and process a single table according to its structure.

        For XML files, each table is expected to be contained within elements
        matching the table name or a configured xpath.
        """
        try:
            self._init_xml()

            # Get required columns
            columns_to_read = [
                col.source_name
                for col in table_structure.columns
                if col.requirement != ColumnRequirement.CONFIRMATION_ONLY
            ]
            columns_to_read.append(table_structure.timestamp_column)

            # Find all elements for this table
            table_elements = self._root.findall(f".//{table_structure.name}")
            if not table_elements:
                logger.error("No elements found for table: %s", table_structure.name)
                return None

            # Extract data for each column
            data: Dict[str, List[str]] = {col: [] for col in columns_to_read}

            for element in table_elements:
                for column in columns_to_read:
                    value = self._extract_value(element, column)
                    data[column].append(value)

            # Convert to DataFrame
            df = pd.DataFrame(data)

            if df.empty:
                raise DataExistsError(f"No data found in table {table_structure.name}")

            # Process timestamps
            df, fmt = self._convert_timestamp_to_utc(
                df, table_structure.timestamp_column
            )

            # Validate required data
            missing_required = self._validate_required_data(df, table_structure.columns)

            return TableData(
                name=table_structure.name,
                dataframe=df,
                missing_required_columns=missing_required,
                timestamp_type=fmt,
            )

        except DataValidationError as e:
            logger.error("Validation error: %s", e)
            return None
        except DataExistsError as e:
            logger.error("No data error: %s", e)
            return None
        except DataProcessingError as e:
            logger.error("Processing error: %s", e)
            return None
        except ReaderError as e:
            logger.error("Unexpected error processing XML: %s", e)
            return None
