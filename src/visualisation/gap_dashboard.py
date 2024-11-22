import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict

def create_gap_dashboard(gaps_data: Dict, save_path: str = "img/gaps_dashboard.png"):
    """
    Creates a dashboard showing gaps data, including total gaps, top 10 largest gaps,
    a scatter plot of all gaps, and adds descriptive statistics, then saves it as a PNG.

    Args:
        gaps_data: Dictionary containing 'total_gaps', 'largest_gaps', and 'gaps_df'.
        save_path: File path to save the dashboard PNG image.

    Returns:
        None
    """

    # Extract the gaps data
    total_gaps = gaps_data.get('total_gaps', 0)
    largest_gaps = gaps_data.get('largest_gaps', None)
    gaps_df = gaps_data.get('gaps_df', None)

    # Calculate descriptive statistics
    if gaps_df is not None:
        mean_gap = gaps_df['length_minutes'].mean()
        q1_gap = gaps_df['length_minutes'].quantile(0.25)  # 25th percentile
        q3_gap = gaps_df['length_minutes'].quantile(0.75)  # 75th percentile
        median_gap = gaps_df['length_minutes'].median()
        std_dev_gap = gaps_df['length_minutes'].std()
        min_gap = gaps_df['length_minutes'].min()
        max_gap = gaps_df['length_minutes'].max()
    else:
        mean_gap = q1_gap = median_gap = q3_gap = std_dev_gap = min_gap = max_gap = None

    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{"type": "indicator"}, {"type": "bar"}],
               [{"type": "scatter"}, {"type": "table"}]],
        subplot_titles=("Total Gaps", "Top 10 Largest Gaps", "All Gaps Distribution", "Gap Statistics")
    )

    # Indicator for total gaps
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=total_gaps,
            title={'text': "Total Gaps"},
            number={'suffix': " Gaps"},
            gauge={'axis': {'range': [None, total_gaps]}},
        ),
        row=1, col=1
    )

    # Bar chart for largest gaps
    if largest_gaps is not None:
        fig.add_trace(
            go.Bar(
                x=largest_gaps['start_time'],  # assuming 'start_time' is in the data
                y=largest_gaps['length_minutes'],  # assuming 'length_minutes' is in the data
                name="Largest Gaps",
                marker_color='orange'
            ),
            row=1, col=2
        )

    # Scatter plot for all gaps
    if gaps_df is not None:
        fig.add_trace(
            go.Scatter(
                x=gaps_df['start_time'],  # assuming 'start_time' is in the data
                y=gaps_df['length_minutes'],  # assuming 'length_minutes' is in the data
                mode='markers',
                marker=dict(color='blue', opacity=0.6),
                name="All Gaps"
            ),
            row=2, col=1
        )

    # Descriptive statistics table
    if gaps_df is not None:
        fig.add_trace(
            go.Table(
                header=dict(values=["Statistic", "Value"],
                            fill_color='paleturquoise',
                            align='left'),
                cells=dict(values=[
                    ["Mean Gap (minutes)", "Median Gap (minutes)", "Standard Deviation", "Min Gap (minutes)", "Max Gap (minutes)"],
                    [mean_gap, q1_gap, median_gap, q3_gap, std_dev_gap, min_gap, max_gap]
                ])
            ),
            row=2, col=2
        )

    # Update layout
    fig.update_layout(
        title="Gaps Data Dashboard",
        showlegend=False,
        height=1000,
        width=1500,
        margin=dict(l=50, r=50)
    )

    # Save as PNG
    fig.write_image(save_path)

    print(f"Gaps Dashboard saved.")