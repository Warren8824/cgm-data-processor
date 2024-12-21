import pandas as pd
from typing import Dict
from sqlalchemy import create_engine, inspect
from pprint import pprint


class XDrip:
    """A class to handle XDrip database operations and data loading.

   This class provides functionality to interact with XDrip+ database,
   including reading glucose measurements and treatment data.

   Args:
       db_path (str): Path to the SQLite database file.

   Attributes:
       db_path (str): Path to the SQLite database file.
       engine: SQLAlchemy engine instance for database connection.
       inspector: SQLAlchemy inspector instance for database inspection.

   Examples:
       >>> xdrip = XDrip("path/to/xdrip.sqlite")
       >>> glucose_df = xdrip.load_glucose_df()
       >>> print(glucose_df.columns)
       Index(['calculated_value', 'raw_data', ...])

       >>> treatment_df = xdrip.load_treatment_df()
       >>> print(treatment_df.columns)
       Index(['insulin', 'carbs', 'timestamp', ...])
   """

    def __init__(self, db_path: str):
        """Initialize XDrip with database path and create engine.

       Args:
           db_path (str): Path to the SQLite database file.

       Examples:
           >>> xdrip = XDrip("path/to/xdrip.sqlite")
           >>> print(xdrip.db_path)
           'path/to/xdrip.sqlite'
       """
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.inspector = inspect(self.engine)

    def get_table_names(self):
        """Print all table names from the database.

        Prints a formatted list of all available tables in the XDrip database
        using pretty print.

        Examples:
            >>> xdrip.get_table_names()
              ['BgReadings',
               'Treatments',
               'Settings',
               'AndroidAPS']
        """
        pprint(self.inspector.get_table_names())

    def load_glucose_df(self) -> pd.DataFrame:
        """Load blood glucose readings from the database into a DataFrame.

        Reads the BgReadings table, converts timestamps from milliseconds to
        datetime, and handles duplicate timestamps.

        Returns:
            pd.DataFrame: DataFrame containing blood glucose readings with columns:
                - calculated_value: Blood glucose value
                - raw_data: Raw sensor data
                Additional columns may be present depending on XDrip version
                Index is timestamp in datetime format

        Examples:
            >>> glucose_df = xdrip.load_glucose_df()
            >>> print(glucose_df.head())
                                   calculated_value  raw_data
            2024-01-01 08:00:00              120.0    120000
            2024-01-01 08:05:00              125.0    125000
        """
        table = 'BgReadings'  # Table containing all BG Readings from XDrip+
        df = pd.read_sql_table(table, con=self.engine)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        # Drop rows where the index (timestamp) is duplicated
        df = df[~df.index.duplicated(keep='first')]

        return df

    def load_treatment_df(self) -> pd.DataFrame:
        """Load treatment data from the database into a DataFrame.

       Reads the Treatments table and converts timestamps from milliseconds
       to datetime.

       Returns:
           pd.DataFrame: DataFrame containing treatment data with columns:
               - insulin: Insulin doses in units
               - carbs: Carbohydrate amounts in grams
               - timestamp: Treatment time as datetime index
               Additional columns may be present depending on XDrip version

       Examples:
           >>> treatment_df = xdrip.load_treatment_df()
           >>> print(treatment_df.head())
                                   insulin  carbs
           2024-01-01 08:00:00       5.0   30.0
           2024-01-01 12:00:00       4.0   45.0
       """
        table = 'Treatments'  # Table containing all Treatments from XDrip+
        df = pd.read_sql_table(table, con=self.engine)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        return df
