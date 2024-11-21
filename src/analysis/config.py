class MealQuality(Enum):
    """Enum for meal analysis quality categories"""
    CLEAN = "Clean"          # No gaps
    USABLE = "Usable"        # Small gaps only, ≤10% missing
    BORDERLINE = "Borderline"  # Medium gaps, ≤20% missing
    UNUSABLE = "Unusable"    # Large gaps or >20% missing

@dataclass
class MealAnalysisConfig:
    """Configuration parameters for meal analysis and interpolation"""
    post_meal_hours: int = 4
    usable_gap_mins: int = 15
    max_gap_mins: int = 25
    usable_missing_pct: float = 0.10
    max_missing_pct: float = 0.20
    min_carbs: float = 20.0  # Minimum carbs to consider as meal
    interpolation_limit: int = 5  # Maximum points to interpolate (25 mins at 5-min intervals)


def get_meal_statistics(df: pd.DataFrame, config: MealAnalysisConfig = None) -> Dict:
    """
    Calculates statistics about meal quality and data completeness.

    Args:
        df: DataFrame with meal analysis columns
        config: MealAnalysisConfig object to ensure consistent carb threshold
               If None, uses default config

    Returns:
        Dictionary containing:
        - Total meals analyzed
        - Counts and percentages for each meal quality category
        - Average missing data percentage
        - Distribution of gap durations
        - Interpolation statistics
    """
    if config is None:
        config = MealAnalysisConfig()

    meals = df[df['carbs'] > config.min_carbs]

    stats = {
        'total_meals': len(meals),
        'quality_counts': meals['meal_quality'].value_counts().to_dict(),
        'quality_percentages': meals['meal_quality'].value_counts(normalize=True).multiply(100).to_dict(),
        'avg_missing_pct': meals['missing_pct'].mean(),
        'avg_gap_duration': meals['gap_duration_mins'].mean(),
        'usable_meals_pct': meals[~meals['skip_meal']].shape[0] / len(meals) * 100,
        'interpolated_points': df['interpolated'].sum(),
        'interpolated_pct': (df['interpolated'].sum() / len(df)) * 100
    }

    return stats
