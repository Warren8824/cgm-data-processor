import pandas as pd
import numpy as np
import json
from typing import Dict


def clean_classify_insulin(df, bolus_limit=8, max_limit=15) -> pd.DataFrame:
    """Cleans and classifies insulin data into bolus and basal doses.

       Processes insulin data by classifying doses into bolus or basal categories based on
       JSON labels and dose amounts. Removes duplicates and handles unlabeled doses using
       configurable thresholds.

       Args:
           df (pd.DataFrame): DataFrame with datetime index and columns:

               - insulin: Insulin doses in units

               - insulinJSON: JSON string containing insulin type information

           bolus_limit (float, optional): Maximum insulin units to classify as bolus
               for unlabeled doses. Defaults to 8.0 units.

           max_limit (float, optional): Maximum valid insulin dose. Doses above this
               are dropped if unlabeled. Defaults to 15.0 units.

       Returns:
           pd.DataFrame: Cleaned DataFrame with columns:

               - basal: Basal insulin doses in units

               - bolus: Bolus insulin doses in units

               - labeled_insulin: Boolean flag indicating if dose was explicitly labeled

       Examples:
           >>> import pandas as pd
           >>> import json
           >>> data = {
           ...     'insulin': [5.0, 12.0, 7.0, 20.0],
           ...     'insulinJSON': [
           ...         json.dumps([{'insulin': 'NovoRapid'}]),
           ...         json.dumps([{'insulin': 'Levemir'}]),
           ...         '{}',  # Invalid JSON
           ...         '{}'   # Invalid JSON
           ...     ]
           ... }
           >>> index = pd.to_datetime([
           ...     '2024-01-01 08:00:00',
           ...     '2024-01-01 12:00:00',
           ...     '2024-01-01 15:00:00',
           ...     '2024-01-01 20:00:00'
           ... ])
           >>> df = pd.DataFrame(data, index=index)
           >>> clean_df = clean_classify_insulin(df)
           >>> print(clean_df)
                               basal  bolus  labeled_insulin
           2024-01-01 08:00:00   0.0    5.0            True
           2024-01-01 12:00:00  12.0    0.0            True
           2024-01-01 15:00:00   0.0    7.0           False
           # Note: 20.0 unit dose was dropped as it exceeded max_limit
       """
    df_clean = df[df['insulin'] > 0.0].copy()
    df_clean = df_clean[~df_clean.index.duplicated(keep='first')]

    # Initialize columns
    df_clean['bolus'] = 0.0
    df_clean['basal'] = 0.0
    # Initialize with explicit bool dtype and set to False
    df_clean['labeled_insulin'] = pd.Series(False, index=df_clean.index, dtype=bool)

    # Process labeled insulin from JSON
    for idx, row in df_clean.iterrows():
        try:
            insulin_data = json.loads(row['insulinJSON'])
            if insulin_data and isinstance(insulin_data, list):
                insulin_type = insulin_data[0].get('insulin', '').lower()
                if 'novorapid' in insulin_type:
                    df_clean.at[idx, 'bolus'] = row['insulin']
                    df_clean.at[idx, 'labeled_insulin'] = True  # Only mark as labeled if explicitly tagged
                elif 'levemir' in insulin_type:
                    df_clean.at[idx, 'basal'] = row['insulin']
                    df_clean.at[idx, 'labeled_insulin'] = True  # Only mark as labeled if explicitly tagged
        except (json.JSONDecodeError, IndexError, KeyError, AttributeError):
            continue

    # Create a mask for unlabeled insulin doses and for doses above 15 units
    unlabeled = (df_clean['bolus'] == 0) & (df_clean['basal'] == 0)
    valid_insulin = df_clean['insulin'] <= max_limit

    # Drop insulin doses which remain unlabeled and fall outside our defined range - > 15 units
    df_clean = df_clean[~(unlabeled & ~valid_insulin)]

    # Classify remaining valid unlabeled insulin based on units - 1-8 = Bolus, >8 = Basal
    # Note: These remain flagged as unlabeled even after classification
    df_clean.loc[unlabeled & valid_insulin & (df_clean['insulin'] <= bolus_limit), 'bolus'] = df_clean['insulin']
    df_clean.loc[unlabeled & valid_insulin & (df_clean['insulin'] > bolus_limit), 'basal'] = df_clean['insulin']

    # Return dataframe containing only insulin related data
    df_clean = df_clean[['basal', 'bolus', 'labeled_insulin']]

    return df_clean


def clean_classify_carbs(df) -> pd.DataFrame:
    """Cleans and filters carbohydrate data from a DataFrame.

        Processes a DataFrame containing carbohydrate intake data by filtering
        for significant meals (≥1g carbs) and removing duplicate timestamps.

        Args:
            df (pd.DataFrame): DataFrame with a datetime index and 'carbs' column
                representing carbohydrate intake in grams.

        Returns:
            pd.DataFrame: Cleaned DataFrame containing only the 'carbs' column,
                filtered for meals ≥1g and with duplicate timestamps removed.

        Examples:
            >>> import pandas as pd
            >>> data = {
            ...     'carbs': [15.0, 0.5, 30.0, 15.0],
            ...     'other_col': ['a', 'b', 'c', 'd']
            ... }
            >>> index = pd.to_datetime([
            ...     '2024-01-01 08:00:00',
            ...     '2024-01-01 10:00:00',
            ...     '2024-01-01 12:00:00',
            ...     '2024-01-01 12:00:00'  # Duplicate timestamp
            ... ])
            >>> df = pd.DataFrame(data, index=index)
            >>> clean_df = clean_classify_carbs(df)
            >>> print(clean_df)
                                carbs
            2024-01-01 08:00:00  15.0
            2024-01-01 12:00:00  30.0
        """
    # Create a copy to avoid altering the original dataframe
    df_clean = df.copy()

    # Keep only rows where carbs is >= 1.0 grams
    df_clean = df_clean[df_clean['carbs'] >= 1.0]

    # Drop rows where the index (timestamp) is duplicated
    df_clean = df_clean[~df_clean.index.duplicated(keep='first')]

    # Return DataFrame containing only meal related data
    df_clean = df_clean[['carbs']]

    return df_clean


def clean_glucose(df, interpolation_limit=4) -> pd.DataFrame:
    """Cleans and processes glucose measurement data.

        Processes continuous glucose monitoring data by standardizing timestamps,
        handling missing values through interpolation, and converting units.

        Args:
            df (pd.DataFrame): DataFrame with datetime index and 'calculated_value'
                column containing glucose measurements in mg/dL.

            interpolation_limit (int, optional): Maximum number of consecutive
                missing values to interpolate. Defaults to 4 (20 minutes at 5-min intervals).

        Returns:
            pd.DataFrame: Cleaned DataFrame with columns:

                - mg_dl: Glucose values in mg/dL (range: 39.64-360.36)

                - mmol_l: Glucose values in mmol/L (range: 2.2-20.0)

                - missing: Boolean flag indicating originally missing values

        Examples:
            >>> import pandas as pd
            >>> import numpy as np
            >>> data = {
            ...     'calculated_value': [100, np.nan, np.nan, 120, 400],
            ...     'other_col': ['a', 'b', 'c', 'd', 'e']
            ... }
            >>> index = pd.to_datetime([
            ...     '2024-01-01 08:00:00',
            ...     '2024-01-01 08:03:00',  # Will be rounded to 08:05
            ...     '2024-01-01 08:07:00',  # Will be rounded to 08:05
            ...     '2024-01-01 08:10:00',
            ...     '2024-01-01 08:15:00'
            ... ])
            >>> df = pd.DataFrame(data, index=index)
            >>> clean_df = clean_glucose(df, interpolation_limit=2)
            >>> print(clean_df)
                                mg_dl  mmol_l  missing
            2024-01-01 08:00:00  100.0    5.55   False
            2024-01-01 08:05:00  110.0    6.11    True
            2024-01-01 08:10:00  120.0    6.66   False
            2024-01-01 08:15:00  360.36  20.00   False
        """
    # Create a copy to avoid altering original dataframe
    clean_df = df.copy()

    # Round all timestamps to nearest 5 minute interval
    clean_df.index = clean_df.index.round('5min')

    # Keep only the numeric 'calculated_value' column before grouping
    clean_df = clean_df[['calculated_value']]

    # Create complete 5-minute interval index
    full_index = pd.date_range(
        start=clean_df.index.min(),
        end=clean_df.index.max(),
        freq='5min'
    )

    # Reindex to include all intervals and handle duplicate times
    clean_df = clean_df.groupby(level=0).mean().reindex(full_index)

    # Create a flag for all rows with missing data
    clean_df['missing'] = clean_df['calculated_value'].isna()

    # Create groups of consecutive missing values
    # When missing values change (True to False or vice versa), the cumsum increases
    clean_df['gap_group'] = (~clean_df['missing']).cumsum()

    # Within each False group (where missing=True), count the group size
    gap_sizes = clean_df[clean_df['missing']].groupby('gap_group').size()

    # Identify gap groups that are larger than interpolation_limit
    large_gaps = gap_sizes[gap_sizes > interpolation_limit].index

    # Interpolate all gaps initially
    clean_df['calculated_value'] = clean_df['calculated_value'].interpolate(
        method='linear',
        limit=interpolation_limit,
        limit_direction='forward'
    )

    # Reset the interpolated values back to NaN for large gaps
    for gap_group in large_gaps:
        mask = (clean_df['gap_group'] == gap_group) & clean_df['missing']
        clean_df.loc[mask, 'calculated_value'] = np.nan

    # Rename the 'calculated_value' column to 'mg_dl'
    clean_df.rename(columns={'calculated_value': 'mg_dl'}, inplace=True)

    # Limit the 'mg_dl' column values to the range 39.64 to 360.36 (2.2 - 20.0 mmol/L)
    clean_df['mg_dl'] = clean_df['mg_dl'].clip(lower=39.64, upper=360.36)

    # Create a new column 'mmol_l' by converting 'calculated_value' from mg/dL to mmol/L
    clean_df['mmol_l'] = clean_df['mg_dl'] * 0.0555

    # Drop all columns except mg_dl and mmol_l
    clean_df = clean_df[['mg_dl', 'mmol_l', 'missing']]

    return clean_df
