"""Command line interface for diabetes data processing.

This module provides the command-line interface for processing diabetes device data files.
It handles format detection, reader selection, and data processing while providing
informative output about the process.
"""

import argparse
import logging
import sys
from pathlib import Path

from src.core.aligner import Aligner
from src.core.exceptions import (
    AlignmentError,
    DataProcessingError,
    DataValidationError,
    FileAccessError,
    ProcessingError,
    ReaderError,
)
from src.file_parser.format_detector import FormatDetectionError, FormatDetector
from src.file_parser.format_registry import FormatRegistry
from src.processors import DataProcessor
from src.readers.base import BaseReader

logger = logging.getLogger(__name__)


def setup_logging(debug: bool = False):
    """Configure logging based on debug flag."""
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(message)s",
    )


def validate_file(file_path: Path):
    """Validate file exists and is accessible."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")


def process_file(file_path: Path):
    """Process diabetes device data file.

    Returns:
        Dict containing processed data by DataType
    """
    logger.debug("\nAnalyzing file: %s", file_path)

    # Load registered formats and detect matches
    registry = FormatRegistry()
    detector = FormatDetector(registry)

    print("\u2170 Format Detection Initialised.")
    detected_format, error, _ = detector.detect_format(file_path)
    if not detected_format:
        raise FormatDetectionError(f"No valid format detected: {error}")
    print("    \u2713 Format Detection Successful.")

    # Get appropriate reader and process data
    print("\u2171 Data Reading Initialised.")
    reader = BaseReader.get_reader_for_format(detected_format, file_path)
    with reader:
        table_data = reader.read_all_tables()
        if not table_data:
            raise DataProcessingError("No valid data found in file")
        print("    \u2713 Data Reading Successful.")

        # Initialize data processor
        print("\u2172 Data Processing Initialised.")
        processor = DataProcessor()
        try:
            # Create a dictionary mapping table names to their configurations
            table_configs = {
                table.name: table
                for file_config in detected_format.files
                for table in file_config.tables
            }

            processed_data = processor.process_tables(
                table_data=table_data, table_configs=table_configs
            )
            if not processed_data:
                raise ProcessingError("No data could be processed")
            return processed_data

        except ProcessingError as e:
            raise ProcessingError(f"Failed to process data: {str(e)}") from e


def display_results(results, debug: bool = False):
    """Display processed data results."""
    for _, processed_data in results.items():
        df = processed_data.dataframe

        if debug:
            print("\nProcessing Notes:")
            for note in processed_data.processing_notes:
                print(f"- {note}")

            print("\nDetailed Analysis:")

            # Data completeness
            null_counts = df.isnull().sum()
            print("\nMissing Values by Column:")
            print(
                null_counts[null_counts > 0]
                if any(null_counts > 0)
                else "No missing values"
            )

            # Value distributions
            print("\nValue Counts for Non-Numeric Columns:")
            for col in df.select_dtypes(exclude=["number"]).columns:
                print(f"\n{col}:")
                print(df[col].value_counts().head())

            # Time-based analysis
            print("\nTemporal Analysis:")
            print(f"Date Range: {df.index.min()} to {df.index.max()}")
            print(f"Total Duration: {df.index.max() - df.index.min()}")

            # Data density
            readings_per_day = df.groupby(df.index.date).size()
            print("\nReadings per Day:")
            print(f"Mean: {readings_per_day.mean():.2f}")
            print(f"Min: {readings_per_day.min()}")
            print(f"Max: {readings_per_day.max()}")

            # Numeric column statistics
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) > 0:
                print("\nDetailed Numeric Analysis:")
                for col in numeric_cols:
                    print(f"\n{col}:")
                    print(f"Skewness: {df[col].skew():.2f}")
                    print(f"Kurtosis: {df[col].kurtosis():.2f}")
                    print("Quantiles:")
                    print(df[col].quantile([0.1, 0.25, 0.5, 0.75, 0.9]))

            # Memory usage
            print("\nMemory Usage:")
            print(df.memory_usage(deep=True))

            # Unit information
            print("\nUnit Information:")
            for col, unit in processed_data.source_units.items():
                print(f"{col}: {unit.value}")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Diabetes Data Format Detection and Processing Tool"
    )
    parser.add_argument("file_path", type=str, help="Path to the file to analyze")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging and detailed analysis",
    )
    args = parser.parse_args()

    setup_logging(args.debug)

    try:
        aligner = Aligner()
        file_path = Path(args.file_path)
        validate_file(file_path)

        results = process_file(file_path)
        display_results(results, args.debug)
        # Display dataframe shapes
        for key, item in results.items():
            print("     ", key.name, " Dataframe Shape: ", item.dataframe.shape)

        # Created Aligned data
        print("\u2173 Data Alignment Initialised.")
        try:
            aligned = aligner.align(results)
            print("    \u2713 Data Alignment Successful.")
            print("      Aligned Dataframe Shape: ", aligned.dataframe.shape)

        except AlignmentError as e:

            logger.error(str(e))
        print("\u2174 Data Export Initialised.")

    except (
        FileAccessError,
        ValueError,
        FormatDetectionError,
        DataProcessingError,
        ReaderError,
        ProcessingError,
    ) as e:
        logger.error(str(e))
        if args.debug and not isinstance(e, (FileNotFoundError, ValueError)):
            logger.exception("Debug traceback:")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nProcess interrupted by user")
        sys.exit(1)
    except DataValidationError:
        logger.error("An unexpected error occurred")
        if args.debug:
            logger.exception("Debug traceback:")
        sys.exit(1)


if __name__ == "__main__":
    main()
