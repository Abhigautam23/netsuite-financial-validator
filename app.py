"""
NetSuite Financial Reporting MVP
A complete Streamlit app for analyzing NetSuite export CSVs
Produces Trial Balance, P&L, and Balance Sheet with filtering and export capabilities
"""

import streamlit as st
import sys
from utils.load_data import load_all_data
from utils.transforms import render_filter_sidebar
from utils.calculations import run_data_validations, display_validation_metrics
from utils.trial_balance import generate_trial_balance, display_trial_balance
from utils.p_and_l import generate_pnl, display_pnl, display_periodised_pnl
from utils.balance_sheet import generate_balance_sheet, display_balance_sheet
from utils.export import export_to_pdf

# Page configuration
st.set_page_config(
    page_title="NetSuite Financial Reporting MVP",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.markdown('<h1 class="main-header">📊 NetSuite Financial Reporting MVP</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Professional financial reporting from NetSuite CSV exports</p>', unsafe_allow_html=True)

# Instructions expander
with st.expander("📖 How to use this app", expanded=False):
    st.markdown("""
    ### Required CSV Files
    
    Upload these 5 NetSuite export files:
    
    1. **account.csv**: Chart of accounts (`id`, `fullname`, `accttype`)
    2. **subsidiary.csv**: List of subsidiaries (`id`, `name`)
    3. **transaction.csv**: Transaction headers (`id`, `trandate`, `postingperiod`, `nonposting`)
    4. **transactionline.csv**: Transaction lines (`transaction`, `subsidiary`, `department`)
    5. **transactionaccountingline.csv**: Accounting entries (`transaction`, `account`, `amount`)
    
    **Optional:**
    - **accountingperiod.csv**: Period information (`id`, `periodname`, `fiscalyear`, `quarter`, `month`)
    
    ### Features
    
    - ✅ **Trial Balance**: Complete account balances by subsidiary
    - ✅ **Profit & Loss**: Revenue vs expenses with periodisation (monthly/quarterly/yearly)
    - ✅ **Balance Sheet**: Assets, liabilities, and equity
    - ✅ **Filters**: Filter by subsidiary, period, department, and account type
    - ✅ **Exports**: Download CSV or PDF for all reports
    - ✅ **Validations**: Automatic data quality checks
    
    ### Important Notes
    
    - **All transactions** are shown by default (both posting and non-posting)
    - Use the **"Exclude Non-Posting Transactions"** filter in the sidebar to filter them out
    - All processing happens client-side (no data stored)
    - Large datasets (>100K rows) may take 30-60 seconds to process
    """)

# File upload section
st.subheader("📁 Upload CSV Files")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Required Files**")
    f_account = st.file_uploader(
        "1. account.csv",
        type=["csv"],
        key="account",
        help="Chart of accounts"
    )
    f_subsidiary = st.file_uploader(
        "2. subsidiary.csv",
        type=["csv"],
        key="subsidiary",
        help="Subsidiaries"
    )

with col2:
    st.markdown("**Transaction Files**")
    f_transaction = st.file_uploader(
        "3. transaction.csv",
        type=["csv"],
        key="transaction",
        help="Transaction headers"
    )
    f_transactionline = st.file_uploader(
        "4. transactionline.csv",
        type=["csv"],
        key="transactionline",
        help="Transaction lines"
    )

with col3:
    st.markdown("**Accounting Data**")
    f_tal = st.file_uploader(
        "5. transactionaccountingline.csv",
        type=["csv"],
        key="tal",
        help="Accounting entries"
    )
    f_period = st.file_uploader(
        "6. accountingperiod.csv (optional)",
        type=["csv"],
        key="period",
        help="Period information for periodised reporting"
    )

# Run button
run_button = st.button("🚀 Generate Reports", type="primary", use_container_width=True)

if run_button:
    # Validate required files
    required_files = {
        "account.csv": f_account,
        "subsidiary.csv": f_subsidiary,
        "transaction.csv": f_transaction,
        "transactionline.csv": f_transactionline,
        "transactionaccountingline.csv": f_tal
    }
    
    missing = [name for name, file in required_files.items() if file is None]
    
    if missing:
        st.error(f"❌ Missing required files: {', '.join(missing)}")
        st.stop()
    
    try:
        # Load all data
        files_dict = {
            'account': f_account,
            'subsidiary': f_subsidiary,
            'transaction': f_transaction,
            'transactionline': f_transactionline,
            'tal': f_tal,
            'period': f_period
        }
        
        con, dfs, stats = load_all_data(files_dict)
        
        # Show data statistics
        st.success("✅ Data loaded successfully!")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Accounts", f"{stats['accounts']:,}")
        col2.metric("Subsidiaries", f"{stats['subsidiaries']:,}")
        col3.metric("Transactions", f"{stats['transactions']:,}")
        col4.metric("Lines", f"{stats['lines']:,}")
        col5.metric("Accounting Lines", f"{stats['accounting_lines']:,}")
        
        # Warn for large datasets
        if stats['total_rows'] > 500000:
            st.warning("⚠️ Large dataset detected. Processing may take 1-2 minutes.")
        elif stats['total_rows'] > 100000:
            st.info("ℹ️ Medium dataset. Processing may take 30-60 seconds.")
        
        # Store connection in session state
        st.session_state['con'] = con
        st.session_state['data_loaded'] = True
        
        st.markdown("---")
        st.info("👈 Use the sidebar to apply filters, then select a report tab below")
        
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.exception(e)
        st.stop()

# Main reporting section (only show if data is loaded)
if st.session_state.get('data_loaded', False):
    con = st.session_state['con']
    
    # Render filters in sidebar
    filters = render_filter_sidebar(con)
    
    # Run validations
    with st.spinner("Running data validations..."):
        validations = run_data_validations(con, filters)
    
    display_validation_metrics(validations, filters.get('exclude_nonposting', False))
    
    st.markdown("---")
    
    # Report tabs
    st.subheader("📊 Financial Reports")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Trial Balance",
        "💰 Profit & Loss",
        "📅 Periodised P&L",
        "🏦 Balance Sheet"
    ])
    
    with tab1:
        with st.spinner("Generating Trial Balance..."):
            tb_df = generate_trial_balance(con, filters)
            display_trial_balance(tb_df)
            
            # PDF export
            if not tb_df.empty and len(tb_df) <= 1000:
                pdf_data = export_to_pdf(
                    {
                        'dataframe': tb_df,
                        'metrics': {
                            'Total Accounts': f"{len(tb_df):,}",
                            'Total Debits': f"${tb_df[tb_df['total_amount'] > 0]['total_amount'].sum():,.2f}",
                            'Total Credits': f"${abs(tb_df[tb_df['total_amount'] < 0]['total_amount'].sum()):,.2f}"
                        }
                    },
                    "Trial Balance",
                    filters
                )
                st.download_button(
                    label="📄 Download Trial Balance PDF",
                    data=pdf_data,
                    file_name="trial_balance.pdf",
                    mime="application/pdf"
                )
    
    with tab2:
        with st.spinner("Generating Profit & Loss..."):
            pnl_df = generate_pnl(con, filters)
            display_pnl(pnl_df)
            
            # PDF export
            if not pnl_df.empty and len(pnl_df) <= 1000:
                from utils.calculations import calculate_pnl_totals
                totals = calculate_pnl_totals(pnl_df)
                pdf_data = export_to_pdf(
                    {
                        'dataframe': pnl_df,
                        'metrics': {
                            'Total Revenue': f"${totals['revenue']:,.2f}",
                            'Total Expenses': f"${totals['expenses']:,.2f}",
                            'Net Income': f"${totals['net_income']:,.2f}"
                        }
                    },
                    "Profit & Loss",
                    filters
                )
                st.download_button(
                    label="📄 Download P&L PDF",
                    data=pdf_data,
                    file_name="profit_and_loss.pdf",
                    mime="application/pdf"
                )
    
    with tab3:
        with st.spinner("Generating Periodised P&L..."):
            display_periodised_pnl(con, filters)
    
    with tab4:
        with st.spinner("Generating Balance Sheet..."):
            bs_df = generate_balance_sheet(con, filters)
            display_balance_sheet(bs_df)
            
            # PDF export
            if not bs_df.empty and len(bs_df) <= 1000:
                from utils.calculations import calculate_balance_sheet_totals
                totals = calculate_balance_sheet_totals(bs_df)
                pdf_data = export_to_pdf(
                    {
                        'dataframe': bs_df,
                        'metrics': {
                            'Total Assets': f"${totals['assets']:,.2f}",
                            'Total Liabilities': f"${abs(totals['liabilities']):,.2f}",
                            'Total Equity': f"${abs(totals['equity']):,.2f}",
                            'Balance Check': f"${totals['balance_check']:,.2f}"
                        }
                    },
                    "Balance Sheet",
                    filters
                )
                st.download_button(
                    label="📄 Download Balance Sheet PDF",
                    data=pdf_data,
                    file_name="balance_sheet.pdf",
                    mime="application/pdf"
                )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><b>NetSuite Financial Reporting MVP</b> | Built with Streamlit & DuckDB</p>
    <p>All data processing happens locally - no data is stored or transmitted</p>
</div>
""", unsafe_allow_html=True)
