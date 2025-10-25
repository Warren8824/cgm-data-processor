import pandas as pd
import pytest

from src.core.aligner import Aligner, AlignmentError, DataType, ProcessedTypeData


# ------------------- FIXTURES ------------------- #
@pytest.fixture
def aligner():
    """Create an Aligner instance."""
    return Aligner()


@pytest.fixture
def reference_index():
    """Create a reference timeline (5-minute intervals)."""
    return pd.date_range("2024-01-01 00:00", "2024-01-01 01:00", freq="5min")


@pytest.fixture
def valid_bgm_data():
    """Create valid BGM data with all required columns."""
    index = pd.date_range("2024-01-01 00:00", "2024-01-01 01:00", freq="10min")
    return pd.DataFrame(
        {
            "bgm_primary": [100.0, 120.0, 110.0, 130.0, 115.0, 125.0, 105.0],
            "bgm_primary_clipped": [False, False, False, True, False, False, False],
            "bgm_primary_mmol": [5.55, 6.66, 6.11, 7.22, 6.38, 6.94, 5.83],
        },
        index=index,
    )


@pytest.fixture
def valid_insulin_data():
    """Create valid insulin data with basal and bolus doses."""
    index = pd.date_range("2024-01-01 00:00", "2024-01-01 01:00", freq="15min")
    return pd.DataFrame(
        {
            "dose": [5.0, 10.0, 3.0, 12.0, 6.0],
            "is_bolus": [True, False, True, False, True],
            "is_basal": [False, True, False, True, False],
            "type": ["novorapid", "levemir", "novorapid", "levemir", ""],
        },
        index=index,
    )


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


# ------------------- COLLECT PROCESSING NOTES TESTS ------------------- #


def test_normal_case():
    aligner = Aligner()
    processed_data = {
        DataType.CGM: ProcessedTypeData(
            dataframe=pd.DataFrame(),
            source_units={},
            processing_notes=["note1", "note2"],
        ),
        DataType.BGM: ProcessedTypeData(
            dataframe=pd.DataFrame(), source_units={}, processing_notes=["bgm note"]
        ),
    }

    notes = aligner._collect_processing_notes(processed_data)

    assert notes == [
        "CGM Processing Notes:",
        "  note1",
        "  note2",
        "BGM Processing Notes:",
        "  bgm note",
    ]


def test_empty_notes_lists():
    aligner = Aligner()
    processed_data = {
        DataType.CGM: ProcessedTypeData(
            dataframe=pd.DataFrame(), source_units={}, processing_notes=[]
        ),
        DataType.BGM: ProcessedTypeData(
            dataframe=pd.DataFrame(), source_units={}, processing_notes=[]
        ),
    }

    notes = aligner._collect_processing_notes(processed_data)

    assert notes == ["CGM Processing Notes:", "BGM Processing Notes:"]


def test_collect_processing_dict_empty():
    aligner = Aligner()
    notes = aligner._collect_processing_notes({})
    assert notes == []


def test_multiline_notes():
    aligner = Aligner()
    processed_data = {
        DataType.CGM: ProcessedTypeData(
            dataframe=pd.DataFrame(),
            source_units={},
            processing_notes=["line1\nline2", "note2"],
        )
    }

    notes = aligner._collect_processing_notes(processed_data)

    assert notes == ["CGM Processing Notes:", "  line1\nline2", "  note2"]


def test_single_type_no_notes():
    aligner = Aligner()
    processed_data = {
        DataType.INSULIN: ProcessedTypeData(
            dataframe=pd.DataFrame(), source_units={}, processing_notes=[]
        )
    }

    notes = aligner._collect_processing_notes(processed_data)

    assert notes == ["INSULIN Processing Notes:"]


# ------------------- ALIGN BGM TESTS ------------------- #
class TestAlignBGMBasic:
    """Test basic functionality and validation."""

    def test_empty_dataframe_raises_error(self, aligner, reference_index):
        """Empty DataFrame should raise AlignmentError."""
        empty_df = pd.DataFrame(index=pd.DatetimeIndex([]))

        with pytest.raises(AlignmentError, match="Input DataFrame is empty"):
            aligner._align_bgm(empty_df, reference_index, "5min")

    def test_non_datetime_index_raises_error(self, aligner, reference_index):
        """Non-DatetimeIndex should raise AlignmentError."""
        df = pd.DataFrame(
            {
                "bgm_primary": [100.0, 120.0],
                "bgm_primary_clipped": [False, False],
                "bgm_primary_mmol": [5.55, 6.66],
            },
            index=[0, 1],  # Integer index
        )

        with pytest.raises(AlignmentError, match="index is not datetime"):
            aligner._align_bgm(df, reference_index, "5min")

    def test_missing_clipped_column_raises_error(self, aligner, reference_index):
        """Missing _clipped column should raise AlignmentError."""
        index = pd.date_range("2024-01-01 00:00", periods=3, freq="10min")
        df = pd.DataFrame(
            {
                "bgm_primary": [100.0, 120.0, 110.0],
                "bgm_primary_mmol": [5.55, 6.66, 6.11],
            },
            index=index,
        )

        with pytest.raises(AlignmentError, match="Missing expected column"):
            aligner._align_bgm(df, reference_index, "5min")

    def test_missing_mmol_column_raises_error(self, aligner, reference_index):
        """Missing _mmol column should raise AlignmentError."""
        index = pd.date_range("2024-01-01 00:00", periods=3, freq="10min")
        df = pd.DataFrame(
            {
                "bgm_primary": [100.0, 120.0, 110.0],
                "bgm_primary_clipped": [False, False, False],
            },
            index=index,
        )

        with pytest.raises(AlignmentError, match="Missing expected column"):
            aligner._align_bgm(df, reference_index, "5min")

    def test_no_value_columns_returns_empty(self, aligner, reference_index):
        """DataFrame with only _clipped and _mmol columns returns empty DataFrame."""
        index = pd.date_range("2024-01-01 00:00", periods=3, freq="10min")
        df = pd.DataFrame(
            {
                "bgm_primary_clipped": [False, False, False],
                "bgm_primary_mmol": [5.55, 6.66, 6.11],
            },
            index=index,
        )

        result = aligner._align_bgm(df, reference_index, "5min")

        assert result.empty
        assert len(result) == len(reference_index)
        assert result.index.equals(reference_index)


class TestAlignBGMAlignment:
    """Test alignment and resampling behaviour."""

    def test_basic_alignment(self, aligner, valid_bgm_data, reference_index):
        """Basic alignment with valid data works correctly."""
        result = aligner._align_bgm(valid_bgm_data, reference_index, "5min")

        assert len(result) == len(reference_index)
        assert result.index.equals(reference_index)
        assert "bgm_primary" in result.columns
        assert "bgm_primary_clipped" in result.columns
        assert "bgm_primary_mmol" in result.columns

    def test_values_averaged_in_resample_window(self, aligner, reference_index):
        """Values in same resample window are averaged."""
        # Create data with multiple values in same 5-min window
        index = pd.DatetimeIndex(
            [
                "2024-01-01 00:00:00",
                "2024-01-01 00:02:00",  # Both round to 00:00
                "2024-01-01 00:10:00",
            ]
        )
        df = pd.DataFrame(
            {
                "bgm_primary": [100.0, 120.0, 110.0],
                "bgm_primary_clipped": [False, False, False],
                "bgm_primary_mmol": [5.55, 6.66, 6.11],
            },
            index=index,
        )

        result = aligner._align_bgm(df, reference_index, "5min")

        # First window should have average of 100 and 120
        assert result.loc["2024-01-01 00:00:00", "bgm_primary"] == 110.0
        assert result.loc["2024-01-01 00:00:00", "bgm_primary_mmol"] == pytest.approx(
            6.105
        )

    def test_clipped_column_any_behaviour(self, aligner, reference_index):
        """Clipped column uses .any() - True if any True in window."""
        index = pd.DatetimeIndex(
            [
                "2024-01-01 00:00:00",
                "2024-01-01 00:02:00",  # Both round to 00:00
                "2024-01-01 00:10:00",
            ]
        )
        df = pd.DataFrame(
            {
                "bgm_primary": [100.0, 120.0, 110.0],
                "bgm_primary_clipped": [False, True, False],  # One True
                "bgm_primary_mmol": [5.55, 6.66, 6.11],
            },
            index=index,
        )

        result = aligner._align_bgm(df, reference_index, "5min")

        # First window has one True, so result should be True
        assert result.loc["2024-01-01 00:00:00", "bgm_primary_clipped"] is True
        # Second window has all False
        assert result.loc["2024-01-01 00:10:00", "bgm_primary_clipped"] is False

    def test_empty_resample_windows_have_nan(self, aligner, reference_index):
        """Empty resample windows result in NaN values."""
        # Data only at start and end, gaps in middle
        index = pd.DatetimeIndex(["2024-01-01 00:00:00", "2024-01-01 01:00:00"])
        df = pd.DataFrame(
            {
                "bgm_primary": [100.0, 120.0],
                "bgm_primary_clipped": [False, False],
                "bgm_primary_mmol": [5.55, 6.66],
            },
            index=index,
        )

        result = aligner._align_bgm(df, reference_index, "5min")

        # Middle windows should be NaN
        assert pd.isna(result.loc["2024-01-01 00:05:00", "bgm_primary"])
        assert pd.isna(result.loc["2024-01-01 00:30:00", "bgm_primary_mmol"])


class TestAlignBGMMultipleColumns:
    """Test handling of multiple value columns."""

    def test_multiple_value_columns(self, aligner, reference_index):
        """Multiple BGM columns are all processed correctly."""
        index = pd.date_range("2024-01-01 00:00", periods=3, freq="10min")
        df = pd.DataFrame(
            {
                "bgm_primary": [100.0, 120.0, 110.0],
                "bgm_primary_clipped": [False, False, False],
                "bgm_primary_mmol": [5.55, 6.66, 6.11],
                "bgm_1": [95.0, 115.0, 105.0],
                "bgm_1_clipped": [False, True, False],
                "bgm_1_mmol": [5.27, 6.38, 5.83],
            },
            index=index,
        )

        result = aligner._align_bgm(df, reference_index, "5min")

        assert "bgm_primary" in result.columns
        assert "bgm_primary_clipped" in result.columns
        assert "bgm_primary_mmol" in result.columns
        assert "bgm_1" in result.columns
        assert "bgm_1_clipped" in result.columns
        assert "bgm_1_mmol" in result.columns


class TestAlignBGMReferenceIndex:
    """Test different reference index scenarios."""

    def test_reference_index_longer_than_data(self, aligner):
        """Reference index extending beyond data results in NaN."""
        # Data from 00:00 to 00:20
        data_index = pd.date_range("2024-01-01 00:00", periods=3, freq="10min")
        df = pd.DataFrame(
            {
                "bgm_primary": [100.0, 120.0, 110.0],
                "bgm_primary_clipped": [False, False, False],
                "bgm_primary_mmol": [5.55, 6.66, 6.11],
            },
            index=data_index,
        )

        # Reference extends to 01:00
        ref_index = pd.date_range("2024-01-01 00:00", "2024-01-01 01:00", freq="5min")

        result = aligner._align_bgm(df, ref_index, "5min")

        assert len(result) == len(ref_index)
        # Later times should be NaN
        assert pd.isna(result.loc["2024-01-01 00:30:00", "bgm_primary"])

    def test_reference_index_shorter_than_data(self, aligner):
        """Reference index shorter than data only returns overlapping period."""
        # Data from 00:00 to 01:00
        data_index = pd.date_range("2024-01-01 00:00", "2024-01-01 01:00", freq="10min")
        df = pd.DataFrame(
            {
                "bgm_primary": [100.0, 120.0, 110.0, 130.0, 115.0, 125.0, 105.0],
                "bgm_primary_clipped": [False] * 7,
                "bgm_primary_mmol": [5.55, 6.66, 6.11, 7.22, 6.38, 6.94, 5.83],
            },
            index=data_index,
        )

        # Reference only to 00:20
        ref_index = pd.date_range("2024-01-01 00:00", "2024-01-01 00:20", freq="5min")

        result = aligner._align_bgm(df, ref_index, "5min")

        assert len(result) == len(ref_index)
        assert result.index.equals(ref_index)


class TestAlignBGMFrequencies:
    """Test different frequency parameters."""

    def test_15min_frequency(self, aligner):
        """Alignment works with 15-minute frequency."""
        data_index = pd.date_range("2024-01-01 00:00", periods=5, freq="7min")
        df = pd.DataFrame(
            {
                "bgm_primary": [100.0, 120.0, 110.0, 130.0, 115.0],
                "bgm_primary_clipped": [False] * 5,
                "bgm_primary_mmol": [5.55, 6.66, 6.11, 7.22, 6.38],
            },
            index=data_index,
        )

        ref_index = pd.date_range("2024-01-01 00:00", "2024-01-01 01:00", freq="15min")

        result = aligner._align_bgm(df, ref_index, "15min")

        assert len(result) == len(ref_index)
        assert result.index.equals(ref_index)

    def test_1hour_frequency(self, aligner):
        """Alignment works with 1-hour frequency."""
        data_index = pd.date_range("2024-01-01 00:00", periods=7, freq="10min")
        df = pd.DataFrame(
            {
                "bgm_primary": [100.0, 120.0, 110.0, 130.0, 115.0, 125.0, 105.0],
                "bgm_primary_clipped": [False] * 7,
                "bgm_primary_mmol": [5.55, 6.66, 6.11, 7.22, 6.38, 6.94, 5.83],
            },
            index=data_index,
        )

        ref_index = pd.date_range("2024-01-01 00:00", "2024-01-01 03:00", freq="1h")

        result = aligner._align_bgm(df, ref_index, "1h")

        assert len(result) == len(ref_index)
        assert result.index.equals(ref_index)


# ------------------ALIGN INSULIN TESTS ------------------ #


class TestAlignInsulinBasic:
    """Test basic functionality and validation."""

    def test_empty_dataframe_raises_error(self, aligner, reference_index):
        """Empty DataFrame should raise AlignmentError."""
        empty_df = pd.DataFrame(index=pd.DatetimeIndex([]))

        with pytest.raises(AlignmentError, match="Input DataFrame is empty"):
            aligner._align_insulin(empty_df, reference_index, "5min")

    def test_non_datetime_index_raises_error(self, aligner, reference_index):
        """Non-DatetimeIndex should raise AlignmentError."""
        df = pd.DataFrame(
            {
                "dose": [5.0, 10.0],
                "is_bolus": [True, False],
                "is_basal": [False, True],
            },
            index=[0, 1],  # Integer index
        )

        with pytest.raises(AlignmentError, match="index is not datetime"):
            aligner._align_insulin(df, reference_index, "5min")

    def test_missing_dose_column_raises_error(self, aligner, reference_index):
        """Missing dose column should raise AlignmentError."""
        index = pd.date_range("2024-01-01 00:00", periods=3, freq="10min")
        df = pd.DataFrame(
            {
                "is_bolus": [True, False, True],
                "is_basal": [False, True, False],
            },
            index=index,
        )

        with pytest.raises(AlignmentError, match="Missing required column.*dose"):
            aligner._align_insulin(df, reference_index, "5min")

    def test_missing_is_bolus_column_raises_error(self, aligner, reference_index):
        """Missing is_bolus column should raise AlignmentError."""
        index = pd.date_range("2024-01-01 00:00", periods=3, freq="10min")
        df = pd.DataFrame(
            {
                "dose": [5.0, 10.0, 3.0],
                "is_basal": [False, True, False],
            },
            index=index,
        )

        with pytest.raises(AlignmentError, match="Missing required column.*is_bolus"):
            aligner._align_insulin(df, reference_index, "5min")

    def test_missing_is_basal_column_raises_error(self, aligner, reference_index):
        """Missing is_basal column should raise AlignmentError."""
        index = pd.date_range("2024-01-01 00:00", periods=3, freq="10min")
        df = pd.DataFrame(
            {
                "dose": [5.0, 10.0, 3.0],
                "is_bolus": [True, False, True],
            },
            index=index,
        )

        with pytest.raises(AlignmentError, match="Missing required column.*is_basal"):
            aligner._align_insulin(df, reference_index, "5min")

    def test_missing_multiple_columns_raises_error(self, aligner, reference_index):
        """Missing multiple columns should raise AlignmentError."""
        index = pd.date_range("2024-01-01 00:00", periods=3, freq="10min")
        df = pd.DataFrame(
            {
                "dose": [5.0, 10.0, 3.0],
            },
            index=index,
        )

        with pytest.raises(AlignmentError, match="Missing required column"):
            aligner._align_insulin(df, reference_index, "5min")


class TestAlignInsulinAlignment:
    """Test alignment and resampling behaviour."""

    def test_basic_alignment(self, aligner, valid_insulin_data, reference_index):
        """Basic alignment with valid data works correctly."""
        result = aligner._align_insulin(valid_insulin_data, reference_index, "5min")

        assert len(result) == len(reference_index)
        assert result.index.equals(reference_index)
        assert "basal_dose" in result.columns
        assert "bolus_dose" in result.columns
        assert len(result.columns) == 2

    def test_doses_summed_in_resample_window(self, aligner, reference_index):
        """Doses in same resample window are summed."""
        # Create data with multiple doses in same 5-min window
        index = pd.DatetimeIndex(
            [
                "2024-01-01 00:00:00",
                "2024-01-01 00:02:00",  # Both round to 00:00
                "2024-01-01 00:10:00",
            ]
        )
        df = pd.DataFrame(
            {
                "dose": [5.0, 3.0, 10.0],
                "is_bolus": [True, True, False],
                "is_basal": [False, False, True],
                "type": ["", "", ""],
            },
            index=index,
        )

        result = aligner._align_insulin(df, reference_index, "5min")

        # First window should have sum of 5.0 + 3.0 = 8.0 for bolus
        assert result.loc["2024-01-01 00:00:00", "bolus_dose"] == 8.0
        assert result.loc["2024-01-01 00:00:00", "basal_dose"] == 0.0
        # Second window has basal dose
        assert result.loc["2024-01-01 00:10:00", "basal_dose"] == 10.0
        assert result.loc["2024-01-01 00:10:00", "bolus_dose"] == 0.0

    def test_basal_and_bolus_separated(self, aligner, reference_index):
        """Basal and bolus doses are correctly separated."""
        index = pd.DatetimeIndex(
            [
                "2024-01-01 00:00:00",
                "2024-01-01 00:05:00",
                "2024-01-01 00:10:00",
            ]
        )
        df = pd.DataFrame(
            {
                "dose": [5.0, 10.0, 7.0],
                "is_bolus": [True, False, True],
                "is_basal": [False, True, False],
                "type": ["", "", ""],
            },
            index=index,
        )

        result = aligner._align_insulin(df, reference_index, "5min")

        assert result.loc["2024-01-01 00:00:00", "bolus_dose"] == 5.0
        assert result.loc["2024-01-01 00:00:00", "basal_dose"] == 0.0
        assert result.loc["2024-01-01 00:05:00", "bolus_dose"] == 0.0
        assert result.loc["2024-01-01 00:05:00", "basal_dose"] == 10.0
        assert result.loc["2024-01-01 00:10:00", "bolus_dose"] == 7.0
        assert result.loc["2024-01-01 00:10:00", "basal_dose"] == 0.0

    def test_empty_resample_windows_have_zero(self, aligner, reference_index):
        """Empty resample windows result in 0 values (not NaN)."""
        # Data only at start and end, gaps in middle
        index = pd.DatetimeIndex(["2024-01-01 00:00:00", "2024-01-01 01:00:00"])
        df = pd.DataFrame(
            {
                "dose": [5.0, 10.0],
                "is_bolus": [True, False],
                "is_basal": [False, True],
                "type": ["", ""],
            },
            index=index,
        )

        result = aligner._align_insulin(df, reference_index, "5min")

        # Middle windows should be 0, not NaN
        assert result.loc["2024-01-01 00:05:00", "bolus_dose"] == 0.0
        assert result.loc["2024-01-01 00:30:00", "basal_dose"] == 0.0
        assert not result["bolus_dose"].isna().any()
        assert not result["basal_dose"].isna().any()

    def test_mixed_doses_in_same_window(self, aligner, reference_index):
        """Window with both basal and bolus doses sums each type separately."""
        index = pd.DatetimeIndex(
            [
                "2024-01-01 00:03:00",
                "2024-01-01 00:04:00",
                "2024-01-01 00:06:00",
            ]
        )
        df = pd.DataFrame(
            {
                "dose": [5.0, 10.0, 3.0],
                "is_bolus": [True, False, True],
                "is_basal": [False, True, False],
                "type": ["", "", ""],
            },
            index=index,
        )

        result = aligner._align_insulin(df, reference_index, "5min")

        # All three doses round to same window, should sum by type
        assert result.loc["2024-01-01 00:05:00", "bolus_dose"] == 8.0  # 5.0 + 3.0
        assert result.loc["2024-01-01 00:05:00", "basal_dose"] == 10.0


class TestAlignInsulinReferenceIndex:
    """Test different reference index scenarios."""

    def test_reference_index_longer_than_data(self, aligner):
        """Reference index extending beyond data results in 0."""
        # Data from 00:00 to 00:20
        data_index = pd.date_range("2024-01-01 00:00", periods=3, freq="10min")
        df = pd.DataFrame(
            {
                "dose": [5.0, 10.0, 3.0],
                "is_bolus": [True, False, True],
                "is_basal": [False, True, False],
                "type": ["", "", ""],
            },
            index=data_index,
        )

        # Reference extends to 01:00
        ref_index = pd.date_range("2024-01-01 00:00", "2024-01-01 01:00", freq="5min")

        result = aligner._align_insulin(df, ref_index, "5min")

        assert len(result) == len(ref_index)
        # Later times should be 0
        assert result.loc["2024-01-01 00:30:00", "bolus_dose"] == 0.0
        assert result.loc["2024-01-01 00:30:00", "basal_dose"] == 0.0

    def test_reference_index_shorter_than_data(self, aligner):
        """Reference index shorter than data only returns overlapping period."""
        # Data from 00:00 to 01:00
        data_index = pd.date_range("2024-01-01 00:00", "2024-01-01 01:00", freq="10min")
        df = pd.DataFrame(
            {
                "dose": [5.0, 10.0, 3.0, 12.0, 6.0, 8.0, 4.0],
                "is_bolus": [True, False, True, False, True, False, True],
                "is_basal": [False, True, False, True, False, True, False],
                "type": [""] * 7,
            },
            index=data_index,
        )

        # Reference only to 00:20
        ref_index = pd.date_range("2024-01-01 00:00", "2024-01-01 00:20", freq="5min")

        result = aligner._align_insulin(df, ref_index, "5min")

        assert len(result) == len(ref_index)
        assert result.index.equals(ref_index)


class TestAlignInsulinFrequencies:
    """Test different frequency parameters."""

    def test_15min_frequency(self, aligner):
        """Alignment works with 15-minute frequency."""
        data_index = pd.date_range("2024-01-01 00:00", periods=5, freq="7min")
        df = pd.DataFrame(
            {
                "dose": [5.0, 10.0, 3.0, 12.0, 6.0],
                "is_bolus": [True, False, True, False, True],
                "is_basal": [False, True, False, True, False],
                "type": [""] * 5,
            },
            index=data_index,
        )

        ref_index = pd.date_range("2024-01-01 00:00", "2024-01-01 01:00", freq="15min")

        result = aligner._align_insulin(df, ref_index, "15min")

        assert len(result) == len(ref_index)
        assert result.index.equals(ref_index)

    def test_1hour_frequency(self, aligner):
        """Alignment works with 1-hour frequency."""
        data_index = pd.date_range("2024-01-01 00:00", periods=7, freq="10min")
        df = pd.DataFrame(
            {
                "dose": [5.0, 10.0, 3.0, 12.0, 6.0, 8.0, 4.0],
                "is_bolus": [True, False, True, False, True, False, True],
                "is_basal": [False, True, False, True, False, True, False],
                "type": [""] * 7,
            },
            index=data_index,
        )

        ref_index = pd.date_range("2024-01-01 00:00", "2024-01-01 03:00", freq="1h")

        result = aligner._align_insulin(df, ref_index, "1h")

        assert len(result) == len(ref_index)
        assert result.index.equals(ref_index)


class TestAlignInsulinEdgeCases:
    """Test edge cases and special scenarios."""

    def test_only_bolus_doses(self, aligner, reference_index):
        """Data with only bolus doses works correctly."""
        index = pd.date_range("2024-01-01 00:00", periods=3, freq="10min")
        df = pd.DataFrame(
            {
                "dose": [5.0, 3.0, 7.0],
                "is_bolus": [True, True, True],
                "is_basal": [False, False, False],
                "type": [""] * 3,
            },
            index=index,
        )

        result = aligner._align_insulin(df, reference_index, "5min")

        assert result["bolus_dose"].sum() > 0
        assert result["basal_dose"].sum() == 0

    def test_only_basal_doses(self, aligner, reference_index):
        """Data with only basal doses works correctly."""
        index = pd.date_range("2024-01-01 00:00", periods=3, freq="10min")
        df = pd.DataFrame(
            {
                "dose": [10.0, 12.0, 9.0],
                "is_bolus": [False, False, False],
                "is_basal": [True, True, True],
                "type": [""] * 3,
            },
            index=index,
        )

        result = aligner._align_insulin(df, reference_index, "5min")

        assert result["basal_dose"].sum() > 0
        assert result["bolus_dose"].sum() == 0

    def test_type_column_not_used_in_alignment(self, aligner, reference_index):
        """Type column is ignored during alignment (only is_basal/is_bolus used)."""
        index = pd.date_range("2024-01-01 00:00", periods=2, freq="10min")
        df = pd.DataFrame(
            {
                "dose": [5.0, 10.0],
                "is_bolus": [True, False],
                "is_basal": [False, True],
                "type": ["novorapid", "levemir"],  # Type present but not used
            },
            index=index,
        )

        result = aligner._align_insulin(df, reference_index, "5min")

        # Should work correctly, type column ignored
        assert "type" not in result.columns
        assert result.loc["2024-01-01 00:00:00", "bolus_dose"] == 5.0
        assert result.loc["2024-01-01 00:10:00", "basal_dose"] == 10.0
