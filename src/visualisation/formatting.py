from typing import Dict
import pandas as pd
from IPython.display import display


def format_gaps_output(gaps_data):
    """
    Pretty-prints the gaps data in a Jupyter Notebook.

    Args:
        gaps_data (dict): Dictionary containing 'total_gaps', 'largest_gaps', and 'gaps_df'.

    Returns:
        None
    """

    # Extract data from the dictionary
    total_gaps = gaps_data.get('total_gaps', 0)
    largest_gaps = gaps_data.get('largest_gaps', None)
    gaps_df = gaps_data.get('gaps_df', None)

    # Print total gaps
    print("\033[1mTotal Number of Gaps:\033[0m", total_gaps)  # Bold title

    # Display largest gaps if available
    if largest_gaps is not None:
        print("\n\033[1mTop 10 Largest Gaps:\033[0m")
        display(largest_gaps.style.set_table_styles(
            [{'selector': 'th', 'props': [('font-weight', 'bold')]}]  # Bold column headers
        ).highlight_max(subset=['length_minutes'], color='orange'))  # Highlight largest gap

    # Display a preview of all gaps if available
    if gaps_df is not None:
        print("\n\033[1mAll Gaps (Summary - Top 10 Rows):\033[0m")
        display(gaps_df.head(10).style.set_table_styles(
            [{'selector': 'th', 'props': [('font-weight', 'bold')]}]
        ).highlight_max(subset=['length_minutes'], color='orange'))

    # Return the original dictionary for further use if needed
    return gaps_data
