# Base Processor API Reference

The Base Processor system provides the foundation for processing different types of diabetes data. It uses a registry pattern with abstract base classes to enable type-specific processing while maintaining consistent interfaces and behavior.

## Core Data Structures

=== "ColumnData"

    ```python
    @dataclass
    class ColumnData:
        """Holds data and metadata for a single column."""
        dataframe: pd.DataFrame  # Single column DataFrame
        unit: Unit
        config: ColumnMapping
        is_primary: bool

        @property
        def data_type(self) -> DataType:
            """Get the data type from the column config."""
            return self.config.data_type
    ```

=== "ProcessedTypeData"

    ```python
    @dataclass
    class ProcessedTypeData:
        """Holds processed data for a single data type."""
        dataframe: pd.DataFrame
        source_units: Dict[str, Unit]  # Maps column name to its original unit
        processing_notes: List[str]
    ```

## Base Type Processor

!!! info "Abstract Base Class"
    `BaseTypeProcessor` defines the interface and common functionality for all type-specific processors.

```python
class BaseTypeProcessor(ABC):
    """Abstract base class for individual data type processors."""

    @abstractmethod
    def process_type(self, columns: List[ColumnData]) -> ProcessedTypeData:
        """Process all data of a specific type."""
```

### Protected Methods

=== "Column Name Generation"

    ```python
    def _generate_column_name(
        self, data_type: DataType, is_primary: bool, index: int
    ) -> str:
        """Generate standardized column names."""
        base_name = data_type.name.lower()
        if is_primary:
            return f"{base_name}_primary"
        return f"{base_name}_{index + 1}"
    ```

=== "Unit Validation"

    ```python
    def _validate_units(self, data_type: DataType, source_unit: Unit) -> None:
        """Validate that units are compatible with data type."""
        valid_units = {
            DataType.CGM: [Unit.MGDL, Unit.MMOL],
            DataType.BGM: [Unit.MGDL, Unit.MMOL],
            DataType.INSULIN: [Unit.UNITS],
            DataType.CARBS: [Unit.GRAMS],
        }

        if data_type not in valid_units:
            raise ProcessingError(f"No unit validation defined for {data_type.value}")

        if source_unit not in valid_units[data_type]:
            raise ProcessingError(
                f"Invalid source unit {source_unit.value} for {data_type.value}"
            )
    ```

=== "Column Combination"

    ```python
    def _combine_and_rename_columns(
        self, columns: List[ColumnData], data_type: DataType
    ) -> Tuple[pd.DataFrame, Dict[str, Unit]]:
        """Combine multiple columns into a single DataFrame with standardized names."""
        try:
            # Sort columns to ensure primary comes first
            sorted_columns = sorted(columns, key=lambda x: (not x.is_primary))

            combined_df = pd.DataFrame(index=pd.DatetimeIndex([]))
            column_units = {}

            # Process each column
            for idx, col_data in enumerate(sorted_columns):
                new_name = self._generate_column_name(
                    data_type, col_data.is_primary, idx
                )

                # Merge with existing data
                temp_df = col_data.dataframe.copy()
                temp_df.columns = [new_name]

                if combined_df.empty:
                    combined_df = temp_df
                else:
                    combined_df = combined_df.join(temp_df, how="outer")

                column_units[new_name] = col_data.unit

            return combined_df, column_units

        except Exception as e:
            raise ProcessingError(f"Failed to combine columns: {str(e)}") from e
    ```

## Main Data Processor

!!! info "Central Processing Class"
    `DataProcessor` manages type-specific processors and handles data routing.

```python
class DataProcessor:
    """Main processor class that handles processing of all data types."""
    _type_processors: Dict[DataType, Type[BaseTypeProcessor]] = {}
```

### Key Methods

=== "Process Tables"

    ```python
    def process_tables(
        self,
        table_data: Dict[str, TableData],
        table_configs: Dict[str, TableStructure]
    ) -> Dict[DataType, ProcessedTypeData]:
        """Process all tables according to their configuration."""
        # Organize data by type
        type_data: Dict[DataType, List[ColumnData]] = {}

        for table_name, data in table_data.items():
            config = table_configs[table_name]

            # Group columns by data type
            for column in config.columns:
                if column.data_type:
                    # Include insulin meta data with insulin data
                    target_type = (
                        DataType.INSULIN
                        if column.data_type == DataType.INSULIN_META
                        else column.data_type
                    )

                    df_subset = data.dataframe[[column.source_name]].copy()
                    df_subset.columns = ["value"]

                    column_data = ColumnData(
                        dataframe=df_subset,
                        unit=column.unit,
                        config=column,
                        is_primary=column.is_primary,
                    )

                    if target_type not in type_data:
                        type_data[target_type] = []

                    type_data[target_type].append(column_data)
    ```

=== "Processor Registration"

    ```python
    @classmethod
    def register_processor(cls, data_type: DataType):
        """Register a processor class for a specific data type."""
        def wrapper(processor_cls: Type[BaseTypeProcessor]):
            cls._type_processors[data_type] = processor_cls
            return processor_cls
        return wrapper
    ```

=== "Processor Selection"

    ```python
    def get_processor_for_type(self, data_type: DataType) -> BaseTypeProcessor:
        """Get appropriate processor instance for the data type."""
        processor_cls = self._type_processors.get(data_type)
        if processor_cls is None:
            raise ProcessingError(
                f"No processor registered for data type: {data_type.value}"
            )
        return processor_cls()
    ```

## Usage Examples

### Creating a Type Processor

```python
@DataProcessor.register_processor(DataType.CGM)
class CGMProcessor(BaseTypeProcessor):
    def process_type(self, columns: List[ColumnData]) -> ProcessedTypeData:
        processing_notes = []
        try:
            # Validate input
            if not any(col.is_primary for col in columns):
                raise ProcessingError("No primary CGM column found")

            # Process data...
            combined_df, column_units = self._combine_and_rename_columns(
                columns, DataType.CGM
            )

            return ProcessedTypeData(
                dataframe=combined_df,
                source_units=column_units,
                processing_notes=processing_notes
            )
        except Exception as e:
            raise ProcessingError(f"Error processing CGM data: {str(e)}") from e
```

### Processing Data

```python
# Initialize processor
processor = DataProcessor()

# Process tables
results = processor.process_tables(table_data, table_configs)

# Access processed data by type
cgm_data = results.get(DataType.CGM)
insulin_data = results.get(DataType.INSULIN)
```

## Best Practices

!!! tip "Implementation Guidelines"
    1. **Type Processor Implementation**
        - Always validate input data
        - Handle primary/secondary column relationships
        - Maintain data type consistency
        - Document processing steps in notes

    2. **Unit Handling**
        - Validate units before processing
        - Convert to standard units if needed
        - Track unit information in results

    3. **Error Handling**
        - Use specific error types
        - Include context in error messages
        - Handle cleanup in error cases

    4. **Performance**
        - Process columns efficiently
        - Handle large datasets appropriately
        - Use vectorized operations where possible