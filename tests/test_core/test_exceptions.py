import pytest

from src.core.exceptions import (
    AlignmentError,
    CalibrationError,
    CGMProcessorError,
    DataExistsError,
    DataGapError,
    DataProcessingError,
    DataQualityError,
    DataValidationError,
    DeviceFormatError,
    ExportError,
    FileAccessError,
    FileError,
    FileExtensionError,
    FileParseError,
    FormatDetectionError,
    FormatError,
    FormatLoadingError,
    FormatValidationError,
    MetricCalculationError,
    ProcessingError,
    ReaderError,
    TimeAlignmentError,
    TimestampProcessingError,
    UnitConversionError,
    ValidationError,
)


def test_base_exception_initialization():
    exc = CGMProcessorError("Test error", {"foo": "bar"})
    assert exc.details == {"foo": "bar"}


def test_base_exception_details_default():
    exc = CGMProcessorError("Test error")
    assert exc.details == {}


@pytest.mark.parametrize(
    "exception_class",
    [
        FileError,
        FileAccessError,
        FileExtensionError,
        FileParseError,
        FormatError,
        FormatDetectionError,
        FormatLoadingError,
        FormatValidationError,
        DeviceFormatError,
        ReaderError,
        ProcessingError,
        DataProcessingError,
        TimestampProcessingError,
        AlignmentError,
        DataExistsError,
        ValidationError,
        DataValidationError,
        ExportError,
        DataQualityError,
        TimeAlignmentError,
        UnitConversionError,
        MetricCalculationError,
        CalibrationError,
        DataGapError,
    ],
)
def test_subclass_is_instance_of_base(exception_class):
    exc = exception_class("Test")
    assert isinstance(exc, CGMProcessorError)


@pytest.mark.parametrize(
    "subclass, parent",
    [
        (FileAccessError, FileError),
        (FileExtensionError, FileError),
        (FileParseError, FileError),
        (FormatDetectionError, FormatError),
        (FormatLoadingError, FormatError),
        (FormatValidationError, FormatError),
        (DeviceFormatError, FormatError),
        (DataProcessingError, ProcessingError),
        (TimestampProcessingError, ProcessingError),
        (AlignmentError, ProcessingError),
        (DataQualityError, ProcessingError),
        (TimeAlignmentError, ProcessingError),
        (UnitConversionError, ProcessingError),
        (MetricCalculationError, ProcessingError),
        (CalibrationError, ProcessingError),
        (DataGapError, DataQualityError),
        (DataExistsError, FileError),
        (DataValidationError, ValidationError),
    ],
)
def test_subclass_correct_parent(subclass, parent):
    assert issubclass(subclass, parent)
