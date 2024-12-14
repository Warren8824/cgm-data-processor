import pandas as pd
from typing import Dict


def analyse_glucose_gaps(aligned_df: pd.DataFrame, show_top_n: int = 10) -> dict:
    """
    Analyzes gaps in glucose readings with detailed information about largest gaps.

    Args:
        aligned_df: DataFrame with 5-min interval index and columns including
                   'mg_dl', 'mmol_l' and 'missing'
        show_top_n: Number of largest gaps to show details for

    Returns:
        Dictionary containing gap analysis including detailed info about largest gaps
    """

    # Calculate initial missing data value and percentage
    total_readings = len(aligned_df)
    initially_missing = aligned_df['missing'].sum()
    missing_percentage = (initially_missing / total_readings) * 100

    # Create mask for all rows with NaN values
    missing_mask = aligned_df['mg_dl'].isna()

    gap_starts = []
    gap_lengths = []
    gap_ends = []  # Added to track end times
    current_start = None

    for idx, (time, is_missing) in enumerate(missing_mask.items()):
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
        gap_lengths.append((missing_mask.index[-1] - current_start).total_seconds() / 60)

    # Create DataFrame with gap details
    gaps_df = pd.DataFrame({
        'start_time': gap_starts,
        'end_time': gap_ends,
        'length_minutes': gap_lengths
    })

    # Sort by gap length and get details of largest gaps
    largest_gaps = gaps_df.sort_values('length_minutes', ascending=False).head(show_top_n)

    # Add human-readable duration
    largest_gaps['duration'] = largest_gaps.apply(
        lambda x: f'{int(x["length_minutes"] // 60)}h {int(x["length_minutes"] % 60)}m',
        axis=1
    )

    # Calculate remaining gaps statistics
    total_gap_minutes = gaps_df['length_minutes'].sum()
    average_gap_minutes = gaps_df['length_minutes'].mean() if len(gaps_df) > 0 else 0
    median_gap_minutes = gaps_df['length_minutes'].median() if len(gaps_df) > 0 else 0
    remaining_gaps = len(gaps_df)
    gaps_percentage = (remaining_gaps / total_readings) * 100

    metrics = {
        'initial_missing_percentage': round(missing_percentage, 2),
        'initial_missing_count': int(initially_missing),
        'total_readings': total_readings,
        'total_gaps': len(gaps_df),
        'gaps_percentage': round(gaps_percentage, 2),
        'total_gap_minutes': round(total_gap_minutes, 2),
        'average_gap_minutes': round(average_gap_minutes, 2),
        'median_gap_minutes': round(median_gap_minutes, 2),
        'largest_gaps': largest_gaps,
        'gaps_df': gaps_df
    }

    return metrics
