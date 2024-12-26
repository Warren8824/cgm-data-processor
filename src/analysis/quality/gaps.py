"""Analyzes gaps in continuous glucose monitoring data."""

import pandas as pd


def analyse_glucose_gaps(aligned_df: pd.DataFrame, show_top_n: int = 10) -> dict:
    """Analyzes gaps in continuous glucose monitoring data.

    Performs detailed analysis of missing glucose readings, including gap counts, durations,
    and statistics. Identifies and provides information about the largest gaps in the data.

    Args:
        aligned_df (pd.DataFrame): DataFrame with 5-minute interval timestamps as index
            and required columns:

                - mg_dl: Blood glucose values in mg/dL

                - mmol_l: Blood glucose values in mmol/L

                - missing: Boolean flag for missing values

        show_top_n (int, optional): Number of largest gaps to analyze in detail.
            Defaults to 10.

    Returns:
        Dict: Dictionary containing gap analysis metrics:

             - initial_missing_count (int): Count of missing values before processing

             - initial_missing_percentage (float): Percentage of missing values before processing

             - total_readings (int): Total number of readings in dataset

             - remaining_missing_count (int): Count of missing values after processing

             - remaining_missing_percentage (float): Percentage of missing values after processing

             - total_gap_minutes (float): Total duration of all gaps in minutes

             - average_gap_minutes (float): Mean gap duration in minutes

             - median_gap_minutes (float): Median gap duration in minutes

             - largest_gaps (pd.DataFrame): Details of top N largest gaps

             - gaps_df (pd.DataFrame): Complete DataFrame of all gaps

    Examples:
        >>> df = pd.DataFrame({
        ...     'mg_dl': [100, np.nan, np.nan, 120],
        ...     'mmol_l': [5.5, np.nan, np.nan, 6.7],
        ...     'missing': [False, True, True, False]
        ... })
        >>> df.index = pd.date_range('2024-01-01', periods=4, freq='5min')
        >>> metrics = analyse_glucose_gaps(df, show_top_n=2)
        >>> print(f"Missing data: {metrics['initial_missing_percentage']}%")
        Missing data: 50.0%
        >>> print(metrics['largest_gaps'][['duration', 'length_minutes']])
                     duration  length_minutes
        0  0h 10m            10.0
    """
    # Calculate initial missing data value and percentage
    total_readings = len(aligned_df)
    initial_missing = aligned_df["missing"].sum()
    initial_missing_percentage = (initial_missing / total_readings) * 100

    # Create mask for all rows with NaN values
    missing_mask = aligned_df["mg_dl"].isna()

    gap_starts = []
    gap_lengths = []
    gap_ends = []  # Added to track end times
    current_start = None

    for _, (time, is_missing) in enumerate(missing_mask.items()):
        if is_missing and current_start is None:
            current_start = time
        elif not is_missing and current_start is not None:
            gap_starts.append(current_start)
            gap_ends.append(time)  # Store end time
            gap_lengths.append((time - current_start).total_seconds() / 60)
            current_start = None

    # Handle case where dataset ends with a gap
    if current_start is not None:
        gap_starts.append(current_start)
        gap_ends.append(missing_mask.index[-1])
        gap_lengths.append(
            (missing_mask.index[-1] - current_start).total_seconds() / 60
        )

    # Create DataFrame with gap details
    gaps_df = pd.DataFrame(
        {"start_time": gap_starts, "end_time": gap_ends, "length_minutes": gap_lengths}
    )

    # Sort by gap length and get details of largest gaps
    largest_gaps = gaps_df.sort_values("length_minutes", ascending=False).head(
        show_top_n
    )

    # Add human-readable duration
    largest_gaps["duration"] = largest_gaps.apply(
        lambda x: f'{int(x["length_minutes"] // 60)}h {int(x["length_minutes"] % 60)}m',
        axis=1,
    )

    # Calculate remaining gaps statistics
    total_gap_minutes = gaps_df["length_minutes"].sum()
    average_gap_minutes = gaps_df["length_minutes"].mean() if len(gaps_df) > 0 else 0
    median_gap_minutes = gaps_df["length_minutes"].median() if len(gaps_df) > 0 else 0
    remaining_missing = aligned_df["mg_dl"].isna().sum()
    remaining_missing_percentage = (remaining_missing / total_readings) * 100

    metrics = {
        "initial_missing_count": int(initial_missing),
        "initial_missing_percentage": round(initial_missing_percentage, 2),
        "total_readings": total_readings,
        "remaining_missing_count": remaining_missing,
        "remaining_missing_percentage": round(remaining_missing_percentage, 2),
        "total_gap_minutes": round(total_gap_minutes, 2),
        "average_gap_minutes": round(average_gap_minutes, 2),
        "median_gap_minutes": round(median_gap_minutes, 2),
        "largest_gaps": largest_gaps,
        "gaps_df": gaps_df,
    }

    return metrics
