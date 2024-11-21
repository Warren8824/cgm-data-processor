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


def format_meal_statistics(stats: Dict):
    """
    Pretty-prints meal statistics in a Jupyter Notebook.

    Args:
        stats: Dictionary returned by the get_meal_statistics function.

    Returns:
        None
    """
    # Create bold headers for clarity
    print("\033[1mMeal Analysis Statistics:\033[0m\n")

    # Total meals and averages
    print(f"\033[1mTotal Meals Analyzed:\033[0m {stats['total_meals']}")
    print(f"\033[1mAverage Missing Data Percentage:\033[0m {stats['avg_missing_pct']:.2f}%")
    print(f"\033[1mAverage Gap Duration:\033[0m {stats['avg_gap_duration']:.2f} minutes")
    print(f"\033[1mUsable Meals Percentage:\033[0m {stats['usable_meals_pct']:.2f}%")

    # Quality counts and percentages
    print("\n\033[1mMeal Quality Distribution:\033[0m")
    quality_df = pd.DataFrame({
        'Quality': stats['quality_counts'].keys(),
        'Count': stats['quality_counts'].values(),
        'Percentage (%)': stats['quality_percentages'].values()
    })
    quality_df = quality_df.sort_values('Count', ascending=False)

    # Apply color to the Count column by using a custom color function
    def color_count(val):
        if val < 5:
            color = 'lightpink'
        elif val < 10:
            color = 'lightblue'
        else:
            color = 'lightgreen'
        return f'background-color: {color}'

    # Apply the color function to the 'Count' column
    quality_df_styled = quality_df.style.map(color_count, subset=['Percentage (%)'])

    # Format Percentage column with 2 decimal places
    quality_df_styled = quality_df_styled.format({'Percentage (%)': '{:.2f}%'})

    # Display the styled DataFrame
    display(quality_df_styled.set_table_styles(
        [{'selector': 'th', 'props': [('font-weight', 'bold')]}]
    ))

    # Interpolation statistics
    print("\n\033[1mInterpolation Statistics:\033[0m")
    interpolation_df = pd.DataFrame({
        'Metric': ['Interpolated Points', 'Interpolated Percentage'],
        'Value': [stats['interpolated_points'], f"{stats['interpolated_pct']:.2f}%"]
    })
    display(interpolation_df.style.set_table_styles(
        [{'selector': 'th', 'props': [('font-weight', 'bold')]}]
    ).hide(axis="index"))

    print("\n\033[1mAll statistics displayed.\033[0m")