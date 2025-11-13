"""
Data Loading and Normalization Functions
Handles CSV uploads and column name normalization
"""

import pandas as pd
import duckdb
from io import StringIO
import streamlit as st


def load_csv_to_dataframe(file):
    """
    Convert uploaded Streamlit file to Pandas DataFrame
    
    Args:
        file: Streamlit UploadedFile object
        
    Returns:
        pd.DataFrame: Loaded data
    """
    if file is None:
        return None
    
    try:
        csv_string = file.getvalue().decode("utf-8")
        return pd.read_csv(StringIO(csv_string))
    except Exception as e:
        st.error(f"Error loading {file.name}: {str(e)}")
        return None


def get_column(df, options):
    """
    Find first available column from a list of options
    
    Args:
        df: DataFrame to search
        options: List of possible column names
        
    Returns:
        str: First matching column name, or first option if none found
    """
    if df is None:
        return options[0]
    
    for col in options:
        if col in df.columns:
            return col
    return options[0]


def normalize_account_table(con, df_account):
    """
    Create normalized account table in DuckDB
    
    Args:
        con: DuckDB connection
        df_account: Raw account DataFrame
    """
    try:
        con.unregister('v_account')
    except:
        pass
    con.register('v_account', df_account)
    
    account_id_col = get_column(df_account, ['id', 'account_id'])
    account_name_col = get_column(df_account, ['fullname', 'name', 'account_name', 'accountsearchdisplayname'])
    account_type_col = get_column(df_account, ['accttype', 'accounttype', 'account_type'])
    
    con.execute(f"""
        CREATE OR REPLACE TABLE account AS
        SELECT 
          TRY_CAST("{account_id_col}" AS BIGINT) AS id,
          "{account_name_col}" AS fullname,
          "{account_type_col}" AS accttype
        FROM v_account
        WHERE "{account_id_col}" IS NOT NULL;
    """)


def normalize_subsidiary_table(con, df_subsidiary):
    """
    Create normalized subsidiary table in DuckDB
    
    Args:
        con: DuckDB connection
        df_subsidiary: Raw subsidiary DataFrame
    """
    try:
        con.unregister('v_subsidiary')
    except:
        pass
    con.register('v_subsidiary', df_subsidiary)
    
    sub_id_col = get_column(df_subsidiary, ['id', 'subsidiary_id'])
    sub_name_col = get_column(df_subsidiary, ['name', 'fullname', 'subsidiary_name'])
    
    con.execute(f"""
        CREATE OR REPLACE TABLE subsidiary AS
        SELECT 
          TRY_CAST("{sub_id_col}" AS BIGINT) AS id,
          "{sub_name_col}" AS name
        FROM v_subsidiary
        WHERE "{sub_id_col}" IS NOT NULL;
    """)


def normalize_transaction_table(con, df_transaction):
    """
    Create normalized transaction table in DuckDB
    
    Args:
        con: DuckDB connection
        df_transaction: Raw transaction DataFrame
    """
    try:
        con.unregister('v_transaction')
    except:
        pass
    con.register('v_transaction', df_transaction)
    
    trx_id_col = get_column(df_transaction, ['id', 'transaction_id'])
    trx_date_col = get_column(df_transaction, ['trandate', 'transaction_date', 'date'])
    trx_period_col = get_column(df_transaction, ['postingperiod', 'posting_period', 'period', 'accountingperiod'])
    trx_nonposting_col = get_column(df_transaction, ['nonposting', 'isnonposting', 'posting'])
    
    # Check if columns exist
    has_date = trx_date_col in df_transaction.columns
    has_period = trx_period_col in df_transaction.columns
    has_nonposting = trx_nonposting_col in df_transaction.columns
    
    date_select = f'TRY_CAST("{trx_date_col}" AS DATE)' if has_date else 'NULL'
    period_select = f'TRY_CAST("{trx_period_col}" AS BIGINT)' if has_period else 'NULL'
    
    # If no nonposting column, assume all are posting (FALSE)
    # If column exists, check if it's 'posting' field (inverted logic) or 'nonposting'
    if not has_nonposting:
        nonposting_select = 'FALSE'
    elif 'posting' in trx_nonposting_col.lower():
        # If column is named 'posting', TRUE means posting (so NOT nonposting)
        nonposting_select = f'NOT COALESCE(TRY_CAST("{trx_nonposting_col}" AS BOOLEAN), TRUE)'
    else:
        # Column is 'nonposting', treat NULL as FALSE (posting)
        nonposting_select = f'COALESCE(TRY_CAST("{trx_nonposting_col}" AS BOOLEAN), FALSE)'
    
    con.execute(f"""
        CREATE OR REPLACE TABLE transaction_header AS
        SELECT 
          TRY_CAST("{trx_id_col}" AS BIGINT) AS id,
          {date_select} AS trandate,
          {period_select} AS postingperiod,
          {nonposting_select} AS nonposting
        FROM v_transaction
        WHERE "{trx_id_col}" IS NOT NULL;
    """)


def normalize_transactionline_table(con, df_transactionline):
    """
    Create normalized transaction line table in DuckDB
    
    Args:
        con: DuckDB connection
        df_transactionline: Raw transaction line DataFrame
    """
    try:
        con.unregister('v_transactionline')
    except:
        pass
    con.register('v_transactionline', df_transactionline)
    
    trxline_trx_col = get_column(df_transactionline, ['transaction', 'transaction_id'])
    trxline_sub_col = get_column(df_transactionline, ['subsidiary', 'subsidiary_id'])
    trxline_dept_col = get_column(df_transactionline, ['department', 'department_id'])
    
    has_dept = trxline_dept_col in df_transactionline.columns
    dept_select = f'TRY_CAST("{trxline_dept_col}" AS BIGINT)' if has_dept else 'NULL'
    
    con.execute(f"""
        CREATE OR REPLACE TABLE transactionline AS
        SELECT 
          TRY_CAST("{trxline_trx_col}" AS BIGINT) AS transaction,
          TRY_CAST("{trxline_sub_col}" AS BIGINT) AS subsidiary,
          {dept_select} AS department
        FROM v_transactionline
        WHERE "{trxline_trx_col}" IS NOT NULL;
    """)


def normalize_transactionaccountingline_table(con, df_tal):
    """
    Create normalized transaction accounting line table in DuckDB
    
    Args:
        con: DuckDB connection
        df_tal: Raw transaction accounting line DataFrame
    """
    # Unregister if exists
    try:
        con.unregister('v_tal')
    except:
        pass
    
    con.register('v_tal', df_tal)
    
    tal_trx_col = get_column(df_tal, ['transaction', 'transaction_id'])
    tal_acct_col = get_column(df_tal, ['account', 'account_id'])
    
    # Verify columns exist
    if tal_trx_col not in df_tal.columns:
        raise ValueError(f"Transaction column not found in transactionaccountingline. Available columns: {', '.join(df_tal.columns)}")
    if tal_acct_col not in df_tal.columns:
        raise ValueError(f"Account column not found in transactionaccountingline. Available columns: {', '.join(df_tal.columns)}")
    if 'amount' not in df_tal.columns:
        raise ValueError(f"Amount column not found in transactionaccountingline. Available columns: {', '.join(df_tal.columns)}")
    
    con.execute(f"""
        CREATE OR REPLACE TABLE transactionaccountingline AS
        SELECT 
          TRY_CAST("{tal_trx_col}" AS BIGINT) AS transaction,
          TRY_CAST("{tal_acct_col}" AS BIGINT) AS account,
          CAST(amount AS DOUBLE) AS amount
        FROM v_tal
        WHERE "{tal_trx_col}" IS NOT NULL
          AND "{tal_acct_col}" IS NOT NULL
          AND amount IS NOT NULL;
    """)


def normalize_accountingperiod_table(con, df_period):
    """
    Create normalized accounting period table in DuckDB
    
    Args:
        con: DuckDB connection
        df_period: Raw accounting period DataFrame
    """
    if df_period is None:
        # Create dummy period table if not provided
        con.execute("""
            CREATE OR REPLACE TABLE accountingperiod AS
            SELECT 
                1 AS id,
                'No Period Data' AS periodname,
                1 AS fiscalyear,
                1 AS quarter,
                1 AS month,
                CAST('2024-01-01' AS DATE) AS startdate,
                CAST('2024-12-31' AS DATE) AS enddate;
        """)
        return
    
    con.register('v_period', df_period)
    
    period_id_col = get_column(df_period, ['id', 'period_id'])
    period_name_col = get_column(df_period, ['periodname', 'period_name', 'name'])
    period_year_col = get_column(df_period, ['fiscalyear', 'year'])
    period_quarter_col = get_column(df_period, ['quarter', 'fiscalquarter'])
    period_month_col = get_column(df_period, ['month', 'fiscalmonth'])
    period_start_col = get_column(df_period, ['startdate', 'start_date'])
    period_end_col = get_column(df_period, ['enddate', 'end_date'])
    
    has_year = period_year_col in df_period.columns
    has_quarter = period_quarter_col in df_period.columns
    has_month = period_month_col in df_period.columns
    has_start = period_start_col in df_period.columns
    has_end = period_end_col in df_period.columns
    
    year_select = f'TRY_CAST("{period_year_col}" AS INTEGER)' if has_year else 'NULL'
    quarter_select = f'TRY_CAST("{period_quarter_col}" AS INTEGER)' if has_quarter else 'NULL'
    month_select = f'TRY_CAST("{period_month_col}" AS INTEGER)' if has_month else 'NULL'
    start_select = f'TRY_CAST("{period_start_col}" AS DATE)' if has_start else 'NULL'
    end_select = f'TRY_CAST("{period_end_col}" AS DATE)' if has_end else 'NULL'
    
    con.execute(f"""
        CREATE OR REPLACE TABLE accountingperiod AS
        SELECT 
          TRY_CAST("{period_id_col}" AS BIGINT) AS id,
          "{period_name_col}" AS periodname,
          {year_select} AS fiscalyear,
          {quarter_select} AS quarter,
          {month_select} AS month,
          {start_select} AS startdate,
          {end_select} AS enddate
        FROM v_period
        WHERE "{period_id_col}" IS NOT NULL;
    """)


def load_all_data(files_dict):
    """
    Load and normalize all CSV files into DuckDB
    
    Args:
        files_dict: Dictionary of file names to UploadedFile objects
        
    Returns:
        tuple: (DuckDB connection, dict of DataFrames, dict of statistics)
    """
    con = duckdb.connect(database=':memory:')
    
    # Load DataFrames
    dfs = {}
    with st.spinner("📥 Loading CSV files..."):
        dfs['account'] = load_csv_to_dataframe(files_dict.get('account'))
        dfs['subsidiary'] = load_csv_to_dataframe(files_dict.get('subsidiary'))
        dfs['transaction'] = load_csv_to_dataframe(files_dict.get('transaction'))
        dfs['transactionline'] = load_csv_to_dataframe(files_dict.get('transactionline'))
        dfs['tal'] = load_csv_to_dataframe(files_dict.get('tal'))
        dfs['period'] = load_csv_to_dataframe(files_dict.get('period'))
    
    # Calculate statistics
    stats = {
        'accounts': len(dfs['account']) if dfs['account'] is not None else 0,
        'subsidiaries': len(dfs['subsidiary']) if dfs['subsidiary'] is not None else 0,
        'transactions': len(dfs['transaction']) if dfs['transaction'] is not None else 0,
        'lines': len(dfs['transactionline']) if dfs['transactionline'] is not None else 0,
        'accounting_lines': len(dfs['tal']) if dfs['tal'] is not None else 0,
        'periods': len(dfs['period']) if dfs['period'] is not None else 0,
    }
    
    total_rows = stats['transactions'] + stats['lines'] + stats['accounting_lines']
    stats['total_rows'] = total_rows
    
    # Normalize tables
    with st.spinner("🔄 Normalizing data..."):
        normalize_account_table(con, dfs['account'])
        normalize_subsidiary_table(con, dfs['subsidiary'])
        normalize_transaction_table(con, dfs['transaction'])
        normalize_transactionline_table(con, dfs['transactionline'])
        normalize_transactionaccountingline_table(con, dfs['tal'])
        normalize_accountingperiod_table(con, dfs['period'])
    
    return con, dfs, stats

