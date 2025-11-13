"""
Validation and Calculation Functions
Performs data quality checks and accounting equation validations
"""

import streamlit as st


def run_data_validations(con, filters):
    """
    Run all data validation checks
    
    Args:
        con: DuckDB connection
        filters: Active filters
        
    Returns:
        dict: Validation results
    """
    validations = {}
    
    # Check for null accounts
    validations['null_accounts'] = con.execute("""
        SELECT COUNT(*) as count
        FROM transactionaccountingline tal
        LEFT JOIN account a ON tal.account = a.id
        WHERE a.id IS NULL
    """).fetchone()[0]
    
    # Check for missing subsidiaries
    validations['missing_subsidiaries'] = con.execute("""
        SELECT COUNT(*) as count
        FROM transactionline tl
        LEFT JOIN subsidiary s ON tl.subsidiary = s.id
        WHERE s.id IS NULL
    """).fetchone()[0]
    
    # Check for non-posting transactions (informational)
    validations['nonposting_count'] = con.execute("""
        SELECT COUNT(DISTINCT th.id) as count
        FROM transaction_header th
        WHERE th.nonposting = TRUE
    """).fetchone()[0]
    
    # Total transaction count
    validations['total_transactions'] = con.execute("""
        SELECT COUNT(DISTINCT id) as count
        FROM transaction_header
    """).fetchone()[0]
    
    # Posting transactions count
    validations['posting_transactions'] = con.execute("""
        SELECT COUNT(DISTINCT id) as count
        FROM transaction_header
        WHERE nonposting = FALSE
    """).fetchone()[0]
    
    return validations


def calculate_balance_sheet_totals(bs_df):
    """
    Calculate balance sheet totals and check accounting equation
    
    Args:
        bs_df: Balance sheet DataFrame
        
    Returns:
        dict: Assets, liabilities, equity, and balance check
    """
    asset_types = ['Bank', 'AcctRec', 'OthCurrAsset', 'FixedAsset', 'OthAsset']
    liability_types = ['AcctPay', 'OthCurrLiab', 'LongTermLiab']
    equity_types = ['Equity']
    
    assets = bs_df[bs_df['account_type'].isin(asset_types)]['total_amount'].sum()
    liabilities = bs_df[bs_df['account_type'].isin(liability_types)]['total_amount'].sum()
    equity = bs_df[bs_df['account_type'].isin(equity_types)]['total_amount'].sum()
    
    balance_check = round(assets - (liabilities + equity), 2)
    
    return {
        'assets': assets,
        'liabilities': liabilities,
        'equity': equity,
        'balance_check': balance_check
    }


def calculate_pnl_totals(pnl_df):
    """
    Calculate P&L totals
    
    Args:
        pnl_df: P&L DataFrame
        
    Returns:
        dict: Revenue, expenses, and net income
    """
    revenue_types = ['Income', 'OthIncome']
    expense_types = ['Expense', 'COGS', 'OthExpense', 'DeferExpense']
    
    revenue = pnl_df[pnl_df['account_type'].isin(revenue_types)]['total_amount'].sum()
    expenses = pnl_df[pnl_df['account_type'].isin(expense_types)]['total_amount'].sum()
    
    # Revenue is typically negative (credit), expenses positive (debit)
    # Net income = Revenue + Expenses (since revenue is negative)
    net_income = revenue + expenses
    
    return {
        'revenue': abs(revenue),  # Show as positive
        'expenses': abs(expenses),  # Show as positive
        'net_income': net_income
    }


def display_validation_metrics(validations, exclude_nonposting=False):
    """
    Display validation metrics in Streamlit
    
    Args:
        validations: Dict of validation results
        exclude_nonposting: Whether non-posting filter is active
    """
    st.subheader("🔍 Data Quality Checks")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Null Accounts",
            validations['null_accounts'],
            delta_color="inverse"
        )
        if validations['null_accounts'] > 0:
            st.warning(f"⚠️ {validations['null_accounts']} accounting lines have missing account references")
    
    with col2:
        st.metric(
            "Missing Subsidiaries",
            validations['missing_subsidiaries'],
            delta_color="inverse"
        )
        if validations['missing_subsidiaries'] > 0:
            st.warning(f"⚠️ {validations['missing_subsidiaries']} lines have missing subsidiary references")
    
    with col3:
        st.metric(
            "Posting Transactions",
            f"{validations['posting_transactions']:,}"
        )
        if exclude_nonposting:
            st.info(f"ℹ️ Included in reports")
        else:
            st.info(f"ℹ️ All transactions shown")
    
    with col4:
        st.metric(
            "Non-Posting",
            f"{validations['nonposting_count']:,}"
        )
        if exclude_nonposting:
            st.info(f"ℹ️ Excluded from reports")
        else:
            st.info(f"ℹ️ Included in reports")


def display_balance_sheet_metrics(totals):
    """
    Display balance sheet metrics and accounting equation check
    
    Args:
        totals: Dict with assets, liabilities, equity, balance_check
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Assets", f"${totals['assets']:,.2f}")
    
    with col2:
        st.metric("Total Liabilities", f"${abs(totals['liabilities']):,.2f}")
    
    with col3:
        st.metric("Total Equity", f"${abs(totals['equity']):,.2f}")
    
    with col4:
        st.metric("Balance Check", f"${totals['balance_check']:,.2f}")
        if abs(totals['balance_check']) < 0.01:
            st.success("✅ Balanced!")
        elif abs(totals['balance_check']) < 100:
            st.warning("⚠️ Minor variance")
        else:
            st.error("❌ Out of balance")


def display_pnl_metrics(totals):
    """
    Display P&L summary metrics
    
    Args:
        totals: Dict with revenue, expenses, net_income
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Revenue", f"${totals['revenue']:,.2f}")
    
    with col2:
        st.metric("Total Expenses", f"${totals['expenses']:,.2f}")
    
    with col3:
        margin = (totals['net_income'] / totals['revenue'] * 100) if totals['revenue'] != 0 else 0
        st.metric(
            "Net Income",
            f"${totals['net_income']:,.2f}",
            delta=f"{margin:.1f}% margin"
        )

