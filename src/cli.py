"""Command line interface for diabetes data processing."""

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
from src.core.format_registry import FormatRegistry
from src.exporters.csv import create_csv_exporter
from src.file_parser.format_detector import FormatDetectionError, FormatDetector
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


def process_file(
    file_path: Path,
    **kwargs,
):
    """Process diabetes device data file with configurable parameters."""
    logger.debug("\nAnalyzing file: %s", file_path)

    registry = FormatRegistry()
    detector = FormatDetector(registry)

    print("\u2170 Format Detection Initialised.")
    detected_format, _, _ = detector.detect_format(file_path)
    if not detected_format:
        raise FormatDetectionError(
            "No valid format detected: Share a sample of this file in our Github Repo."
        )
    print("    \u2713 Format Detection Successful.")
    print(f"      Currently processing file with {detected_format.name} Format. \n")

    print("\u2171 Data Reading Initialised.")
    reader = BaseReader.get_reader_for_format(detected_format, file_path)
    with reader:
        table_data = reader.read_all_tables()
        if not table_data:
            raise DataProcessingError("No valid data found in file")
        print("    \u2713 Data Reading Successful. \n")

        print("\u2172 Data Processing Initialised.")
        processor = DataProcessor()
        try:
            processed_data = processor.process_tables(
                table_data=table_data,
                detected_format=detected_format,
                **kwargs,
            )
            if not processed_data:
                raise ProcessingError("No data could be processed")
            return processed_data

        except ProcessingError as e:
            raise ProcessingError(f"Failed to process data: {str(e)}") from e


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
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory for exported data",
    )
    parser.add_argument(
        "--interpolation-limit",
        type=int,
        help="Maximum number of CGM gaps to interpolate (4 = 20 mins)",
    )
    parser.add_argument(
        "--bolus-limit",
        type=float,
        help="Maximum insulin units for bolus classification",
    )
    parser.add_argument(
        "--max-dose",
        type=float,
        help="Maximum valid insulin dose",
    )
    args = parser.parse_args()

    setup_logging(args.debug)

    try:
        aligner = Aligner()
        file_path = Path(args.file_path)
        validate_file(file_path)

        results = process_file(
            file_path,
            interpolation_limit=args.interpolation_limit,
            bolus_limit=args.bolus_limit,
            max_dose=args.max_dose,
        )

        for key, item in results.items():
            print("     ", key.name, " Dataframe Shape: ", item.dataframe.shape)

        print("\n\u2173 Data Alignment Initialised.")
        try:
            aligned = aligner.align(results)
            print("    \u2713 Data Alignment Successful.")
            print("      Aligned Dataframe Shape: ", aligned.dataframe.shape, "\n")

        except AlignmentError as e:
            logger.error(str(e))

        print("\u2174 Data Export Initialised.")
        if args.output is None:
            exporter = create_csv_exporter()
        else:
            exporter = create_csv_exporter(args.output)
        exporter.export_data(results, aligned)
        print("    \u2713 Data Export Successful.")

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
