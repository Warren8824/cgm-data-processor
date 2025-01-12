"""Command line interface for diabetes data processing.

This module provides the command-line interface for processing diabetes device data files.
It handles format detection, reader selection, and data processing while providing
informative output about the process.
"""

import argparse
import logging
import sys
from pathlib import Path

from src.core.exceptions import DataProcessingError, DataValidationError, ReaderError
from src.file_parser.format_detector import FormatDetectionError, FormatDetector
from src.file_parser.format_registry import FormatRegistry
from src.readers.base import BaseReader

logger = logging.getLogger(__name__)


def setup_logging(debug: bool = False):
    """Configure logging based on debug flag."""
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(message)s",
    )


def validate_file(file_path: Path):
    """Validate file exists and is accessible.

    Args:
        file_path: Path to the data file

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If path is not a file
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")


def process_file(file_path: Path):
    """Process diabetes device data file.

    Args:
        file_path: Path to the data file

    Returns:
        Dict containing processed table data

    Raises:
        FormatDetectionError: If format detection fails
        DataProcessingError: If data processing fails
        ReaderError: If appropriate reader not found
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

        # Filter out tables with missing critical columns
        result = {
            name: data.dataframe
            for name, data in table_data.items()
            if not data.missing_required_columns
        }

        if not result:
            raise DataProcessingError("No valid data found in file")

        print("    \u2713 Data Reading Successful.")
        return result


def display_results(results, debug: bool = False):
    """Display processed data results.

    Args:
        results: Dict of table names to processed DataFrames
        debug: If True, displays additional statistical information
    """
    for table_name, df in results.items():
        print(f"\n{'=' * 50}")
        print(f"{table_name,df.shape}")
        print(f"{'=' * 50}")

        if debug:
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
        file_path = Path(args.file_path)
        validate_file(file_path)

        results = process_file(file_path)
        display_results(results, args.debug)  # Pass debug flag to display_results

    except (
        FileNotFoundError,
        ValueError,
        FormatDetectionError,
        DataProcessingError,
        ReaderError,
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
