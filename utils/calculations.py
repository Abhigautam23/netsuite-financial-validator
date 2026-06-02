"""
Validation and Calculation Functions
Performs data quality checks and accounting equation validations
"""

import streamlit as st


def run_data_validations(con, filters):
    """Run data quality checks on the loaded GL transactions."""
    v = {}

    v['null_accounts'] = con.execute(
        "SELECT COUNT(*) FROM gl_transactions WHERE account_name IS NULL OR account_name = ''"
    ).fetchone()[0]

    v['missing_subsidiaries'] = con.execute(
        "SELECT COUNT(*) FROM gl_transactions WHERE subsidiary IS NULL OR subsidiary = ''"
    ).fetchone()[0]

    v['total_transactions'] = con.execute(
        "SELECT COUNT(DISTINCT transaction_id) FROM gl_transactions"
    ).fetchone()[0]

    row = con.execute(
        "SELECT ROUND(SUM(debit), 2), ROUND(SUM(credit), 2) FROM gl_transactions"
    ).fetchone()
    v['total_debits'] = row[0] or 0.0
    v['total_credits'] = row[1] or 0.0

    return v


def calculate_balance_sheet_totals(bs_df):
    asset_types = ['Bank', 'AcctRec', 'OthCurrAsset', 'FixedAsset', 'OthAsset']
    liability_types = ['AcctPay', 'OthCurrLiab', 'LongTermLiab']
    equity_types = ['Equity']

    assets = bs_df[bs_df['account_type'].isin(asset_types)]['total_amount'].sum()
    liabilities = bs_df[bs_df['account_type'].isin(liability_types)]['total_amount'].sum()
    equity = bs_df[bs_df['account_type'].isin(equity_types)]['total_amount'].sum()
    balance_check = round(assets - (liabilities + equity), 2)

    return {'assets': assets, 'liabilities': liabilities, 'equity': equity, 'balance_check': balance_check}


def calculate_pnl_totals(pnl_df):
    revenue_types = ['Income', 'OthIncome']
    expense_types = ['Expense', 'COGS', 'OthExpense', 'DeferExpense']

    revenue = pnl_df[pnl_df['account_type'].isin(revenue_types)]['total_amount'].sum()
    expenses = pnl_df[pnl_df['account_type'].isin(expense_types)]['total_amount'].sum()
    net_income = revenue + expenses

    return {
        'revenue': abs(revenue),
        'expenses': abs(expenses),
        'net_income': net_income,
    }


def display_validation_metrics(validations):
    """Display data quality summary metrics."""
    st.subheader("🔍 Data Quality Checks")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Transactions", f"{validations['total_transactions']:,}")

    with col2:
        st.metric("Null Accounts", validations['null_accounts'], delta_color="inverse")
        if validations['null_accounts'] > 0:
            st.warning(f"⚠️ {validations['null_accounts']} rows missing account name")

    with col3:
        st.metric("Missing Subsidiaries", validations['missing_subsidiaries'], delta_color="inverse")
        if validations['missing_subsidiaries'] > 0:
            st.warning(f"⚠️ {validations['missing_subsidiaries']} rows missing subsidiary")

    with col4:
        variance = round(validations['total_debits'] - validations['total_credits'], 2)
        st.metric("Debit/Credit Variance", f"${variance:,.2f}")
        if abs(variance) < 0.01:
            st.success("✅ Balanced")
        elif abs(variance) < 100:
            st.warning("⚠️ Minor variance")
        else:
            st.error("❌ Out of balance")


def display_balance_sheet_metrics(totals):
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
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Revenue", f"${totals['revenue']:,.2f}")
    with col2:
        st.metric("Total Expenses", f"${totals['expenses']:,.2f}")
    with col3:
        margin = (totals['net_income'] / totals['revenue'] * 100) if totals['revenue'] != 0 else 0
        st.metric("Net Income", f"${totals['net_income']:,.2f}", delta=f"{margin:.1f}% margin")
