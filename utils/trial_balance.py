"""
Trial Balance Report Generation
"""

import streamlit as st
from .transforms import get_base_query_with_filters
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


def generate_trial_balance(con, filters):
    """
    Generate Trial Balance report
    
    Args:
        con: DuckDB connection
        filters: Active filters dict
        
    Returns:
        pd.DataFrame: Trial balance data
    """
    base_query = get_base_query_with_filters(filters)
    
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
        GROUP BY 1, 2, 3
        ORDER BY subsidiary_name, account_name
    """
    
    return con.execute(query).fetchdf()


def display_trial_balance(tb_df, filters=None):
    """
    Display trial balance report in Streamlit

    Args:
        tb_df: Trial balance DataFrame
        filters: Active filters dict (used for PDF metadata)
    """
    section_header(
        "Trial Balance",
        "Net balance by account — debits positive, credits negative.",
    )

    if tb_df.empty:
        empty_state(
            "No rows match your filters",
            "Clear or adjust the filters in the sidebar to see data.",
        )
        return

    total_debits = tb_df[tb_df['total_amount'] > 0]['total_amount'].sum()
    total_credits = abs(tb_df[tb_df['total_amount'] < 0]['total_amount'].sum())
    difference = round(total_debits - total_credits, 2)

    # Toolbar: record count left, downloads right
    cap_col, csv_col, pdf_col = st.columns([5, 0.8, 0.8], vertical_alignment="center")
    cap_col.markdown(
        f'<p class="sc-toolbar-caption">{len(tb_df):,} accounts</p>',
        unsafe_allow_html=True,
    )
    csv_col.download_button(
        "CSV", tb_df.to_csv(index=False).encode('utf-8'),
        "trial_balance.csv", "text/csv",
        type="tertiary", icon=":material/download:", key="tb_csv",
    )
    if len(tb_df) <= MAX_PDF_ROWS:
        pdf_data = export_to_pdf(
            {
                'dataframe': tb_df,
                'metrics': {
                    'Total Accounts': f"{len(tb_df):,}",
                    'Total Debits':   fmt_money(total_debits),
                    'Total Credits':  fmt_money(total_credits),
                },
            },
            "Trial Balance",
            filters,
        )
        pdf_col.download_button(
            "PDF", pdf_data, "trial_balance.pdf", "application/pdf",
            type="tertiary", icon=":material/download:", key="tb_pdf",
        )

    shown = humanize_account_types(tb_df.head(MAX_DISPLAY_ROWS))
    st.dataframe(
        shown,
        use_container_width=True,
        hide_index=True,
        height=480,
        column_config=REPORT_COLUMN_CONFIG,
    )
    if len(tb_df) > MAX_DISPLAY_ROWS:
        st.caption(
            f"Showing first {MAX_DISPLAY_ROWS:,} of {len(tb_df):,} rows — "
            "download the CSV for the full set."
        )

    total_row([
        ("Total debits", fmt_money(total_debits)),
        ("Total credits", fmt_money(total_credits)),
        ("Difference", fmt_money(difference),
         "ok" if abs(difference) < 0.01 else "bad"),
    ])

