"""
Data Loading Functions
Handles single flat GL transaction detail CSV upload
"""

import pandas as pd
import duckdb
from io import StringIO
import streamlit as st

REQUIRED_COLUMNS = {'transaction_id', 'date', 'period', 'account_name', 'account_type', 'subsidiary', 'debit', 'credit'}


def load_flat_csv(file):
    """Read uploaded CSV and normalize column names."""
    if file is None:
        return None
    try:
        csv_string = file.getvalue().decode("utf-8")
        df = pd.read_csv(StringIO(csv_string))
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error reading {file.name}: {str(e)}")
        return None


def validate_columns(df):
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")


def load_all_data(file):
    """
    Load flat GL CSV into DuckDB and return connection + stats.

    Returns:
        tuple: (DuckDB connection, stats dict)
    """
    with st.spinner("📥 Loading CSV..."):
        df = load_flat_csv(file)

    if df is None:
        raise ValueError("Failed to read CSV file.")

    validate_columns(df)

    con = duckdb.connect(database=':memory:')
    con.register('v_gl', df)

    with st.spinner("🔄 Building in-memory tables..."):
        con.execute("""
            CREATE TABLE gl_transactions AS
            SELECT
                CAST(transaction_id AS VARCHAR)                         AS transaction_id,
                TRY_CAST(date AS DATE)                                  AS date,
                CAST(period AS VARCHAR)                                 AS period,
                CAST(account_name AS VARCHAR)                           AS account_name,
                CAST(account_type AS VARCHAR)                           AS account_type,
                CAST(subsidiary AS VARCHAR)                             AS subsidiary,
                COALESCE(CAST(department AS VARCHAR), '')               AS department,
                COALESCE(TRY_CAST(debit  AS DOUBLE), 0.0)              AS debit,
                COALESCE(TRY_CAST(credit AS DOUBLE), 0.0)              AS credit,
                COALESCE(TRY_CAST(debit  AS DOUBLE), 0.0)
                    - COALESCE(TRY_CAST(credit AS DOUBLE), 0.0)        AS amount
            FROM v_gl
            WHERE transaction_id IS NOT NULL
        """)

    row = con.execute("""
        SELECT
            COUNT(*)                        AS total_rows,
            COUNT(DISTINCT transaction_id)  AS transactions,
            COUNT(DISTINCT account_name)    AS accounts,
            COUNT(DISTINCT subsidiary)      AS subsidiaries,
            COUNT(DISTINCT period)          AS periods
        FROM gl_transactions
    """).fetchone()

    stats = {
        'total_rows':    row[0],
        'transactions':  row[1],
        'accounts':      row[2],
        'subsidiaries':  row[3],
        'periods':       row[4],
    }

    return con, stats
