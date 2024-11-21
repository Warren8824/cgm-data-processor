def align_diabetes_data(
        bg_df: pd.DataFrame,
        carb_df: pd.DataFrame,
        insulin_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Aligns diabetes data (blood glucose, carbohydrates, insulin) to regular 5-minute intervals.

    This function takes three dataframes with timestamped diabetes data and produces a single
    dataframe with regular 5-minute intervals. Blood glucose readings are averaged within
    each interval, while carbohydrates and insulin entries are summed.

    Args:
        bg_df: DataFrame with timestamp index and columns ['mg_dl', 'mmol_l']
              Blood glucose readings at irregular intervals
        carb_df: DataFrame with timestamp index and column ['carbs']
                Sporadic carbohydrate entries
        insulin_df: DataFrame with timestamp index and columns ['bolus', 'basal']
                   Sporadic insulin entries

    Processing steps:
    1. Round all timestamps to nearest 5-minute interval
    2. Create complete timeline at 5-minute intervals from earliest to latest data point
    3. Resample BG data - average any readings within each 5-min window
    4. Resample treatment data - sum any entries within each 5-min window
    5. Combine all data and ensure all intervals exist
    6. Fill missing treatment values with 0 (keep BG as NaN)

    Returns:
        DataFrame with:
        - Regular 5-minute interval index
        - Columns: ['mg_dl', 'mmol_l', 'carbs', 'bolus', 'basal']
        - BG values averaged within intervals, NaN where missing
        - Treatment values summed within intervals, 0 where missing
    """
    # First round timestamps in all dataframes to 5-min intervals
    bg_df = bg_df.copy()
    carb_df = carb_df.copy()
    insulin_df = insulin_df.copy()

    bg_df.index = bg_df.index.round('5min')
    carb_df.index = carb_df.index.round('5min')
    insulin_df.index = insulin_df.index.round('5min')

    # Create complete timeline of 5-min intervals
    full_range = pd.date_range(
        start=min(bg_df.index.min(), carb_df.index.min(), insulin_df.index.min()),
        end=max(bg_df.index.max(), carb_df.index.max(), insulin_df.index.max()),
        freq='5min'
    )

    # Resample blood glucose - average within windows
    bg_resampled = bg_df.resample('5min').agg({
        'mg_dl': 'mean',
        'mmol_l': 'mean'
    })

    # Resample carbs - sum within windows
    carb_resampled = carb_df.resample('5min').agg({
        'carbs': 'sum'
    })

    # Resample insulin - sum within windows
    insulin_resampled = insulin_df.resample('5min').agg({
        'bolus': 'sum',
        'basal': 'sum'
    })

    # Combine all data
    aligned_df = pd.concat([bg_resampled, carb_resampled, insulin_resampled], axis=1)

    # Ensure all 5-minute intervals exist
    aligned_df = aligned_df.reindex(full_range)

    # Fill missing treatment values with 0
    aligned_df['carbs'] = aligned_df['carbs'].fillna(0)
    aligned_df['bolus'] = aligned_df['bolus'].fillna(0)
    aligned_df['basal'] = aligned_df['basal'].fillna(0)

    return aligned_df
