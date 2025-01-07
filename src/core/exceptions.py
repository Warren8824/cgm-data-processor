"""Base module for all expceptions used within the system"""

from typing import Any, Dict, Optional


class CGMProcessorError(Exception):
    """Base exception for all CGM processor errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class FileError(CGMProcessorError):
    """Base class for file-related errors."""


class FormatError(CGMProcessorError):
    """Base class for format-related errors."""


class ProcessingError(CGMProcessorError):
    """Base class for data processing errors."""


class ValidationError(CGMProcessorError):
    """Base class for validation errors."""


# Specific Exceptions
class FileAccessError(FileError):
    """Raised when there's an error accessing a file."""


class FileParseError(FileError):
    """Raised when there's an error parsing file contents."""


class FormatDetectionError(FormatError):
    """Raised when there's an error detecting file format."""


class FormatValidationError(FormatError):
    """Raised when there's an error validating format definition."""


class DataProcessingError(ProcessingError):
    """Raised when there's an error processing data."""


class DataValidationError(ValidationError):
    """Raised when there's an error validating data."""


# Data Quality Errors


class DataQualityError(ProcessingError):
    """Raised when data quality checks fail (e.g., too many gaps, noise)."""


class TimeAlignmentError(ProcessingError):
    """Raised when there are issues aligning different data streams (e.g., CGM with insulin)."""


class UnitConversionError(ProcessingError):
    """Raised for unit conversion issues (e.g., mg/dL to mmol/L)."""


class DeviceFormatError(FormatError):
    """Raised for device-specific format issues."""


class MetricCalculationError(ProcessingError):
    """Raised when there are issues calculating diabetes metrics."""


class CalibrationError(ProcessingError):
    """Raised for sensor calibration related issues."""


class DataGapError(DataQualityError):
    """Raised when data gaps exceed acceptable thresholds."""