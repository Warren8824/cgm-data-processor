"""Abstract base class for all data source readers"""
from abc import abstractmethod

import pandas as pd


class BaseDataReader:
    """Define essential class methods"""

    @abstractmethod
    def load_glucose(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def load_treatments(self) -> pd.DataFrame:
        pass
