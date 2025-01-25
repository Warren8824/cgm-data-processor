"""SQLite Reader for confirmed configuration with sqlite FileType

This module provides SQLite file reading capabilities for the data processing system.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from src.core.exceptions import (
    DataExistsError,
    DataProcessingError,
    DataValidationError,
    ProcessingError,
    ReaderError,
)

from .base import (
    BaseReader,
    ColumnRequirement,
    FileConfig,
    FileType,
    TableData,
    TableStructure,
)

logger = logging.getLogger(__name__)


@BaseReader.register(FileType.SQLITE)
class SQLiteReader(BaseReader):
    """Reads and processes SQLite files according to the provided format configuration."""

    def __init__(self, path: Path, file_config: FileConfig):
        super().__init__(path, file_config)
        self._engine = None

    @property
    def engine(self):
        """Lazy initialization of database engine."""
        if self._engine is None:
            self._engine = create_engine(f"sqlite:///{self.file_path}")
        return self._engine

    def _cleanup(self):
        """Cleanup database connections."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def read_table(self, table_structure: TableStructure) -> Optional[TableData]:
        """Read and process a single table according to its structure."""
        try:
            # Validate identifiers
            if not self._validate_identifier(table_structure.name):
                raise DataValidationError(f"Invalid table name: {table_structure.name}")

            # Read only needed columns
            columns_to_read = [
                col.source_name
                for col in table_structure.columns
                if col.requirement != ColumnRequirement.CONFIRMATION_ONLY
            ]
            columns_to_read.append(table_structure.timestamp_column)

            # Validate column names
            for col in columns_to_read:
                if not self._validate_identifier(col):
                    raise DataValidationError(f"Invalid column name: {col}")

            # Create query with quoted identifiers for SQLite
            quoted_columns = [f'"{col}"' for col in columns_to_read]
            query = text(
                f"""
                SELECT {', '.join(quoted_columns)}
                FROM "{table_structure.name}"
                ORDER BY "{table_structure.timestamp_column}"
            """
            )

            # Execute query within connection context
            with self.engine.connect() as conn:
                df = pd.read_sql_query(query, conn)

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
            # Handle specific ValueErrors such as invalid table or column names
            logger.error("ValueError: %s", e)
            return None
        except SQLAlchemyError as e:
            # Handle any database-related errors (e.g., connection, query execution)
            logger.error(
                "SQLAlchemyError processing table %s: %s", table_structure.name, e
            )
            return None
        except DataExistsError as e:
            # Handle case where there is no data in the result set
            logger.error(
                "EmptyDataError processing table %s: %s", table_structure.name, e
            )
            return None
        except ReaderError as e:
            # Catch any unexpected errors
            logger.error(
                "Unexpected error processing table %s: %s", table_structure.name, e
            )
            return None


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
        from src.core.exceptions import FormatDetectionError
        from src.core.format_registry import FormatRegistry
        from src.file_parser.format_detector import FormatDetector
        from src.readers.base import BaseReader

        file_path = Path(args.file_path)

        # Check if file exists and is accessible
        if not file_path.exists():
            logger.error("File not found: %s", file_path)
            sys.exit(1)
        if not file_path.is_file():
            logger.error("Path is not a file: %s", file_path)
            sys.exit(1)

        logger.debug("\nAnalyzing file: %s", file_path)

        # Load registered formats and detect any matches
        registry = FormatRegistry()
        detector = FormatDetector(registry)

        try:
            detected_format, error, validation_results = detector.detect_format(
                file_path
            )
        except FormatDetectionError as e:
            logger.error("Format detection error: %s", str(e))
            sys.exit(1)

        if detected_format is None:
            logger.error("No valid format detected for file")
            sys.exit(1)

        # Process file using automatic reader selection
        try:
            reader = BaseReader.get_reader_for_format(detected_format, file_path)
            with reader:  # Use context manager for proper resource cleanup
                table_data = reader.read_all_tables()

                # Filter out tables with missing critical columns
                result = {
                    name: data.dataframe
                    for name, data in table_data.items()
                    if not data.missing_required_columns
                }

        except (DataProcessingError, ReaderError) as exc:
            logger.error("Failed to process file %s: %s", file_path, str(exc))
            if args.debug:
                logger.exception("Debug traceback:")
            sys.exit(1)

        # Display results
        if not result:
            logger.error("No valid data found in file")
            sys.exit(1)

        if "BgReadings" in result:
            print("CGM Data Info:")
            result["BgReadings"].info()
            print("\nCGM Data Descriptive Stats:")
            print(result["BgReadings"].describe())

        if "Treatments" in result:
            print("Treatment Data Info:")
            result["Treatments"].info()
            print("\nTreatment Data Descriptive Stats:")
            print(result["Treatments"].describe())

    except ProcessingError as e:
        logger.error("Unexpected error occurred: %s", str(e))
        if args.debug:
            logger.exception("Debug traceback:")
        sys.exit(1)
