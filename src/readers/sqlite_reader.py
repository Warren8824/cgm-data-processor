"""SQLite Reader for confirmed configuration with sqlite FileType"""

import logging
import sys
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
from pandas.errors import EmptyDataError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from .base import BaseReader, ColumnRequirement, FileConfig, TableData, TableStructure

logger = logging.getLogger(__name__)


class TableReadError(Exception):
    """Base Exception for unexpected read errors"""


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
                raise ValueError(f"Invalid table name: {table_structure.name}")

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
                    raise ValueError(f"Invalid column name: {col}")

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

        except ValueError as e:
            # Handle specific ValueErrors such as invalid table or column names
            logger.error("ValueError: %s", e)
            return None
        except SQLAlchemyError as e:
            # Handle any database-related errors (e.g., connection, query execution)
            logger.error(
                "SQLAlchemyError processing table %s: %s", table_structure.name, e
            )
            return None
        except EmptyDataError as e:
            # Handle case where there is no data in the result set
            logger.error(
                "EmptyDataError processing table %s: %s", table_structure.name, e
            )
            return None
        except TableReadError as e:
            # Catch any unexpected errors
            logger.error(
                "Unexpected error processing table %s: %s", table_structure.name, e
            )
            return None


if __name__ == "__main__":
    # Example usage
    try:
        from src.file_parser.format_detector import FormatDetectionError, FormatDetector
        from src.file_parser.format_registry import FormatRegistry

        file_path = Path("data/20240928-130349.sqlite")
        logger.debug("\nAnalyzing file: %s", file_path)

        # Load registered formats and detect any matches
        registry = FormatRegistry()
        detector = FormatDetector(registry)

        detected_format, error, validation_results = detector.detect_format(file_path)
    except FormatDetectionError as e:
        logger.error("Error: %s", str(e))
        sys.exit(1)

    # Function to process SQLite file
    def process_sqlite_file(
        path: Path, fmt: detected_format
    ) -> Dict[str, pd.DataFrame]:
        """Process SQLite file according to detected format."""
        try:
            # Create the SQLiteReader object using the detected format
            reader = SQLiteReader(path, fmt.files[0])
            table_data = reader.read_all_tables()

            # Return DataFrames, filtering out tables with missing critical columns
            return {
                name: data.dataframe
                for name, data in table_data.items()
                if not data.missing_required_columns
            }

        except FormatDetectionError as e:
            logger.error("Failed to process SQLite file %s: %s", path, e)
            return {}

    # Run the file processing
    result = process_sqlite_file(file_path, detected_format)

    # Display results
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
