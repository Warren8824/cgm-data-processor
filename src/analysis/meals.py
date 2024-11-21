import pandas as pd
from datetime import timedelta
from typing import Dict
from .config import MealQuality, MealAnalysisConfig


def analyse_meal_data(aligned_df: pd.DataFrame, config: MealAnalysisConfig = None) -> pd.DataFrame:
    """
    Analyses diabetes data for meal analysis suitability and handles missing data interpolation, using
    MealAnalysisConfig variables if not overwritten and interpolates wheres suitable.

    Processes the data in these steps:
    1. Analyses each meal period (4h post-meal by default)
    2. Categorises meal quality based on missing data patterns
    3. Interpolates missing glucose values within acceptable gaps
    4. Marks quality and interpolation status

    Args:
        aligned_df: DataFrame with 5-min aligned diabetes data
                   Must have columns: mg_dl, mmol_l, carbs
        config: Optional MealAnalysisConfig object with analysis parameters

    Returns:
        DataFrame with:
        - Interpolated glucose values where appropriate
        - Additional columns:
            - has_missing_data: Boolean, True if any missing BG in post-meal period
            - gap_duration_mins: Maximum gap duration in post-meal period
            - missing_pct: Percentage of missing readings in post-meal period
            - meal_quality: Category from MealQuality enum
            - skip_meal: Boolean, True if meal should be excluded from analysis
            - interpolated: Boolean, True if value was interpolated
    """
    if config is None:
        config = MealAnalysisConfig()

    # Create copy to avoid modifying original
    df = aligned_df.copy()

    # Initialize new columns
    df['has_missing_data'] = False
    df['gap_duration_mins'] = 0.0
    df['missing_pct'] = 0.0
    df['meal_quality'] = None
    df['skip_meal'] = False
    df['interpolated'] = False

    # Number of 5-min intervals in post-meal period
    intervals = config.post_meal_hours * 12

    # First pass: Analyze gaps and mark meal quality
    meal_rows = df[df['carbs'] > config.min_carbs].index

    for meal_time in meal_rows:
        # Get post-meal period
        end_time = meal_time + pd.Timedelta(hours=config.post_meal_hours)
        post_meal = df[meal_time:end_time]

        # Skip if we don't have enough future data
        if len(post_meal) < intervals:
            df.loc[meal_time, 'skip_meal'] = True
            df.loc[meal_time, 'meal_quality'] = MealQuality.UNUSABLE.value
            continue

        # Analyze missing data
        missing_mask = post_meal['mg_dl'].isna()
        df.loc[meal_time, 'has_missing_data'] = missing_mask.any()

        # Calculate missing percentage
        missing_pct = missing_mask.mean()
        df.loc[meal_time, 'missing_pct'] = missing_pct * 100

        # Find longest gap
        gap_duration = 0
        current_gap = 0

        for is_missing in missing_mask:
            if is_missing:
                current_gap += 5  # 5-minute intervals
                gap_duration = max(gap_duration, current_gap)
            else:
                current_gap = 0

        df.loc[meal_time, 'gap_duration_mins'] = gap_duration

        # Determine meal quality
        if not missing_mask.any():
            quality = MealQuality.CLEAN
            skip = False
        elif gap_duration <= config.usable_gap_mins and missing_pct <= config.usable_missing_pct:
            quality = MealQuality.USABLE
            skip = False
        elif gap_duration <= config.max_gap_mins and missing_pct <= config.max_missing_pct:
            quality = MealQuality.BORDERLINE
            skip = False
        else:
            quality = MealQuality.UNUSABLE
            skip = True

        df.loc[meal_time, 'meal_quality'] = quality.value
        df.loc[meal_time, 'skip_meal'] = skip

    # Second pass: Interpolate missing data where appropriate
    # Only interpolate for non-skipped meals
    usable_meals = df[
        (df['carbs'] > config.min_carbs) &
        (~df['skip_meal'])
        ].index

    for meal_time in usable_meals:
        end_time = meal_time + pd.Timedelta(hours=config.post_meal_hours)
        post_meal_idx = df[meal_time:end_time].index

        # Interpolate glucose values
        original_mg_dl = df.loc[post_meal_idx, 'mg_dl'].copy()
        original_mmol_l = df.loc[post_meal_idx, 'mmol_l'].copy()

        # Use time-based interpolation with limit
        df.loc[post_meal_idx, 'mg_dl'] = df.loc[post_meal_idx, 'mg_dl'].interpolate(
            method='time',
            limit=config.interpolation_limit
        )
        df.loc[post_meal_idx, 'mmol_l'] = df.loc[post_meal_idx, 'mmol_l'].interpolate(
            method='time',
            limit=config.interpolation_limit
        )

        # Mark interpolated values
        df.loc[post_meal_idx, 'interpolated'] = (
                df.loc[post_meal_idx, 'mg_dl'].notna() &
                original_mg_dl.isna()
        )

    return df