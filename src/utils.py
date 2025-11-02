# src/utils.py

CONFIG = {
    # Select which data source to use
    "data_source": "csv",  # Options: "csv" or "sql"

    # Base path for CSV files
    "csv_base_path": "data/",

    # SQL connection string (used only if data_source == "sql")
    "sql_connection_string": "postgresql+psycopg2://user:password@localhost:5432/finance_db",

    # Output directory
    "output_path": "output/"
}

def ensure_output_path(path: str):
    """Create output folder if it doesn't exist."""
    import os
    os.makedirs(path, exist_ok=True)
