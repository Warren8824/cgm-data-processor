import pandas as pd
from typing import Dict, Optional


def display_quality_metrics(df: pd.DataFrame) -> Dict:
    """
    Calculates and returns detailed quality metrics.

    Args:
        df: Processed DataFrame

    Returns:
        Dictionary containing detailed metrics
    """
    total_readings = len(df)
    complete_readings = df['mg_dl'].notna().sum()

    metrics = {
        'total_readings': total_readings,
        'complete_readings': complete_readings,
        'completeness_rate': (complete_readings / total_readings) * 100,
        'interpolated_points': df['interpolated'].sum(),
        'interpolation_rate': (df['interpolated'].sum() / total_readings) * 100,
        'average_gap_duration': df['gap_duration_mins'].mean(),
        'max_gap_duration': df['gap_duration_mins'].max(),
        'total_meals': len(df[df['meal_quality'].notna()]),
        'meal_quality_distribution': df['meal_quality'].value_counts().to_dict() if 'meal_quality' in df else None,
    }

    return metrics