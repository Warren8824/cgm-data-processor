"""Cleans and classifies insulin data into bolus and basal doses."""
import json

import pandas as pd


def clean_classify_insulin(df, bolus_limit=8, max_limit=15) -> pd.DataFrame:
    """
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
    df_clean = df[df["insulin"] > 0.0].copy()
    df_clean = df_clean[~df_clean.index.duplicated(keep="first")]

    # Initialize columns
    df_clean["bolus"] = 0.0
    df_clean["basal"] = 0.0
    # Initialize with explicit bool dtype and set to False
    df_clean["labeled_insulin"] = pd.Series(False, index=df_clean.index, dtype=bool)

    # Process labeled insulin from JSON
    for idx, row in df_clean.iterrows():
        try:
            insulin_data = json.loads(row["insulinJSON"])
            if insulin_data and isinstance(insulin_data, list):
                insulin_type = insulin_data[0].get("insulin", "").lower()
                if "novorapid" in insulin_type:
                    df_clean.at[idx, "bolus"] = row["insulin"]
                    df_clean.at[
                        idx, "labeled_insulin"
                    ] = True  # Only mark as labeled if explicitly tagged
                elif "levemir" in insulin_type:
                    df_clean.at[idx, "basal"] = row["insulin"]
                    df_clean.at[
                        idx, "labeled_insulin"
                    ] = True  # Only mark as labeled if explicitly tagged
        except (json.JSONDecodeError, IndexError, KeyError, AttributeError):
            continue

    # Create a mask for unlabeled insulin doses and for doses above 15 units
    unlabeled = (df_clean["bolus"] == 0) & (df_clean["basal"] == 0)
    valid_insulin = df_clean["insulin"] <= max_limit

    # Drop insulin doses which remain unlabeled and fall outside our defined range - > 15 units
    df_clean = df_clean[~(unlabeled & ~valid_insulin)]

    # Classify remaining valid unlabeled insulin based on units - 1-8 = Bolus, >8 = Basal
    # Note: These remain flagged as unlabeled even after classification
    df_clean.loc[
        unlabeled & valid_insulin & (df_clean["insulin"] <= bolus_limit), "bolus"
    ] = df_clean["insulin"]
    df_clean.loc[
        unlabeled & valid_insulin & (df_clean["insulin"] > bolus_limit), "basal"
    ] = df_clean["insulin"]

    # Return dataframe containing only insulin related data
    df_clean = df_clean[["basal", "bolus", "labeled_insulin"]]

    return df_clean
