"""Abstract base for data processors with automatic processor selection."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Type

import pandas as pd

from src.core.data_types import (
    ColumnMapping,
    DataType,
    DeviceFormat,
    TableStructure,
    Unit,
)
from src.core.exceptions import ProcessingError
from src.readers.base import TableData

logger = logging.getLogger(__name__)


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


@dataclass
class ProcessedTypeData:
    """Holds processed data for a single data type."""

    dataframe: pd.DataFrame
    source_units: Dict[str, Unit]  # Maps column name to its original unit
    processing_notes: List[str]


class BaseTypeProcessor(ABC):
    """Abstract base class for individual data type processors."""

    def _generate_column_name(
        self, data_type: DataType, is_primary: bool, index: int
    ) -> str:
        """Generate standardized column names."""
        base_name = data_type.name.lower()
        if is_primary:
            return f"{base_name}_primary"
        return f"{base_name}_{index + 1}"

    def validate_units(self, data_type: DataType, source_unit: Unit) -> None:
        """Validate that units are compatible with data type.

        Args:
            data_type: Type of data being validated
            source_unit: Unit to validate for the data type

        Raises:
            ProcessingError: If the unit is not valid for the given data type

        Returns:
            None
        """
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

    def _combine_and_rename_columns(
        self, columns: List[ColumnData], data_type: DataType
    ) -> Tuple[pd.DataFrame, Dict[str, Unit]]:
        """Combine multiple columns into a single DataFrame with standardized names."""
        try:
            # Sort columns to ensure primary comes first
            sorted_columns = sorted(columns, key=lambda x: (not x.is_primary))

            combined_df = pd.DataFrame(index=pd.DatetimeIndex([]))
            column_units = {}

            # Process primary column first, then others
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
            logger.error("Error combining columns: %s", str(e))
            raise ProcessingError(f"Failed to combine columns: {str(e)}") from e

    @abstractmethod
    def process_type(self, columns: List[ColumnData]) -> ProcessedTypeData:
        """Process all data of a specific type."""


class DataProcessor:
    """Main processor class that handles processing of all data types."""

    _type_processors: Dict[DataType, Type[BaseTypeProcessor]] = {}

    # Define defaults for insulin classification centrally
    DEFAULT_INSULIN_BOLUS_LIMIT: float = 8.0
    DEFAULT_INSULIN_MAX_DOSE: float = 15.0

    @staticmethod
    def create_table_configs(
        detected_format: DeviceFormat,
    ) -> Dict[str, TableStructure]:
        """
        Creates a table configuration dictionary from detected format.

        Args:
            detected_format: Format object containing files and their table configurations

        Returns:
            Dict[str, TableStructure]: Dictionary mapping table names to their structures
        """
        try:
            return {
                table.name: table
                for file_config in detected_format.files
                for table in file_config.tables
            }
        except Exception as e:
            logger.error("Failed to create table configurations: %s", str(e))
            raise ProcessingError("Failed to create table configurations") from e

    def process_tables(
        self,
        table_data: Dict[str, TableData],
        detected_format: DeviceFormat,
        interpolation_limit: Optional[
            Any
        ] = None,  # Optional parameter for CGM processor
        bolus_limit: Optional[
            float
        ] = None,  # Optional parameters for insulin processor
        max_dose: Optional[float] = None,
    ) -> Dict[DataType, ProcessedTypeData]:
        """
        Process all tables according to their configuration.

        Args:
            table_data: Dictionary mapping table names to their data
            detected_format: Format object containing table configurations
            interpolation_limit: Max length of gaps to interpolate
            bolus_limit: Maximum insulin dose to be classified as bolus(default = 8)
            max_dose: Maximum insulin dose - all over will be discarded

        Returns:
            Dict[DataType, ProcessedTypeData]: Processed data organized by type
        """
        table_configs = self.create_table_configs(detected_format)

        # Rest of your existing process_tables implementation
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

        # Process each data type
        results = {}
        for data_type, columns in type_data.items():
            try:
                processor = self.get_processor_for_type(data_type)

                # Inject optional parameters based on processor type
                if data_type == DataType.CGM and interpolation_limit is not None:
                    result = processor.process_type(columns, interpolation_limit)
                elif data_type == DataType.INSULIN:
                    # Use provided values or defaults, but never None
                    final_bolus_limit = (
                        bolus_limit
                        if bolus_limit is not None
                        else self.DEFAULT_INSULIN_BOLUS_LIMIT
                    )
                    final_max_dose = (
                        max_dose
                        if max_dose is not None
                        else self.DEFAULT_INSULIN_MAX_DOSE
                    )
                    result = processor.process_type(
                        columns, final_bolus_limit, final_max_dose
                    )
                else:
                    result = processor.process_type(columns)

                if not result.dataframe.empty:
                    results[data_type] = result

                    col_count = len(columns)
                    primary_count = sum(1 for c in columns if c.is_primary)
                    logger.info(
                        "    \u2713 Processed %s: %d primary and %d secondary columns",
                        data_type.name,
                        primary_count,
                        col_count - primary_count,
                    )

            except ProcessingError as e:
                logger.error("Error processing %s: %s", data_type, str(e))
                continue

        return results

    @classmethod
    def register_processor(cls, data_type: DataType):
        """Register a processor class for a specific data type."""

        def wrapper(processor_cls: Type[BaseTypeProcessor]):
            cls._type_processors[data_type] = processor_cls
            return processor_cls

        return wrapper

    def get_processor_for_type(self, data_type: DataType) -> BaseTypeProcessor:
        """Get appropriate processor instance for the data type."""
        processor_cls = self._type_processors.get(data_type)
        if processor_cls is None:
            raise ProcessingError(
                f"No processor registered for data type: {data_type.value}"
            )
        return processor_cls()
