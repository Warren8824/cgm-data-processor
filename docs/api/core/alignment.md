# Data Alignment API Reference

The Alignment system provides functionality to synchronize different types of diabetes data (CGM, insulin, carbs, notes) to a common timeline, enabling integrated analysis of diabetes management data.

## Core Components

=== "AlignmentResult"

    ```python
    @dataclass
    class AlignmentResult:
        dataframe: pd.DataFrame    # The aligned timeseries data
        start_time: pd.Timestamp  # Start of aligned timeline
        end_time: pd.Timestamp    # End of aligned timeline
        frequency: str            # Alignment frequency
        processing_notes: List[str] # Notes about the alignment process
    ```

=== "Aligner"

    ```python
    class Aligner:
        def align(
            self,
            processed_data: Dict[DataType, ProcessedTypeData],
            reference_df: pd.DataFrame = None,
            freq: str = "5min",
        ) -> AlignmentResult:
            """Align all data to a reference timeline."""
    ```

## Alignment Process

### Timeline Validation

!!! info "Timeline Requirements"
    The reference timeline must meet these criteria:

    ```python
    def _validate_timeline(self, reference_data: pd.DataFrame, freq: str) -> None:
        # 1. Must not be empty
        if reference_data.empty:
            raise AlignmentError("Reference data is empty")

        # 2. Must have DatetimeIndex
        if not isinstance(reference_data.index, pd.DatetimeIndex):
            raise AlignmentError("Reference data must have DatetimeIndex")

        # 3. Must be monotonically increasing
        if not reference_data.index.is_monotonic_increasing:
            raise AlignmentError("Reference data index must be monotonically increasing")

        # 4. Must match expected frequency
        time_diffs = reference_data.index.to_series().diff()
        modal_diff = time_diffs.mode()[0]
        expected_diff = pd.Timedelta(freq)

        if modal_diff != expected_diff:
            raise AlignmentError(
                f"Reference data frequency {modal_diff} does not match expected {freq}"
            )
    ```

### Data Type Alignment Strategies

=== "Insulin"

    ```python
    def _align_insulin(
        self, df: pd.DataFrame, reference_index: pd.DatetimeIndex, freq: str
    ) -> pd.DataFrame:
        """Align insulin data."""
        # Round timestamps to alignment frequency
        df.index = df.index.round(freq)

        # Split and sum basal/bolus doses separately
        basal_doses = df["dose"].where(df["is_basal"], 0)
        bolus_doses = df["dose"].where(df["is_bolus"], 0)

        # Resample to reference frequency
        result = pd.DataFrame({
            "basal_dose": basal_doses.resample(freq).sum(),
            "bolus_dose": bolus_doses.resample(freq).sum(),
        })

        return result.reindex(reference_index).fillna(0)
    ```

=== "Carbs"

    ```python
    def _align_carbs(
        self, df: pd.DataFrame, reference_index: pd.DatetimeIndex, freq: str
    ) -> pd.DataFrame:
        """Align carbohydrate data."""
        # Round timestamps
        df.index = df.index.round(freq)

        # Sum carbs in each interval
        result = df["carbs_primary"].resample(freq).sum()
        return pd.DataFrame({"carbs_primary": result}).reindex(reference_index).fillna(0)
    ```

=== "Notes"

    ```python
    def _align_notes(
        self, df: pd.DataFrame, reference_index: pd.DatetimeIndex, freq: str
    ) -> pd.DataFrame:
        """Align notes data."""
        # Round timestamps
        df.index = df.index.round(freq)

        # Keep last note in each interval
        result = df["notes_primary"].resample(freq).last()
        return pd.DataFrame({"notes_primary": result}).reindex(reference_index)
    ```

## Usage Examples

### Basic Alignment

```python
from src.core.aligner import Aligner
from src.processors import DataProcessor

# Process data
processor = DataProcessor()
processed_data = processor.process_tables(table_data, table_configs)

# Align data
aligner = Aligner()
aligned_result = aligner.align(processed_data, freq="5min")

# Access aligned data
aligned_df = aligned_result.dataframe
print(f"Aligned from {aligned_result.start_time} to {aligned_result.end_time}")
print(f"Using {aligned_result.frequency} frequency")
```

### Custom Reference Timeline

```python
# Use custom reference timeline instead of CGM
custom_timeline = pd.DataFrame(
    index=pd.date_range(start="2024-01-01", end="2024-01-02", freq="15min")
)

aligned_result = aligner.align(
    processed_data,
    reference_df=custom_timeline,
    freq="15min"
)
```

## Data Type Handling

!!! note "Alignment Strategies"
    Each data type is handled differently based on its characteristics:

    - **CGM Data**: Used as reference timeline by default
    - **Insulin Doses**: Split into basal/bolus and summed within intervals
    - **Carbohydrates**: Summed within intervals
    - **Notes**: Last value within each interval is kept

### Column Naming

The aligned DataFrame includes these columns:

- CGM data (reference):
    - `cgm_primary`
    - `cgm_primary_mmol`
    - `cgm_2`
    - `cgm_2_mmol`
    - `missing_cgm`
- Insulin doses:
    - `basal_dose`
    - `bolus_dose`
- Carbohydrates:
    - `carbs_primary`
    - `carbs_2`
- Notes:
    - `notes_primary`

## Error Handling

```python
try:
    aligned_result = aligner.align(processed_data)
except AlignmentError as e:
    print(f"Alignment failed: {str(e)}")
```

## Best Practices

!!! tip "Alignment Tips"
    1. **Reference Timeline**
        - Use CGM data as reference when available
        - Ensure reference data has consistent frequency
        - Validate timeline before alignment

    2. **Frequency Selection**
        - Match frequency to reference data collection rate
        - Consider memory usage for long time periods
        - Standard frequencies: "5min", "15min", "30min", "1H"

    3. **Data Preparation**
        - Clean and validate data before alignment
        - Handle missing values appropriately
        - Consider timezone consistency

    4. **Performance**
        - Limit alignment range for large datasets
        - Pre-filter unnecessary data
        - Cache aligned results when appropriate

## Integration with Processors

The alignment system works with processed data from type-specific processors:

```python
# Type processors prepare data for alignment
@DataProcessor.register_processor(DataType.CGM)
class CGMProcessor(BaseTypeProcessor):
    def process_type(self, columns: List[ColumnData]) -> ProcessedTypeData:
        # Process and prepare CGM data
        ...

@DataProcessor.register_processor(DataType.INSULIN)
class InsulinProcessor(BaseTypeProcessor):
    def process_type(self, columns: List[ColumnData]) -> ProcessedTypeData:
        # Process and prepare insulin data
        ...

# Alignment uses the processed results
aligner = Aligner()
aligned_data = aligner.align(processed_results)
```