import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict
import os


def create_meal_statistics_dashboard(
        stats: Dict,
        save_path: str = "img/meal_statistics_dashboard.png"
) -> None:
    """
    Creates a dashboard to visualize meal statistics and saves it as a PNG.

    Args:
        stats: Dictionary with meal statistics (e.g., total meals, usable meals, etc.)
        save_path: File path to save the dashboard PNG image.

    Returns:
        None
    """
    # Extract key metrics
    total_meals = stats['total_meals']
    avg_missing_pct = stats['avg_missing_pct']
    avg_gap_duration = stats['avg_gap_duration']
    usable_meals_pct = stats['usable_meals_pct']

    # Create subplot layout
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{"type": "indicator"}, {"type": "indicator"}],
               [{"type": "indicator"}, {"type": "table"}]],
        subplot_titles=("Total Meals Analyzed", "Usable Meals %",
                        "Average Gap Duration (min)", "Meal Quality Distribution")
    )

    # Add gauges for key metrics
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=total_meals,
            title={'text': "Total Meals"},
            gauge={
                'axis': {'range': [0, max(50, total_meals)]},
                'steps': [
                    {'range': [0, total_meals * 0.3], 'color': "red"},
                    {'range': [total_meals * 0.3, total_meals * 0.7], 'color': "orange"},
                    {'range': [total_meals * 0.7, total_meals], 'color': "lightgray"}
                ]
            }
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=usable_meals_pct,
            title={'text': "Usable Meals (%)"},
            number={'suffix': "%"},
            gauge={
                'axis': {'range': [0, 100]},
                'steps': [
                    {'range': [0, 50], 'color': "red"},
                    {'range': [50, 80], 'color': "orange"},
                    {'range': [80, 100], 'color': "lightgray"}
                ]
            }
        ),
        row=1, col=2
    )
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=avg_gap_duration,
            title={'text': "Avg Gap Duration (min)"},
            gauge={
                'axis': {'range': [0, 30]},
                'steps': [
                    {'range': [0, 10], 'color': "lightgray"},
                    {'range': [10, 20], 'color': "orange"},
                    {'range': [20, 30], 'color': "red"}
                ]
            }
        ),
        row=2, col=1
    )

    # Add table for meal quality distribution
    quality_df = pd.DataFrame({
        'Quality': list(stats['quality_counts'].keys()),
        'Count': list(stats['quality_counts'].values()),
        'Percentage (%)': [f"{v:.2f}%" for v in stats['quality_percentages'].values()]
    })
    fig.add_trace(
        go.Table(
            header=dict(values=["Quality", "Count", "Percentage (%)"],
                        fill_color="paleturquoise",
                        align="left"),
            cells=dict(values=[quality_df[col] for col in quality_df.columns],
                       fill_color="lavender",
                       align="left")
        ),
        row=2, col=2
    )

    # Update layout
    fig.update_layout(
        title={
            'text': "Meal Statistics Dashboard",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24}
        },
        height=800,
        width=1200,
        margin=dict(l=50, r=50)
    )

    # Save as PNG
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig.write_image(save_path)
    print("Meal Statistics Dashboard saved.")
