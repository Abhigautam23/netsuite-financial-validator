"""
NetSuite Financial Reporting MVP
Streamlit app for analysing a flat NetSuite GL transaction detail export.
"""

import streamlit as st
from utils.load_data import load_all_data
from utils.transforms import render_filter_sidebar
from utils.calculations import run_data_validations, display_validation_metrics
from utils.trial_balance import generate_trial_balance, display_trial_balance
from utils.p_and_l import generate_pnl, display_pnl, display_periodised_pnl
from utils.balance_sheet import generate_balance_sheet, display_balance_sheet
from utils.close_health import display_close_health
from utils.export import export_to_pdf

st.set_page_config(
    page_title="NetSuite Close Validator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main-header { font-size:3rem; font-weight:bold; color:#1f77b4; text-align:center; margin-bottom:1rem; }
.sub-header  { text-align:center; color:#666; margin-bottom:2rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">📊 NetSuite Close Validator</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Professional financial reporting from a NetSuite GL transaction detail export</p>', unsafe_allow_html=True)

# Instructions
with st.expander("📖 How to use this app", expanded=False):
    st.markdown("""
### How to export from NetSuite

In NetSuite, go to: **Reports → Saved Searches → Transaction Detail**

Include these columns in your saved search:

`Internal ID` · `Date` · `Posting Period` · `Account` · `Account Type` · `Subsidiary` · `Department` · `Debit` · `Credit`

Export as CSV and upload it here.

**What you get:**
- Trial Balance, P&L, and Balance Sheet from your export
- Close Health Check — which periods are balanced, which transactions do not tie
- Download any report as CSV

*Nothing is stored. Everything runs in your session.*
""")

# File upload
st.subheader("📁 Upload GL Transaction Detail CSV")

_sample_path = "sample_data/gl_transactions.csv"
try:
    with open(_sample_path, "rb") as _f:
        st.download_button(
            "⬇️ Download sample gl_transactions.csv",
            _f,
            file_name="gl_transactions.csv",
            mime="text/csv",
            help="Download the sample file to see the expected column format before uploading your own data",
        )
except FileNotFoundError:
    pass

st.caption("Not sure about the format? Download the sample file above, explore it, then upload your own data.")

uploaded_file = st.file_uploader(
    "Select your NetSuite GL export file",
    type=["csv"],
    help="Flat CSV with columns: transaction_id, date, period, account_name, account_type, subsidiary, department, debit, credit",
)

run_button = st.button("🚀 Generate Reports", type="primary", use_container_width=True)

if run_button:
    if uploaded_file is None:
        st.error("❌ Please upload a CSV file before generating reports.")
        st.stop()

    try:
        con, stats = load_all_data(uploaded_file)

        st.success("✅ Data loaded successfully!")

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Rows",     f"{stats['total_rows']:,}")
        col2.metric("Transactions",   f"{stats['transactions']:,}")
        col3.metric("Accounts",       f"{stats['accounts']:,}")
        col4.metric("Subsidiaries",   f"{stats['subsidiaries']:,}")
        col5.metric("Periods",        f"{stats['periods']:,}")

        if stats['total_rows'] > 500_000:
            st.warning("⚠️ Large dataset detected. Processing may take 1–2 minutes.")
        elif stats['total_rows'] > 100_000:
            st.info("ℹ️ Medium dataset. Processing may take 30–60 seconds.")

        st.session_state['con'] = con
        st.session_state['data_loaded'] = True

        st.markdown("---")
        st.info("👈 Use the sidebar to apply filters, then select a report tab below.")

    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.exception(e)
        st.stop()

# Reporting section
if st.session_state.get('data_loaded', False):
    con = st.session_state['con']

    filters = render_filter_sidebar(con)

    with st.spinner("Running data validations..."):
        validations = run_data_validations(con, filters)

    display_validation_metrics(validations)

    st.markdown("---")
    st.subheader("📊 Financial Reports")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Trial Balance",
        "💰 Profit & Loss",
        "📅 Periodised P&L",
        "🏦 Balance Sheet",
        "🔒 Close Health Check",
    ])

    with tab1:
        with st.spinner("Generating Trial Balance..."):
            tb_df = generate_trial_balance(con, filters)
            display_trial_balance(tb_df)

            if not tb_df.empty and len(tb_df) <= 1000:
                pdf_data = export_to_pdf(
                    {
                        'dataframe': tb_df,
                        'metrics': {
                            'Total Accounts': f"{len(tb_df):,}",
                            'Total Debits':   f"${tb_df[tb_df['total_amount'] > 0]['total_amount'].sum():,.2f}",
                            'Total Credits':  f"${abs(tb_df[tb_df['total_amount'] < 0]['total_amount'].sum()):,.2f}",
                        },
                    },
                    "Trial Balance",
                    filters,
                )
                st.download_button("📄 Download Trial Balance PDF", pdf_data, "trial_balance.pdf", "application/pdf")

    with tab2:
        with st.spinner("Generating Profit & Loss..."):
            pnl_df = generate_pnl(con, filters)
            display_pnl(pnl_df)

            if not pnl_df.empty and len(pnl_df) <= 1000:
                from utils.calculations import calculate_pnl_totals
                totals = calculate_pnl_totals(pnl_df)
                pdf_data = export_to_pdf(
                    {
                        'dataframe': pnl_df,
                        'metrics': {
                            'Total Revenue':  f"${totals['revenue']:,.2f}",
                            'Total Expenses': f"${totals['expenses']:,.2f}",
                            'Net Income':     f"${totals['net_income']:,.2f}",
                        },
                    },
                    "Profit & Loss",
                    filters,
                )
                st.download_button("📄 Download P&L PDF", pdf_data, "profit_and_loss.pdf", "application/pdf")

    with tab3:
        with st.spinner("Generating Periodised P&L..."):
            display_periodised_pnl(con, filters)

    with tab4:
        with st.spinner("Generating Balance Sheet..."):
            bs_df = generate_balance_sheet(con, filters)
            display_balance_sheet(bs_df)

            if not bs_df.empty and len(bs_df) <= 1000:
                from utils.calculations import calculate_balance_sheet_totals
                totals = calculate_balance_sheet_totals(bs_df)
                pdf_data = export_to_pdf(
                    {
                        'dataframe': bs_df,
                        'metrics': {
                            'Total Assets':      f"${totals['assets']:,.2f}",
                            'Total Liabilities': f"${abs(totals['liabilities']):,.2f}",
                            'Total Equity':      f"${abs(totals['equity']):,.2f}",
                            'Balance Check':     f"${totals['balance_check']:,.2f}",
                        },
                    },
                    "Balance Sheet",
                    filters,
                )
                st.download_button("📄 Download Balance Sheet PDF", bs_df.to_csv(index=False).encode(), "balance_sheet.csv", "text/csv")

    with tab5:
        display_close_health(con)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#666;'>
<p><b>NetSuite Close Validator</b> | Built with Streamlit &amp; DuckDB</p>
<p>All data processing happens locally — no data is stored or transmitted</p>
<p style='font-size:0.85rem;'>Built by <a href='https://suiteclose.co.uk' target='_blank' style='color:#888; text-decoration:none;'>SuiteClose</a> · suiteclose.co.uk</p>
</div>
""", unsafe_allow_html=True)
