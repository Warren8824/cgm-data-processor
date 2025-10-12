"""initialise processors package and register all processors."""

from src.processors.base import DataProcessor
from src.processors.bgm import BGMProcessor
from src.processors.carbs import CarbsProcessor
from src.processors.cgm import CGMProcessor
from src.processors.insulin import InsulinProcessor
from src.processors.notes import NotesProcessor

__all__ = [
    "DataProcessor",
    "CGMProcessor",
    "BGMProcessor",
    "CarbsProcessor",
    "InsulinProcessor",
    "NotesProcessor",
]
