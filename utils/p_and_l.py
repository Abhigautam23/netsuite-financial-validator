"""
Profit & Loss Report Generation
Includes periodised reporting (monthly, quarterly, YTD)
"""

import streamlit as st
import pandas as pd
from .transforms import get_base_query_with_filters
from .calculations import calculate_pnl_totals
from .styles import (
    ACCENT, BORDER_STRONG, section_header, empty_state, total_row, fmt_money,
    humanize_account_types,
)
from .export import export_to_pdf


MAX_DISPLAY_ROWS = 5000
MAX_PDF_ROWS = 1000

REVENUE_TYPES = ['Income', 'OthIncome']

REPORT_COLUMN_CONFIG = {
    "subsidiary_name": st.column_config.TextColumn("Subsidiary"),
    "account_name":    st.column_config.TextColumn("Account"),
    "account_type":    st.column_config.TextColumn("Type"),
    "total_amount":    st.column_config.NumberColumn("Amount", format="accounting"),
}


def generate_pnl(con, filters):
    """
    Generate Profit & Loss report

    Args:
        con: DuckDB connection
        filters: Active filters dict

    Returns:
        pd.DataFrame: P&L data
    """
    base_query = get_base_query_with_filters(filters)

    pnl_account_types = ['Income', 'OthIncome', 'Expense', 'COGS', 'OthExpense', 'DeferExpense']
    types_str = ', '.join([f"'{t}'" for t in pnl_account_types])

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


def generate_pnl_by_period(con, filters, period_type='month'):
    """
    Generate periodised P&L report

    Args:
        con: DuckDB connection
        filters: Active filters dict
        period_type: 'month', 'quarter', or 'year'

    Returns:
        pd.DataFrame: Periodised P&L data
    """
    base_query = get_base_query_with_filters(filters)

    pnl_account_types = ['Income', 'OthIncome', 'Expense', 'COGS', 'OthExpense', 'DeferExpense']
    types_str = ', '.join([f"'{t}'" for t in pnl_account_types])

    if period_type == 'month':
        period_cols = "fiscal_year, fiscal_month, period_name"
        group_cols = "1, 2, 3, 4"
        order_cols = "fiscal_year DESC, fiscal_month DESC, account_type"
    elif period_type == 'quarter':
        period_cols = "fiscal_year, fiscal_quarter, period_name"
        group_cols = "1, 2, 3, 4"
        order_cols = "fiscal_year DESC, fiscal_quarter DESC, account_type"
    else:  # year
        period_cols = "fiscal_year"
        group_cols = "1, 2"
        order_cols = "fiscal_year DESC, account_type"

    query = f"""
        WITH base_data AS (
            {base_query}
        )
        SELECT
            {period_cols},
            account_type,
            ROUND(SUM(amount), 2) AS total_amount
        FROM base_data
        WHERE account_type IN ({types_str})
        GROUP BY {group_cols}
        ORDER BY {order_cols}
    """

    return con.execute(query).fetchdf()


def display_pnl(pnl_df, filters=None):
    """
    Display P&L report in Streamlit

    Args:
        pnl_df: P&L DataFrame
        filters: Active filters dict (used for PDF metadata)
    """
    section_header(
        "Profit & Loss",
        "Income and expense accounts for the selected periods.",
    )

    if pnl_df.empty:
        empty_state(
            "No rows match your filters",
            "Clear or adjust the filters in the sidebar to see data.",
        )
        return

    totals = calculate_pnl_totals(pnl_df)
    margin = (totals['net_income'] / totals['revenue'] * 100) if totals['revenue'] else 0

    # Toolbar: record count left, downloads right
    cap_col, csv_col, pdf_col = st.columns([5, 0.8, 0.8], vertical_alignment="center")
    cap_col.markdown(
        f'<p class="sc-toolbar-caption">{len(pnl_df):,} accounts</p>',
        unsafe_allow_html=True,
    )
    csv_col.download_button(
        "CSV", pnl_df.to_csv(index=False).encode('utf-8'),
        "profit_and_loss.csv", "text/csv",
        type="tertiary", icon=":material/download:", key="pnl_csv",
    )
    if len(pnl_df) <= MAX_PDF_ROWS:
        pdf_data = export_to_pdf(
            {
                'dataframe': pnl_df,
                'metrics': {
                    'Total Revenue':  fmt_money(totals['revenue']),
                    'Total Expenses': fmt_money(totals['expenses']),
                    'Net Income':     fmt_money(totals['net_income']),
                },
            },
            "Profit & Loss",
            filters,
        )
        pdf_col.download_button(
            "PDF", pdf_data, "profit_and_loss.pdf", "application/pdf",
            type="tertiary", icon=":material/download:", key="pnl_pdf",
        )

    shown = humanize_account_types(pnl_df.head(MAX_DISPLAY_ROWS))
    st.dataframe(
        shown,
        use_container_width=True,
        hide_index=True,
        height=480,
        column_config=REPORT_COLUMN_CONFIG,
    )
    if len(pnl_df) > MAX_DISPLAY_ROWS:
        st.caption(
            f"Showing first {MAX_DISPLAY_ROWS:,} of {len(pnl_df):,} rows — "
            "download the CSV for the full set."
        )

    total_row([
        ("Revenue", fmt_money(totals['revenue'])),
        ("Expenses", fmt_money(totals['expenses'])),
        ("Net income", f"{fmt_money(totals['net_income'])} ({margin:.1f}% margin)",
         "ok" if totals['net_income'] >= 0 else "bad"),
    ])


def _render_period_table(df, pivot_columns, filename, key):
    """Pivot a periodised P&L frame, format numbers, and add a CSV toolbar."""
    pivot_df = humanize_account_types(df).pivot_table(
        index='account_type',
        columns=pivot_columns,
        values='total_amount',
        aggfunc='sum',
        fill_value=0,
    )

    cap_col, csv_col = st.columns([6, 0.8], vertical_alignment="center")
    cap_col.markdown(
        f'<p class="sc-toolbar-caption">{len(pivot_df)} account types × '
        f'{len(pivot_df.columns)} periods</p>',
        unsafe_allow_html=True,
    )
    csv_col.download_button(
        "CSV", df.to_csv(index=False).encode('utf-8'), filename, "text/csv",
        type="tertiary", icon=":material/download:", key=key,
    )

    st.dataframe(pivot_df.style.format("{:,.2f}"), use_container_width=True)


def display_periodised_pnl(con, filters):
    """
    Display periodised P&L with tabs for different periods

    Args:
        con: DuckDB connection
        filters: Active filters dict
    """
    section_header(
        "Periodised P&L",
        "Revenue and expenses broken down across fiscal periods.",
    )

    monthly_df = generate_pnl_by_period(con, filters, 'month')

    if monthly_df.empty:
        empty_state(
            "No rows match your filters",
            "Clear or adjust the filters in the sidebar to see data.",
        )
        return

    # Monthly revenue vs expenses chart, themed via design-system colours.
    chart_src = monthly_df.copy()
    chart_src['month'] = (
        chart_src['fiscal_year'].astype(int).astype(str) + '-' +
        chart_src['fiscal_month'].astype(int).astype(str).str.zfill(2)
    )
    chart_src['bucket'] = chart_src['account_type'].apply(
        lambda t: 'Revenue' if t in REVENUE_TYPES else 'Expenses'
    )
    chart_df = (
        chart_src.groupby(['month', 'bucket'])['total_amount']
        .sum().abs().unstack(fill_value=0).sort_index()
    )
    for col in ('Revenue', 'Expenses'):
        if col not in chart_df.columns:
            chart_df[col] = 0.0
    st.bar_chart(
        chart_df[['Revenue', 'Expenses']],
        color=[ACCENT, BORDER_STRONG],
        stack=False,
        height=240,
    )

    period_tabs = st.tabs(["Monthly", "Quarterly", "Yearly"])

    with period_tabs[0]:
        _render_period_table(
            monthly_df, ['fiscal_year', 'fiscal_month'], "pnl_monthly.csv", "ppnl_m_csv",
        )

    with period_tabs[1]:
        quarterly_df = generate_pnl_by_period(con, filters, 'quarter')
        if quarterly_df.empty:
            empty_state("No quarterly data available")
        else:
            _render_period_table(
                quarterly_df, ['fiscal_year', 'fiscal_quarter'], "pnl_quarterly.csv", "ppnl_q_csv",
            )

    with period_tabs[2]:
        yearly_df = generate_pnl_by_period(con, filters, 'year')
        if yearly_df.empty:
            empty_state("No yearly data available")
        else:
            _render_period_table(
                yearly_df, 'fiscal_year', "pnl_yearly.csv", "ppnl_y_csv",
            )
