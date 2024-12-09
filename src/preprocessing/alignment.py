import pandas as pd
from typing import Dict
from datetime import datetime


def align_diabetes_data(
        bg_df: pd.DataFrame,
        carb_df: pd.DataFrame,
        insulin_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Aligns diabetes data (blood glucose, carbohydrates, insulin) to regular 5-minute intervals
    already established in the bg_df dataframe.

    This function takes three dataframes with timestamped diabetes data and produces a single
    dataframe with regular 5-minute intervals. Carbohydrates and insulin entries are summed. This dataset is suitable
    for ML applications where a unified timestamp is required.

    Args:
        bg_df: DataFrame with timestamp index and columns ['mg_dl', 'mmol_l', 'missing']
              Blood glucose readings at irregular intervals
        carb_df: DataFrame with timestamp index and column ['carbs']
                Sporadic carbohydrate entries
        insulin_df: DataFrame with timestamp index and columns ['bolus', 'basal', 'labeled_insulin']
                   Sporadic insulin entries

    Processing steps:
    1. Resample insulin treatment data - sum any entries within each 5-min window
    2. Resample insulin_labeled data - mark as True only if ALL are labeled
    3. Resample carb treatment data - sum any entries within each 5-min window
    4. Combine all data and ensure all intervals exist
    5. Fill missing treatment values with 0 (keep BG as NaN)

    Returns:
        DataFrame with:
        - Regular 5-minute interval index
        - Columns: ['mg_dl', 'mmol_l', 'missing', 'carbs', 'bolus', 'basal', 'labeled_insulin']
        - BG values averaged within intervals, NaN where missing
        - Treatment values summed within intervals, 0 where missing
    """
    # First round timestamps in all dataframes to 5-min intervals
    bg_df = bg_df.copy()
    carb_df = carb_df.copy()
    insulin_df = insulin_df.copy()

    carb_df.index = carb_df.index.round('5min')
    insulin_df.index = insulin_df.index.round('5min')

    # Resample insulin - sum within windows
    insulin_resampled = insulin_df.resample('5min').agg({
        'bolus': 'sum',
        'basal': 'sum',
        'labeled_insulin': 'all'
    })

    # Resample carbs - sum within windows
    carb_resampled = carb_df.resample('5min').agg({
        'carbs': 'sum'
    })

    # Combine all data
    aligned_df = pd.concat([bg_df, carb_resampled, insulin_resampled], axis=1)

    # Fill missing treatment values with 0
    aligned_df['carbs'] = aligned_df['carbs'].fillna(0)
    aligned_df['bolus'] = aligned_df['bolus'].fillna(0)
    aligned_df['basal'] = aligned_df['basal'].fillna(0)
    aligned_df['labeled_insulin'] = aligned_df['labeled_insulin'].fillna(False)

    return aligned_df
