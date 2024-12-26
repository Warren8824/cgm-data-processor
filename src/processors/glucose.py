"""Cleans and processes glucose measurement data."""
import numpy as np
import pandas as pd


def clean_glucose(df, interpolation_limit=4) -> pd.DataFrame:
    """
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
    clean_df.index = clean_df.index.round("5min")

    # Keep only the numeric 'calculated_value' column before grouping
    clean_df = clean_df[["calculated_value"]]

    # Create complete 5-minute interval index
    full_index = pd.date_range(
        start=clean_df.index.min(), end=clean_df.index.max(), freq="5min"
    )

    # Reindex to include all intervals and handle duplicate times
    clean_df = clean_df.groupby(level=0).mean().reindex(full_index)

    # Create a flag for all rows with missing data
    clean_df["missing"] = clean_df["calculated_value"].isna()

    # Create groups of consecutive missing values
    # When missing values change (True to False or vice versa), the cumsum increases
    clean_df["gap_group"] = (~clean_df["missing"]).cumsum()

    # Within each False group (where missing=True), count the group size
    gap_sizes = clean_df[clean_df["missing"]].groupby("gap_group").size()

    # Identify gap groups that are larger than interpolation_limit
    large_gaps = gap_sizes[gap_sizes > interpolation_limit].index

    # Interpolate all gaps initially
    clean_df["calculated_value"] = clean_df["calculated_value"].interpolate(
        method="linear", limit=interpolation_limit, limit_direction="forward"
    )

    # Reset the interpolated values back to NaN for large gaps
    for gap_group in large_gaps:
        mask = (clean_df["gap_group"] == gap_group) & clean_df["missing"]
        clean_df.loc[mask, "calculated_value"] = np.nan

    # Rename the 'calculated_value' column to 'mg_dl'
    clean_df.rename(columns={"calculated_value": "mg_dl"}, inplace=True)

    # Limit the 'mg_dl' column values to the range 39.64 to 360.36 (2.2 - 20.0 mmol/L)
    clean_df["mg_dl"] = clean_df["mg_dl"].clip(lower=39.64, upper=360.36)

    # Create a new column 'mmol_l' by converting 'calculated_value' from mg/dL to mmol/L
    clean_df["mmol_l"] = clean_df["mg_dl"] * 0.0555

    # Drop all columns except mg_dl and mmol_l
    clean_df = clean_df[["mg_dl", "mmol_l", "missing"]]

    return clean_df
