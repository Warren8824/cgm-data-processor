import pandas as pd
from typing import Dict
from enum import Enum
from dataclasses import dataclass


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