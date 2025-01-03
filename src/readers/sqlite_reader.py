"""SQLite Reader for confirmed configuration with sqlite DATA_TYPE"""

import logging
import sys
from pathlib import Path

from file_parser.format_detector import FormatDetectionError, FormatDetector
from file_parser.format_registry import FormatRegistry

logger = logging.getLogger(__name__)
try:
    file_path = Path("data/20240928-130349.sqlite")
    logger.debug("\nAnalyzing file: %s", file_path)

    registry = FormatRegistry()
    detector = FormatDetector(registry)

    detected_format, error, validation_results = detector.detect_format(file_path)
    print(detected_format)
except FormatDetectionError as e:
    logger.error("Error: %s", str(e))
    sys.exit(1)
