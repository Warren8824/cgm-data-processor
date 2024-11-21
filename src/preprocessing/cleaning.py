import pandas as pd
import json
from typing import Dict


def clean_classify_insulin(df):
    '''
    Clean and separate basal and bolus insulin into separate columns based on insulin type if selected.
    "Novorapid" = Bolus & "Levemir" = Basal, if undefined then all insulin <= 8 units are classified as bolus,
    and <= 15 units are classified as Basal. All unclassified treatments over 15 units are dropped.
    '''

    # Create a copy to avoid altering the original dataframe
    df_clean = df.copy()

    # Keep only rows where insulin is > 0.0 units
    df_clean = df_clean[df_clean['insulin'] > 0.0]

    # Initialize bolus and basal columns with 0
    df_clean['bolus'] = 0.0
    df_clean['basal'] = 0.0

    # Process labeled data first using insulinJSON column
    def extract_insulin_type(row):
        try:
            if pd.isna(row['insulinJSON']):
                return None
            data = json.loads(row['insulinJSON'])
            insulin_type = data.get('insulin', '').lower()
            if 'novorapid' in insulin_type:
                df_clean.at[row.name, 'bolus'] = row['insulin']
            elif 'levemir' in insulin_type:
                df_clean.at[row.name, 'basal'] = row['insulin']
        except:
            return None

    # Apply extract_insulin_types to each row
    df_clean.apply(extract_insulin_type, axis=1)

    # Process unlabeled data
    unlabeled_mask = (df_clean['bolus'] == 0) & (df_clean['basal'] == 0)

    # Drop all rows where insulin is unclassified AND > 15 units (Likely error)
    df_clean = df_clean.drop(
        df_clean[unlabeled_mask & (df_clean['insulin'] > 15)].index
    )

    # Classify remaining unlabeled data
    df_clean.loc[unlabeled_mask & (df_clean['insulin'] <= 8), 'bolus'] = df_clean['insulin']
    df_clean.loc[unlabeled_mask & (df_clean['insulin'] > 8) & (df_clean['insulin'] <= 15), 'basal'] = df_clean[
        'insulin']

    # Drop the original insulin column if desired
    # df_clean = df_clean.drop('insulin', axis=1)

    return df_clean


def clean_classify_carbs(df):
    # Create a copy to avoid altering the original dataframe
    df_clean = df.copy()

    # Keep only rows where carbs is >= 1.0 grams
    df_clean = df_clean[df_clean['carbs'] >= 1.0]

    return df_clean


def clean_glucose(df):
    # Create copy to avoid altering original dataframe
    clean_df = df.copy()

    # Rename the 'calculated_value' column to 'mg_dl'
    clean_df.rename(columns={'calculated_value': 'mg_dl'}, inplace=True)

    # Limit the 'mg_dl' column values to the range 39.64 to 360.36
    clean_df['mg_dl'] = clean_df['mg_dl'].clip(lower=39.64, upper=360.36)

    # Create a new column 'mmol_l' by converting 'calculated_value' from mg/dL to mmol/L
    clean_df['mmol_l'] = clean_df['mg_dl'] * 0.0555

    # Drop all rows except mg_dl and mmol_l
    clean_df = clean_df[['mg_dl', 'mmol_l']]

    return clean_df
