"""
Balance Sheet Report Generation
"""

import streamlit as st
from .transforms import get_base_query_with_filters
from .calculations import calculate_balance_sheet_totals
from .styles import section_header, empty_state, total_row, fmt_money, humanize_account_types
from .export import export_to_pdf


MAX_DISPLAY_ROWS = 5000
MAX_PDF_ROWS = 1000

REPORT_COLUMN_CONFIG = {
    "subsidiary_name": st.column_config.TextColumn("Subsidiary"),
    "account_name":    st.column_config.TextColumn("Account"),
    "account_type":    st.column_config.TextColumn("Type"),
    "total_amount":    st.column_config.NumberColumn("Balance", format="accounting"),
}

# Narrower widths for the half-width Assets / Liabilities / Equity panes
COMPACT_COLUMN_CONFIG = {
    "subsidiary_name": st.column_config.TextColumn("Subsidiary", width="small"),
    "account_name":    st.column_config.TextColumn("Account", width="medium"),
    "account_type":    st.column_config.TextColumn("Type", width="small"),
    "total_amount":    st.column_config.NumberColumn("Balance", format="accounting", width="small"),
}


def generate_balance_sheet(con, filters):
    """
    Generate Balance Sheet report
    
    Args:
        con: DuckDB connection
        filters: Active filters dict
        
    Returns:
        pd.DataFrame: Balance sheet data
    """
    base_query = get_base_query_with_filters(filters)
    
    bs_account_types = [
        'Bank', 'AcctRec', 'OthCurrAsset', 'FixedAsset', 'OthAsset',  # Assets
        'AcctPay', 'OthCurrLiab', 'LongTermLiab',  # Liabilities
        'Equity'  # Equity
    ]
    types_str = ', '.join([f"'{t}'" for t in bs_account_types])
    
    query = f"""
        WITH base_data AS (
            {base_query}
        )
        SELECT
            subsidiary_name,
            account_name,
            account_type,
            ROUND(SUM(amount), 2) AS total_amount
        FROM base_data
        WHERE account_type IN ({types_str})
        GROUP BY 1, 2, 3
        ORDER BY subsidiary_name, account_type, account_name
    """
    
    return con.execute(query).fetchdf()


def display_balance_sheet(bs_df, filters=None):
    """
    Display balance sheet report in Streamlit

    Args:
        bs_df: Balance sheet DataFrame
        filters: Active filters dict (used for PDF metadata)
    """
    section_header(
        "Balance Sheet",
        "Assets, liabilities, and equity for the selected periods.",
    )

    if bs_df.empty:
        empty_state(
            "No rows match your filters",
            "Clear or adjust the filters in the sidebar to see data.",
        )
        return

    totals = calculate_balance_sheet_totals(bs_df)

    # Toolbar: record count left, downloads right
    cap_col, csv_col, pdf_col = st.columns([5, 0.8, 0.8], vertical_alignment="center")
    cap_col.markdown(
        f'<p class="sc-toolbar-caption">{len(bs_df):,} accounts</p>',
        unsafe_allow_html=True,
    )
    csv_col.download_button(
        "CSV", bs_df.to_csv(index=False).encode('utf-8'),
        "balance_sheet.csv", "text/csv",
        type="tertiary", icon=":material/download:", key="bs_csv",
    )
    if len(bs_df) <= MAX_PDF_ROWS:
        pdf_data = export_to_pdf(
            {
                'dataframe': bs_df,
                'metrics': {
                    'Total Assets':      fmt_money(totals['assets']),
                    'Total Liabilities': fmt_money(abs(totals['liabilities'])),
                    'Total Equity':      fmt_money(abs(totals['equity'])),
                    'Balance Check':     fmt_money(totals['balance_check']),
                },
            },
            "Balance Sheet",
            filters,
        )
        pdf_col.download_button(
            "PDF", pdf_data, "balance_sheet.pdf", "application/pdf",
            type="tertiary", icon=":material/download:", key="bs_pdf",
        )

    # Split into sections
    asset_types = ['Bank', 'AcctRec', 'OthCurrAsset', 'FixedAsset', 'OthAsset']
    liability_types = ['AcctPay', 'OthCurrLiab', 'LongTermLiab']
    equity_types = ['Equity']

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="sc-card-title">Assets</p>', unsafe_allow_html=True)
        assets_df = bs_df[bs_df['account_type'].isin(asset_types)]
        if not assets_df.empty:
            st.dataframe(
                humanize_account_types(assets_df), use_container_width=True,
                hide_index=True, height=320, column_config=COMPACT_COLUMN_CONFIG,
            )
        else:
            st.caption("No asset accounts found.")

    with col2:
        st.markdown('<p class="sc-card-title">Liabilities</p>', unsafe_allow_html=True)
        liabilities_df = bs_df[bs_df['account_type'].isin(liability_types)]
        if not liabilities_df.empty:
            st.dataframe(
                humanize_account_types(liabilities_df), use_container_width=True,
                hide_index=True, height=150, column_config=COMPACT_COLUMN_CONFIG,
            )
        else:
            st.caption("No liability accounts found.")

        st.markdown('<p class="sc-card-title">Equity</p>', unsafe_allow_html=True)
        equity_df = bs_df[bs_df['account_type'].isin(equity_types)]
        if not equity_df.empty:
            st.dataframe(
                humanize_account_types(equity_df), use_container_width=True,
                hide_index=True, height=150, column_config=COMPACT_COLUMN_CONFIG,
            )
        else:
            st.caption("No equity accounts found.")

    total_row([
        ("Total assets", fmt_money(totals['assets'])),
        ("Total liabilities", fmt_money(abs(totals['liabilities']))),
        ("Total equity", fmt_money(abs(totals['equity']))),
        ("Balance check", fmt_money(totals['balance_check']),
         "ok" if abs(totals['balance_check']) < 0.01 else "bad"),
    ])

