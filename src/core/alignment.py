"""Aligns diabetes data (blood glucose, carbohydrates, insulin) to regular 5-minute intervals
    already established in the bg_df dataframe.
    """
import pandas as pd


def align_diabetes_data(
    bg_df: pd.DataFrame, carb_df: pd.DataFrame, insulin_df: pd.DataFrame
) -> pd.DataFrame:
    """
    This function takes three dataframes with timestamped diabetes data and produces a single
    dataframe with regular 5-minute intervals. Carbohydrates and insulin entries are summed. This
    dataset is suitable for ML, and other applications where a unified timestamp is required.

    Args:
        bg_df: DataFrame with timestamp index and columns ['mg_dl', 'mmol_l', 'missing']
              Blood glucose readings at irregular intervals
        carb_df: DataFrame with timestamp index and column ['carbs']
                Sporadic carbohydrate entries
        insulin_df: DataFrame with timestamp index and columns ['bolus', 'basal', 'labeled_insulin']
                   Sporadic insulin entries

    Processing steps:

    1. Create copies of dataframes to avoid warnings

    2. Round carbs_df and insulin_df timestamps to nearest 5 minutes

    3. Resample insulin treatment data - sum any entries within each 5-min window

    4. Reindex this dataframe to bg_df.index to align timestamps

    5. Fill missing insulin_labeled rows(where bg_df has index and insulin_resampled does not)
       with False

    6. Resample carb treatment data - sum any entries within each 5-min window

    7. Reindex this dataframe to bg_df.index to align timestamps

    8. Combine all data and ensure all intervals exist

    9. Fill missing treatment values with 0 (keep BG as NaN)

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

    # Round index timestamps to nearest 5 minute intervals
    carb_df.index = carb_df.index.round("5min")
    insulin_df.index = insulin_df.index.round("5min")

    # Resample and reindex insulin - sum within windows
    insulin_resampled = (
        insulin_df.resample("5min")
        .agg(
            {
                "bolus": "sum",
                "basal": "sum",
                # Use a lambda to ensure empty groups are explicitly False - Empty groups equal True by
                # default
                "labeled_insulin": lambda x: x.all() if len(x) > 0 else False,
            }
        )
        .reindex(bg_df.index)
    )

    # Fill missing labeled_insulin values with False, explicitly astype boolean to avoid warnings
    insulin_resampled["labeled_insulin"] = (
        insulin_resampled["labeled_insulin"].astype("boolean").fillna(False)
    )

    # Resample and reindex carbs - sum within windows
    carb_resampled = carb_df.resample("5min").agg({"carbs": "sum"}).reindex(bg_df.index)

    # Combine all data
    aligned_df = pd.concat([bg_df, carb_resampled, insulin_resampled], axis=1)

    # Fill missing treatment values with 0
    aligned_df["carbs"] = aligned_df["carbs"].fillna(0)
    aligned_df[["basal", "bolus"]] = aligned_df[["basal", "bolus"]].fillna(0)

    return aligned_df
