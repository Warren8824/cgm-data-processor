import pandas as pd
import json
from typing import Dict


def clean_classify_insulin(df, bolus_limit=8, max_limit=15):
    """
    Clean and classify insulin data into basal and bolus categories.
    Parameters:
        df: DataFrame with insulin and insulinJSON columns
        bolus_limit: Units threshold for classifying unlabeled insulin as bolus
        max_limit: Maximum units allowed for unlabeled insulin


    Returns:
        df_clean: DataFrame with basal, bolus, and labeled_insulin columns with
        datetime index.
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

    # Process unlabeled insulin
    unlabeled = (df_clean['bolus'] == 0) & (df_clean['basal'] == 0)
    valid_insulin = df_clean['insulin'] <= max_limit

    # Drop insulin doses which remain unlabeled and fall outside our defined range - 1 - 15 units
    df_clean = df_clean[~(unlabeled & ~valid_insulin)]

    # Classify remaining valid unlabeled insulin based on units
    # Note: These remain flagged as unlabeled even after classification
    df_clean.loc[unlabeled & valid_insulin & (df_clean['insulin'] <= bolus_limit), 'bolus'] = df_clean['insulin']
    df_clean.loc[unlabeled & valid_insulin & (df_clean['insulin'] > bolus_limit), 'basal'] = df_clean['insulin']

    # Return dataframe containing only insulin related data
    df_clean = df_clean[['basal', 'bolus', 'labeled_insulin']]

    return df_clean



def clean_classify_carbs(df):
    # Create a copy to avoid altering the original dataframe
    df_clean = df.copy()

    # Keep only rows where carbs is >= 1.0 grams
    df_clean = df_clean[df_clean['carbs'] >= 1.0]

    # Drop rows where the index (timestamp) is duplicated
    df_clean = df_clean[~df_clean.index.duplicated(keep='first')]

    # Return DataFrame containing only meal related data
    df_clean = df_clean[['carbs']]

    return df_clean


def clean_glucose(df):
    # Create copy to avoid altering original dataframe
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

    # Interpolate gaps up to 20 minutes (4 intervals) using vectorized operation
    clean_df['calculated_value'] = clean_df['calculated_value'].interpolate(method='linear', limit=4, limit_direction='forward')

    # Rename the 'calculated_value' column to 'mg_dl'
    clean_df.rename(columns={'calculated_value': 'mg_dl'}, inplace=True)

    # Limit the 'mg_dl' column values to the range 39.64 to 360.36 (2.2 - 20.0 mmol/L)
    clean_df['mg_dl'] = clean_df['mg_dl'].clip(lower=39.64, upper=360.36)

    # Create a new column 'mmol_l' by converting 'calculated_value' from mg/dL to mmol/L
    clean_df['mmol_l'] = clean_df['mg_dl'] * 0.0555

    # Drop all rows except mg_dl and mmol_l
    clean_df = clean_df[['mg_dl', 'mmol_l', 'missing']]

    return clean_df
