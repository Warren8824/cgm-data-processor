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

    detected_format, error, _ = detector.detect_format(file_path)
    if not detected_format:
        raise FormatDetectionError(f"No valid format detected: {error}")

    # Get appropriate reader and process data
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

        return result


def display_results(results):
    """Display processed data results.

    Args:
        results: Dict of table names to processed DataFrames
    """
    if "BgReadings" in results:
        print("\nCGM Data Info:")
        results["BgReadings"].info()
        print("\nCGM Data Descriptive Stats:")
        print(results["BgReadings"].describe())

    if "Treatments" in results:
        print("\nTreatment Data Info:")
        results["Treatments"].info()
        print("\nTreatment Data Descriptive Stats:")
        print(results["Treatments"].describe())


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Diabetes Data Format Detection and Processing Tool"
    )
    parser.add_argument("file_path", type=str, help="Path to the file to analyze")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    setup_logging(args.debug)

    try:
        file_path = Path(args.file_path)
        validate_file(file_path)

        results = process_file(file_path)
        display_results(results)

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
