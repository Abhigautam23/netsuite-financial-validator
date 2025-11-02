import os
import pandas as pd
import sqlalchemy


def load_csv(filename: str, base_path: str = "../data/") -> pd.DataFrame:
    """
    Loads a CSV file from the data folder.
    """
    file_path = os.path.join(base_path, filename)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found.")
    return pd.read_csv(file_path)


def load_sql(query: str, connection_string: str) -> pd.DataFrame:
    """
    Executes a SQL query and returns a DataFrame.
    Example:
        df = load_sql(
            "SELECT * FROM transactions LIMIT 10",
            "postgresql+psycopg2://user:password@localhost:5432/finance_db"
        )
    """
    try:
        engine = sqlalchemy.create_engine(connection_string)
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        raise RuntimeError(f"Error executing SQL query: {e}")
