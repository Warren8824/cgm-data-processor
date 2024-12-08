import pandas as pd
import json
from typing import Dict


def clean_classify_insulin(df, bolus_limit=8, max_limit=15):
    '''
    Clean and separate basal and bolus insulin into separate columns based on insulin type if selected.
    "Novorapid" = Bolus & "Levemir" = Basal, if undefined then all insulin <= bolus_limit are classified as bolus,
    and > bolus_limit are classified as Basal. All unclassified treatments over max_limit are dropped.
    '''

    # Create a copy to avoid altering the original dataframe
    df_clean = df.copy()

    # Keep only rows where insulin is > 0.0 units
    df_clean = df_clean[df_clean['insulin'] > 0.0]

    # Drop rows where the index (timestamp) is duplicated
    df_clean = df_clean[~df_clean.index.duplicated(keep='first')]

    # Initialise bolus, basal, and unlabeled_insulin columns
    df_clean['bolus'] = 0.0
    df_clean['basal'] = 0.0
    df_clean['unlabeled_insulin'] = True  # Start with all as unlabeled

    # Process labeled data using insulinJSON column
    def extract_insulin_type(row):
        try:
            if pd.isna(row['insulinJSON']):
                return None
            data = json.loads(row['insulinJSON'])
            insulin_type = data.get('insulin', '').lower()
            if 'novorapid' in insulin_type:
                return 'bolus'
            elif 'levemir' in insulin_type:
                return 'basal'
        except:
            return None

    # Apply function to classify insulin type
    df_clean['insulin_type'] = df_clean.apply(extract_insulin_type, axis=1)

    # Update bolus, basal, and unlabeled_insulin based on insulin_type
    df_clean.loc[df_clean['insulin_type'] == 'bolus', 'bolus'] = df_clean['insulin']
    df_clean.loc[df_clean['insulin_type'] == 'basal', 'basal'] = df_clean['insulin']
    df_clean.loc[df_clean['insulin_type'].notna(), 'unlabeled_insulin'] = False

    # Process unlabeled data
    unlabeled_mask = (df_clean['bolus'] == 0) & (df_clean['basal'] == 0)

    # Drop all rows where insulin is unclassified AND > 15 units (Likely error)
    df_clean = df_clean.drop(
        df_clean[unlabeled_mask & (df_clean['insulin'] > 15)].index
    )

    # Classify remaining unlabeled data
    df_clean.loc[unlabeled_mask & (df_clean['insulin'] <= bolus_limit), 'bolus'] = df_clean['insulin']
    df_clean.loc[unlabeled_mask & (df_clean['insulin'] > bolus_limit) & (df_clean['insulin'] <= max_limit), 'basal'] = df_clean[
        'insulin']

    # Update unlabeled_insulin flag after all processing
    df_clean.loc[~unlabeled_mask, 'unlabeled_insulin'] = False

    # Drop the temporary insulin_type column if not needed
    df_clean = df_clean.drop(columns=['insulin_type'])

    return df_clean



def clean_classify_carbs(df):
    # Create a copy to avoid altering the original dataframe
    df_clean = df.copy()

    # Keep only rows where carbs is >= 1.0 grams
    df_clean = df_clean[df_clean['carbs'] >= 1.0]

    # Drop rows where the index (timestamp) is duplicated
    df = df[~df.index.duplicated(keep='first')]

    return df_clean


def clean_glucose(df):
    # Create copy to avoid altering original dataframe
    clean_df = df.copy()

    # Drop rows where the index (timestamp) is duplicated
    clean_df = clean_df[~clean_df.index.duplicated(keep='first')]

    # Rename the 'calculated_value' column to 'mg_dl'
    clean_df.rename(columns={'calculated_value': 'mg_dl'}, inplace=True)

    # Limit the 'mg_dl' column values to the range 39.64 to 360.36
    clean_df['mg_dl'] = clean_df['mg_dl'].clip(lower=39.64, upper=360.36)

    # Create a new column 'mmol_l' by converting 'calculated_value' from mg/dL to mmol/L
    clean_df['mmol_l'] = clean_df['mg_dl'] * 0.0555

    # Drop all rows except mg_dl and mmol_l
    clean_df = clean_df[['mg_dl', 'mmol_l']]

    return clean_df
