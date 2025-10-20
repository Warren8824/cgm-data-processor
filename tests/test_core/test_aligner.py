import pandas as pd
import pytest

from src.core.aligner import Aligner, AlignmentError

# ------------------- VALIDATE TIMELINE TESTS ------------------- #
# Sample reference data for tests

# Valid path: 5-minute increasing timeline
valid_index = pd.date_range("2025-10-20 00:00", periods=5, freq="5min")
valid_df = pd.DataFrame({"value": [1, 2, 3, 4, 5]}, index=valid_index)

# Empty DataFrame
empty_df = pd.DataFrame({"value": []}, index=pd.DatetimeIndex([]))

# Non-datetime index
non_datetime_df = pd.DataFrame({"value": [1, 2]}, index=[1, 2])

# Non-monotonic index
non_mono_index = pd.to_datetime(
    ["2025-10-20 00:00", "2025-10-20 00:10", "2025-10-20 00:05"]
)
non_mono_df = pd.DataFrame({"value": [1, 2, 3]}, index=non_mono_index)

# Wrong frequency
wrong_freq_index = pd.date_range("2025-10-20 00:00", periods=5, freq="10min")
wrong_freq_df = pd.DataFrame({"value": [1, 2, 3, 4, 5]}, index=wrong_freq_index)


def test_empty_dataframe():
    aligner = Aligner()
    with pytest.raises(AlignmentError, match="Reference data is empty"):
        aligner._validate_timeline(empty_df, "5min")


def test_non_datetime_index():
    aligner = Aligner()
    with pytest.raises(AlignmentError, match="Reference data must have DatetimeIndex"):
        aligner._validate_timeline(non_datetime_df, "5min")


def test_non_monotonic_index():
    aligner = Aligner()
    with pytest.raises(
        AlignmentError, match="Reference data index must be monotonically increasing"
    ):
        aligner._validate_timeline(non_mono_df, "5min")


def test_wrong_frequency():
    aligner = Aligner()
    with pytest.raises(
        AlignmentError, match="Reference data frequency .* does not match expected 5min"
    ):
        aligner._validate_timeline(wrong_freq_df, "5min")


def test_valid_timeline():
    aligner = Aligner()
    # Should pass without raising
    aligner._validate_timeline(valid_df, "5min")
