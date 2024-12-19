import pandas as pd
from typing import Dict
from sqlalchemy import create_engine, inspect
from pprint import pprint


class XDrip:
    """ A class to handle XDrip database operations and data loading.

        This class provides functionality to interact with XDrip+ database,
        including reading glucose measurements and treatment data.

        Attributes:
            db_path (str): Path to the SQLite database file.
            engine: SQLAlchemy engine instance for database connection.
            inspector: SQLAlchemy inspector instance for database inspection.

        Example:
            >>> xdrip = XDrip("xdrip_database.sqlite")
            >>> glucose_df = xdrip.load_glucose_df()
            >>> treatment_df = xdrip.load_treatment_df()
    """

    def __init__(self, db_path: str):
        """Initialize XDrip with database path and create engine.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.inspector = inspect(self.engine)

    def get_table_names(self):
        """Print all table names from the database.

        Prints a formatted list of all available tables in the XDrip database
        using pretty print.

        Example:
            >>> xdrip.get_table_names()
            ['Entries', 'Treatments', 'Settings']
        """
        pprint(self.inspector.get_table_names())

    def load_glucose_df(self):
        """Load blood glucose readings from the database into a DataFrame.

        Reads the BgReadings table, converts timestamps from milliseconds to
        datetime, and handles duplicate timestamps.

        Returns:
            pd.DataFrame: DataFrame containing blood glucose readings with
                timestamp index and no duplicates.

            Example:
                >>> glucose_df = xdrip.load_glucose_df()
                >>> print(glucose_df.head())
        """
        table = 'BgReadings'  # Table containing all BG Readings from XDrip+
        df = pd.read_sql_table(table, con=self.engine)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        # Drop rows where the index (timestamp) is duplicated
        df = df[~df.index.duplicated(keep='first')]

        return df

    def load_treatment_df(self):
        """Load treatment data from the database into a DataFrame.

        Reads the Treatments table and converts timestamps from milliseconds
        to datetime.

        Returns:
            pd.DataFrame: DataFrame containing treatment data with timestamp index.Example:
                >>> glucose_df = xdrip.load_treatment_df()
                >>> print(glucose_df.head())


        """
        table = 'Treatments'  # Table containing all Treatments from XDrip+
        df = pd.read_sql_table(table, con=self.engine)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        return df
