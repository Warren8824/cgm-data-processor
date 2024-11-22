import pandas as pd
from typing import Dict
from sqlalchemy import create_engine, inspect
from pprint import pprint


class XDrip:
    def __init__(self, db_path: str):
        """Initialize XDrip with database path and create engine."""
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.inspector = inspect(self.engine)

    def get_table_names(self):
        """Pprint all table names from the database."""

        pprint(self.inspector.get_table_names())

    def load_glucose_df(self):
        """Load BgReadings table into a dataframe and set timestamp index"""

        table = 'BgReadings'  # Table containing all BG Readings from XDrip+
        df = pd.read_sql_table(table, con=self.engine)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        return df

    def load_treatment_df(self):
        """Load Treatments table into a dataframe and set timestamp index"""

        table = 'Treatments'  # Table containing all Treatments from XDrip+
        df = pd.read_sql_table(table, con=self.engine)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        return df
