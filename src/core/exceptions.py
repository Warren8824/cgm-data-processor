"""This module provides all exceptions used within the system. All exceptions inherit from
the base class CGMProcessorError or one of the subsequent children classes.
"""

from typing import Any, Dict, Optional


class CGMProcessorError(Exception):
    """Base exception for all CGM processor errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class FileError(CGMProcessorError):
    """Base class for file-related errors."""


class FileAccessError(FileError):
    """Raised when there's an error accessing a file."""


class FileExtensionError(FileError):
    """Raised When file extension is not supported."""


class FileParseError(FileError):
    """Raised when there's an error parsing file contents."""


class FormatError(CGMProcessorError):
    """Base class for format-related errors."""


class FormatDetectionError(FormatError):
    """Raised when there's an error detecting file format."""


class FormatLoadingError(FormatError):
    """Raised when a format file can`t be loaded."""


class FormatValidationError(FormatError):
    """Raised when there's an error validating format definition."""


class DeviceFormatError(FormatError):
    """Raised for device-specific format issues."""


class ReaderError(CGMProcessorError):
    """Base class for reader related errors."""


class ProcessingError(CGMProcessorError):
    """Base class for data processing errors."""


class DataProcessingError(ProcessingError):
    """Raised when there's an error processing data."""


class TimestampProcessingError(ProcessingError):
    """Raised when there is a timestamp format issues"""


class AlignmentError(ProcessingError):
    """Raised when there is an error aligning datasets"""


class DataExistsError(FileError):
    """Raised when the reader returns no data"""


class ValidationError(CGMProcessorError):
    """Base class for validation errors."""


class DataValidationError(ValidationError):
    """Raised when there's an error validating data."""


class ExportError(CGMProcessorError):
    """Base class for export errors"""


# Data Quality Errors


class DataQualityError(ProcessingError):
    """Raised when data quality checks fail (e.g., too many gaps, noise)."""


class TimeAlignmentError(ProcessingError):
    """Raised when there are issues aligning different data streams (e.g., CGM with insulin)."""


class UnitConversionError(ProcessingError):
    """Raised for unit conversion issues (e.g., mg/dL to mmol/L)."""


class MetricCalculationError(ProcessingError):
    """Raised when there are issues calculating diabetes metrics."""


class CalibrationError(ProcessingError):
    """Raised for sensor calibration related issues."""


class DataGapError(DataQualityError):
    """Raised when data gaps exceed acceptable thresholds."""
