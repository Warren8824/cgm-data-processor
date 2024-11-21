def analyse_glucose_gaps(aligned_df: pd.DataFrame, show_top_n: int = 10) -> dict:
    """
    Analyzes gaps in glucose readings with detailed information about largest gaps.

    Args:
        aligned_df: DataFrame with 5-min interval index and columns including
                   'mg_dl' and 'mmol_l'
        show_top_n: Number of largest gaps to show details for

    Returns:
        Dictionary containing gap analysis including detailed info about largest gaps
    """
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
        lambda x: f"{int(x['length_minutes'] // 60)}h {int(x['length_minutes'] % 60)}m",
        axis=1
    )

    return {
        'total_gaps': len(gaps_df),
        'largest_gaps': largest_gaps,
        'gaps_df': gaps_df
    }