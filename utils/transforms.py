"""
Data Transformation and Filtering Functions
Handles filtering by period, subsidiary, department, and account type
"""

import streamlit as st


def get_account_type_category(account_type):
    """
    Map NetSuite account types to financial statement categories
    
    Args:
        account_type: NetSuite account type code
        
    Returns:
        str: 'Asset', 'Liability', 'Equity', 'Revenue', or 'Expense'
    """
    asset_types = ['Bank', 'AcctRec', 'OthCurrAsset', 'FixedAsset', 'OthAsset']
    liability_types = ['AcctPay', 'OthCurrLiab', 'LongTermLiab']
    equity_types = ['Equity']
    revenue_types = ['Income', 'OthIncome']
    expense_types = ['Expense', 'COGS', 'OthExpense', 'DeferExpense']
    
    if account_type in asset_types:
        return 'Asset'
    elif account_type in liability_types:
        return 'Liability'
    elif account_type in equity_types:
        return 'Equity'
    elif account_type in revenue_types:
        return 'Revenue'
    elif account_type in expense_types:
        return 'Expense'
    else:
        return 'Other'


def build_filter_where_clause(filters):
    """
    Build SQL WHERE clause from filters
    
    Args:
        filters: Dict with keys: subsidiaries, periods, departments, account_types, exclude_nonposting
        
    Returns:
        str: SQL WHERE clause
    """
    conditions = []
    
    # Optional: Filter out non-posting transactions (only if user enables it)
    if filters.get('exclude_nonposting', False):
        conditions.append("COALESCE(th.nonposting, FALSE) = FALSE")
    
    # Subsidiary filter
    if filters.get('subsidiaries') and len(filters['subsidiaries']) > 0:
        sub_ids = ', '.join([str(s) for s in filters['subsidiaries']])
        conditions.append(f"tl.subsidiary IN ({sub_ids})")
    
    # Period filter
    if filters.get('periods') and len(filters['periods']) > 0:
        period_ids = ', '.join([f"'{p}'" for p in filters['periods']])
        conditions.append(f"ap.periodname IN ({period_ids})")
    
    # Department filter
    if filters.get('departments') and len(filters['departments']) > 0:
        dept_ids = ', '.join([str(d) for d in filters['departments']])
        conditions.append(f"tl.department IN ({dept_ids})")
    
    # Account type filter
    if filters.get('account_types') and len(filters['account_types']) > 0:
        acct_types = ', '.join([f"'{at}'" for at in filters['account_types']])
        conditions.append(f"a.accttype IN ({acct_types})")
    
    if conditions:
        return "WHERE " + " AND ".join(conditions)
    return ""


def get_base_query_with_filters(filters):
    """
    Generate base SQL query with all joins and filters applied
    
    Args:
        filters: Filter dictionary
        
    Returns:
        str: SQL query string
    """
    where_clause = build_filter_where_clause(filters)
    
    query = f"""
        SELECT
            COALESCE(s.name, 'Unknown Subsidiary') AS subsidiary_name,
            s.id AS subsidiary_id,
            COALESCE(a.fullname, 'Unknown Account [' || CAST(tal.account AS VARCHAR) || ']') AS account_name,
            a.id AS account_id,
            COALESCE(a.accttype, 'Unknown') AS account_type,
            ap.periodname AS period_name,
            ap.fiscalyear AS fiscal_year,
            ap.quarter AS fiscal_quarter,
            ap.month AS fiscal_month,
            th.trandate AS transaction_date,
            tl.department AS department_id,
            tal.amount AS amount
        FROM transactionaccountingline tal
        LEFT JOIN account a ON tal.account = a.id
        INNER JOIN transactionline tl ON tal.transaction = tl.transaction
        LEFT JOIN subsidiary s ON tl.subsidiary = s.id
        INNER JOIN transaction_header th ON tal.transaction = th.id
        LEFT JOIN accountingperiod ap ON th.postingperiod = ap.id
        {where_clause}
    """
    
    return query


@st.cache_data(ttl=300)
def get_available_filters(_con):
    """
    Get available values for all filters from the database
    
    Args:
        _con: DuckDB connection (prefixed with _ to avoid hashing)
        
    Returns:
        dict: Available filter values
    """
    filters = {}
    
    # Get subsidiaries
    try:
        subs_df = _con.execute("""
            SELECT DISTINCT id, name 
            FROM subsidiary 
            ORDER BY name
        """).fetchdf()
        filters['subsidiaries'] = [{'id': row['id'], 'name': row['name']} 
                                   for _, row in subs_df.iterrows()]
    except:
        filters['subsidiaries'] = []
    
    # Get periods
    try:
        periods_df = _con.execute("""
            SELECT DISTINCT periodname, fiscalyear, quarter, month
            FROM accountingperiod
            ORDER BY fiscalyear DESC, month DESC
        """).fetchdf()
        filters['periods'] = [{'name': row['periodname'], 
                              'year': row['fiscalyear'],
                              'quarter': row['quarter'],
                              'month': row['month']}
                             for _, row in periods_df.iterrows() if row['periodname']]
    except:
        filters['periods'] = []
    
    # Get departments
    try:
        depts_df = _con.execute("""
            SELECT DISTINCT department
            FROM transactionline
            WHERE department IS NOT NULL
            ORDER BY department
        """).fetchdf()
        filters['departments'] = [int(row['department']) 
                                 for _, row in depts_df.iterrows()]
    except:
        filters['departments'] = []
    
    # Get account types
    try:
        types_df = _con.execute("""
            SELECT DISTINCT accttype
            FROM account
            WHERE accttype IS NOT NULL
            ORDER BY accttype
        """).fetchdf()
        filters['account_types'] = [row['accttype'] 
                                   for _, row in types_df.iterrows()]
    except:
        filters['account_types'] = []
    
    return filters


def render_filter_sidebar(_con):
    """
    Render filter sidebar and return selected filters
    
    Args:
        _con: DuckDB connection
        
    Returns:
        dict: Selected filter values
    """
    st.sidebar.header("🔍 Filters")
    
    available = get_available_filters(_con)
    selected = {}
    
    # Non-posting filter (optional)
    st.sidebar.markdown("### Data Options")
    selected['exclude_nonposting'] = st.sidebar.checkbox(
        "Exclude Non-Posting Transactions",
        value=False,
        help="Check this to exclude non-posting/memo transactions from reports"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Filter By:")
    
    # Subsidiary filter
    if available['subsidiaries']:
        sub_options = {s['name']: s['id'] for s in available['subsidiaries']}
        selected_subs = st.sidebar.multiselect(
            "Subsidiaries",
            options=list(sub_options.keys()),
            default=None,
            help="Select one or more subsidiaries. Leave empty for all."
        )
        selected['subsidiaries'] = [sub_options[s] for s in selected_subs]
    else:
        selected['subsidiaries'] = []
    
    # Period filter
    if available['periods']:
        period_options = [p['name'] for p in available['periods']]
        selected['periods'] = st.sidebar.multiselect(
            "Periods",
            options=period_options,
            default=None,
            help="Select one or more periods. Leave empty for all."
        )
    else:
        selected['periods'] = []
    
    # Department filter
    if available['departments']:
        selected['departments'] = st.sidebar.multiselect(
            "Departments",
            options=available['departments'],
            default=None,
            help="Select one or more departments. Leave empty for all."
        )
    else:
        selected['departments'] = []
    
    # Account type filter
    if available['account_types']:
        selected['account_types'] = st.sidebar.multiselect(
            "Account Types",
            options=available['account_types'],
            default=None,
            help="Select one or more account types. Leave empty for all."
        )
    else:
        selected['account_types'] = []
    
    # Show filter summary
    active_filters = sum([
        1 if selected['subsidiaries'] else 0,
        1 if selected['periods'] else 0,
        1 if selected['departments'] else 0,
        1 if selected['account_types'] else 0,
        1 if selected['exclude_nonposting'] else 0
    ])
    
    if active_filters > 0:
        st.sidebar.success(f"✅ {active_filters} filter(s) active")
    else:
        st.sidebar.info("ℹ️ No filters applied (showing all data)")
    
    return selected

