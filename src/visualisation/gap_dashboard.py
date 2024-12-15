import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict


def create_gap_dashboard(gaps_data: Dict, save_path: str = "img/gaps_dashboard.png", display: bool = True,
                         width: int = 1000, height: int = 1300):
    """
    Creates a comprehensive dashboard showing gaps data, including initial missing data stats,
    total gaps, largest gaps, gap distribution, and descriptive statistics.

    Args:
        gaps_data: Dictionary containing gap analysis data including initial missing stats
        save_path: File path to save the dashboard PNG image, set to None to not save.
        display: If True, returns the figure object for display in notebook. True by default

    Returns:
        plotly.graph_objects.Figure if display=True, else None
    """

    # Extract the gaps data
    total_gaps = gaps_data.get('total_gaps', 0)
    largest_gaps = gaps_data.get('largest_gaps', None)
    gaps_df = gaps_data.get('gaps_df', None)

    # New statistics
    initial_missing_percentage = gaps_data.get('initial_missing_percentage', 100)
    initial_missing_count = gaps_data.get('initial_missing_count', 0)
    remaining_missing_percentage = gaps_data.get('gaps_percentage', 100)
    total_readings = gaps_data.get('total_readings', 0)
    total_gap_minutes = gaps_data.get('total_gap_minutes', 0)
    average_gap_minutes = gaps_data.get('average_gap_minutes', 0)
    median_gap_minutes = gaps_data.get('median_gap_minutes', 0)

    # Calculate additional descriptive statistics
    if gaps_df is not None:
        q1_gap = gaps_df['length_minutes'].quantile(0.25)
        q3_gap = gaps_df['length_minutes'].quantile(0.75)
        std_dev_gap = gaps_df['length_minutes'].std()
        min_gap = gaps_df['length_minutes'].min()
        max_gap = gaps_df['length_minutes'].max()
    else:
        q1_gap = q3_gap = std_dev_gap = min_gap = max_gap = None

    # Create subplots with new layout
    fig = make_subplots(
        rows=4, cols=2,
        specs=[
            [{"type": "indicator"}, {"type": "indicator"}],
            [{"type": "indicator"}, {"type": "indicator"}],
            [{"type": "bar"}, {"type": "scatter"}],
            [{"type": "table", "colspan": 2}, None],
        ],
        subplot_titles=(
            "", "",
            "", "",
            "Top 10 Largest Gaps", "All Gaps Distribution",
            "Comprehensive Statistics"
        )
    )

    # Indicator for total gaps before interpolation
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=initial_missing_count,
            title={'text': "Initial Gaps"},
            number={'suffix': " Gaps"},
            gauge={'axis': {'range': [None, initial_missing_count]}},
        ),
        row=1, col=1
    )

    # Indicator for initial missing percentage
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=initial_missing_percentage,
            title={'text': "Initial Missing Data"},
            number={'suffix': "%"},
            gauge={'axis': {'range': [0, 100]}},
        ),
        row=1, col=2
    )

    # Indicator for total gaps before interpolation
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=total_gaps,
            title={'text': "Remaining Gaps"},
            number={'suffix': " Gaps"},
            gauge={'axis': {'range': [None, (total_gaps*2.2)]}},
        ),
        row=2, col=1
    )

    # Indicator for initial missing percentage
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=remaining_missing_percentage,
            title={'text': "Remaining Missing Data"},
            number={'suffix': "%"},
            gauge={'axis': {'range': [0, 100]}},
        ),
        row=2, col=2
    )

    # Bar chart for largest gaps
    if largest_gaps is not None:
        fig.add_trace(
            go.Bar(
                x=largest_gaps['start_time'],
                y=largest_gaps['length_minutes'],
                name="Largest Gaps",
                marker_color='orange',
                hovertemplate="Start: %{x}<br>Duration: %{y} minutes<extra></extra>"
            ),
            row=3, col=1
        )

    # Scatter plot for all gaps
    if gaps_df is not None:
        fig.add_trace(
            go.Scatter(
                x=gaps_df['start_time'],
                y=gaps_df['length_minutes'],
                mode='markers',
                marker=dict(color='blue', opacity=0.6),
                name="All Gaps",
                hovertemplate="Time: %{x}<br>Duration: %{y} minutes<extra></extra>"
            ),
            row=3, col=2
        )

    # Comprehensive statistics table
    fig.add_trace(
        go.Table(
            header=dict(
                values=["Metric", "Value"],
                fill_color='paleturquoise',
                align='left',
                font=dict(size=12)
            ),
            cells=dict(
                values=[
                    [
                        "Total Readings",
                        "Initial Missing Count",
                        "Initial Missing Percentage",
                        "Remaining Missing Count",
                        "Remaining Missing Percentage"
                        "Total Gap Duration",
                        "Average Gap Duration",
                        "Median Gap Duration",
                        "25th Percentile Gap",
                        "75th Percentile Gap",
                        "Standard Deviation",
                        "Minimum Gap",
                        "Maximum Gap"
                    ],
                    [
                        f"{total_readings:,}",
                        f"{initial_missing_count:,}",
                        f"{initial_missing_percentage:.3f}%",
                        f"{total_gaps:,}",
                        f"{remaining_missing_percentage:.3f}%",
                        f"{total_gap_minutes:.1f} minutes",
                        f"{average_gap_minutes:.1f} minutes",
                        f"{median_gap_minutes:.1f} minutes",
                        f"{q1_gap:.1f} minutes",
                        f"{q3_gap:.1f} minutes",
                        f"{std_dev_gap:.1f} minutes",
                        f"{min_gap:.1f} minutes",
                        f"{max_gap:.1f} minutes"
                    ]
                ],
                align='left',
                font=dict(size=11)
            )
        ),
        row=4, col=1
    )

    # Update layout with new dimensions and better use of space
    fig.update_layout(
        title={
            'text': "Glucose Reading Gaps Analysis Dashboard",
            'y': 0.98,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        showlegend=False,
        height=height,
        width=width,
        margin=dict(l=20, r=20, t=60, b=20),
        autosize=True,
        font=dict(size=10),
        title_font_size=14,
    )

    # Update font sizes for all subplot titles
    for annotation in fig['layout']['annotations']:
        annotation['font'] = dict(size=12)

    # Update table font sizes
    for trace in fig.data:
        if isinstance(trace, go.Table):
            trace.header.font.size = 10
            trace.cells.font.size = 9

    # Update axis labels with smaller font
    fig.update_xaxes(title_font=dict(size=10))
    fig.update_yaxes(title_font=dict(size=10))

    # Save as PNG if path is provided
    if save_path:
        fig.write_image(save_path)
        print(f"Enhanced Gaps Dashboard saved to {save_path}")

    # Return figure for display if requested
    if display:
        return fig
