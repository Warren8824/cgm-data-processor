"""Abstract base for data processing"""

from abc import abstractmethod

import pandas as pd


class BaseDataProcessor:
    """Abstract base class for data processing"""

    @abstractmethod
    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        pass

    @abstractmethod
    def validate(self, data: pd.DataFrame) -> bool:
        pass
