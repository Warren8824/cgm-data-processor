import pandas as pd
import matplotlib.pyplot as plt
import ast
from typing import Tuple


def analyse_insulin_over_time(df):
    # Create a copy of the dataframe with monthly periods
    df_monthly = df.copy()
    df_monthly['month'] = df_monthly.index.to_period('M')

    # Function to process insulin types from JSON
    def get_insulin_types(entry):
        if pd.isna(entry) or entry == "[]":
            return ["Not Stated"]
        insulin_data = ast.literal_eval(entry)
        return [record['insulin'] for record in insulin_data]

    # Create monthly statistics
    monthly_stats = []

    # Get unique months and sort them
    unique_months = sorted(df_monthly['month'].unique())

    for month in unique_months:
        month_data = df_monthly[df_monthly['month'] == month]

        # Count insulin types for this month
        insulin_counts = {'Novorapid': 0, 'Levemir': 0, 'Other': 0, 'Not Stated': 0}
        total_entries = len(month_data)

        for entry in month_data['insulinJSON']:
            insulin_types = get_insulin_types(entry)
            for insulin_type in insulin_types:
                if insulin_type == "Novorapid":
                    insulin_counts['Novorapid'] += 1
                elif insulin_type == "Levemir":
                    insulin_counts['Levemir'] += 1
                elif insulin_type == "Not Stated":
                    insulin_counts['Not Stated'] += 1
                else:
                    insulin_counts['Other'] += 1

        # Calculate percentages
        monthly_stats.append({
            'month': str(month),  # Convert period to string
            'Novorapid': (insulin_counts['Novorapid'] / total_entries) * 100,
            'Levemir': (insulin_counts['Levemir'] / total_entries) * 100,
            'Other': (insulin_counts['Other'] / total_entries) * 100,
            'Not Stated': (insulin_counts['Not Stated'] / total_entries) * 100,
            'total_entries': total_entries
        })

    # Convert to DataFrame
    stats_df = pd.DataFrame(monthly_stats)

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(25, 15))

    # Stacked area chart
    ax1.stackplot(range(len(stats_df)),
                  [stats_df['Novorapid'].values,
                   stats_df['Levemir'].values,
                   stats_df['Other'].values,
                   stats_df['Not Stated'].values],
                  labels=['Novorapid', 'Levemir', 'Other', 'Not Stated'],
                  colors=['#F26F21', '#35b57d', '#808080', '#D3D3D3'])  # Add specific colors

    # Set x-axis ticks and labels
    ax1.set_xticks(range(len(stats_df)))
    ax1.set_xticklabels(stats_df['month'], rotation=45)
    ax1.set_title('Distribution of Insulin Types Over Time')
    ax1.set_xlabel('Month')
    ax1.set_ylabel('Percentage')
    ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    # Line plot of total entries
    ax2.plot(range(len(stats_df)), stats_df['total_entries'].values, marker='o')
    ax2.set_xticks(range(len(stats_df)))
    ax2.set_xticklabels(stats_df['month'], rotation=45)
    ax2.set_title('Total Number of Entries per Month')
    ax2.set_xlabel('Month')
    ax2.set_ylabel('Number of Entries')

    # Adjust layout to prevent overlap
    plt.tight_layout()
    return plt, stats_df
