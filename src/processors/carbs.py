"""Cleans and filters carbohydrate data from a DataFrame."""

import pandas as pd


def clean_classify_carbs(df) -> pd.DataFrame:
    """
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
    df_clean = df_clean[df_clean["carbs"] >= 1.0]

    # Drop rows where the index (timestamp) is duplicated
    df_clean = df_clean[~df_clean.index.duplicated(keep="first")]

    # Return DataFrame containing only meal related data
    df_clean = df_clean[["carbs"]]

    return df_clean
