import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Optional
import os


def create_quality_dashboard(
    df: pd.DataFrame,
    save_path: str = "img/data_quality_dashboard.png"
) -> None:
    """
    Creates a dashboard showing key data quality metrics and saves it as a PNG.

    Args:
        df: Processed DataFrame containing glucose, meal, and insulin data
            Must have columns: mg_dl, meal_quality, interpolated, gap_duration_mins
        save_path: File path to save the dashboard PNG image

    Returns:
        None
    """
    # Calculate metrics
    total_readings = len(df)
    complete_readings = df['mg_dl'].notna().sum()
    data_completeness = (complete_readings / total_readings) * 100

    meals = df[df['meal_quality'].notna()]
    usable_meals = len(meals[meals['meal_quality'].isin(['Clean', 'Usable'])])
    total_meals = len(meals)
    meal_usability = (usable_meals / total_meals) * 100 if total_meals > 0 else 0

    interpolation_rate = (df['interpolated'].sum() / total_readings) * 100
    avg_gap = df['gap_duration_mins'].mean()

    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{"type": "indicator"}, {"type": "indicator"}],
               [{"type": "indicator"}, {"type": "indicator"}]],
        subplot_titles=("Data Completeness", "Usable Meals",
                        "Interpolation Rate", "Average Gap Duration")
    )

    # Add gauges
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=data_completeness,
            title={'text': "Data Completeness - >90% Target"},
            number={'suffix': "%"},
            gauge={
                'axis': {'range': [0, 100]},
                'steps': [
                    {'range': [0, 70], 'color': "red"},
                    {'range': [70, 90], 'color': "orange"},
                    {'range': [90, 100], 'color': "lightgray"}
                ],
                'threshold': {
                    'line': {'color': "lightgreen", 'width': 5},
                    'thickness': 0.75,
                    'value': 90
                }
            },
            delta={'reference': 90}
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=meal_usability,
            title={'text': "Usable Meals"},
            number={'suffix': "%"},
            gauge={
                'axis': {'range': [0, 100]},
                'steps': [
                    {'range': [0, 60], 'color': "red"},
                    {'range': [60, 80], 'color': "orange"},
                    {'range': [80, 100], 'color': "lightgray"}
                ],
                'threshold': {
                    'line': {'color': "lightgreen", 'width': 5},
                    'thickness': 0.75,
                    'value': 80
                }
            },
            delta={'reference': 80}
        ),
        row=1, col=2
    )
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=interpolation_rate,
            title={'text': "Interpolation Rate"},
            number={'suffix': "%"},
            gauge={
                'axis': {'range': [0, 10]},
                'steps': [
                    {'range': [0, 2], 'color': "lightgray"},
                    {'range': [2, 5], 'color': "orange"},
                    {'range': [5, 10], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 5},
                    'thickness': 0.75,
                    'value': 2
                }
            },
            delta={'reference': 2, 'decreasing': {'color': "green"}}
        ),
        row=2, col=1
    )
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=avg_gap,
            title={'text': "Avg Gap Duration"},
            number={'suffix': " min"},
            gauge={
                'axis': {'range': [0, 15]},
                'steps': [
                    {'range': [0, 5], 'color': "lightgray"},
                    {'range': [5, 10], 'color': "orange"},
                    {'range': [10, 15], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 5
                }
            },
            delta={'reference': 10, 'decreasing': {'color': "green"}}
        ),
        row=2, col=2
    )

    # Update layout
    fig.update_layout(
        title={
            'text': "Data Quality Dashboard",
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24}
        },
        showlegend=False,
        height=800,
        width=1200,
        margin=dict(l=50, r=50)
    )

    # Save as PNG
    fig.write_image(save_path)

    print("Data Quality Dashboard saved")
