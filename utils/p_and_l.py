"""
Profit & Loss Report Generation
Includes periodised reporting (monthly, quarterly, YTD)
"""

import streamlit as st
import pandas as pd
from .transforms import get_base_query_with_filters
from .calculations import calculate_pnl_totals, display_pnl_metrics


MAX_DISPLAY_ROWS = 5000


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


def display_pnl(pnl_df):
    """
    Display P&L report in Streamlit
    
    Args:
        pnl_df: P&L DataFrame
    """
    st.markdown("### 💰 Profit & Loss Statement")
    
    if pnl_df.empty:
        st.warning("No P&L data available for selected filters")
        return
    
    # Calculate and display totals
    totals = calculate_pnl_totals(pnl_df)
    display_pnl_metrics(totals)
    
    st.markdown("---")
    
    # Display data with limit
    if len(pnl_df) > MAX_DISPLAY_ROWS:
        st.warning(f"⚠️ Showing first {MAX_DISPLAY_ROWS:,} of {len(pnl_df):,} rows. Download CSV for complete data.")
        st.dataframe(
            pnl_df.head(MAX_DISPLAY_ROWS),
            use_container_width=True,
            height=500
        )
    else:
        st.dataframe(
            pnl_df,
            use_container_width=True,
            height=500
        )
    
    # Download button
    csv = pnl_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download P&L CSV",
        data=csv,
        file_name="profit_and_loss.csv",
        mime="text/csv",
        use_container_width=True
    )


def display_periodised_pnl(con, filters):
    """
    Display periodised P&L with tabs for different periods
    
    Args:
        con: DuckDB connection
        filters: Active filters dict
    """
    st.markdown("### 📅 Periodised P&L")
    
    period_tabs = st.tabs(["Monthly", "Quarterly", "Yearly"])
    
    with period_tabs[0]:
        st.markdown("#### Monthly P&L")
        monthly_df = generate_pnl_by_period(con, filters, 'month')
        
        if not monthly_df.empty:
            # Pivot table for better view
            if 'fiscal_month' in monthly_df.columns:
                pivot_df = monthly_df.pivot_table(
                    index='account_type',
                    columns=['fiscal_year', 'fiscal_month'],
                    values='total_amount',
                    aggfunc='sum',
                    fill_value=0
                )
                st.dataframe(pivot_df, use_container_width=True)
            else:
                st.dataframe(monthly_df, use_container_width=True)
            
            csv = monthly_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Monthly P&L CSV",
                data=csv,
                file_name="pnl_monthly.csv",
                mime="text/csv"
            )
        else:
            st.info("No monthly data available")
    
    with period_tabs[1]:
        st.markdown("#### Quarterly P&L")
        quarterly_df = generate_pnl_by_period(con, filters, 'quarter')
        
        if not quarterly_df.empty:
            # Pivot table for better view
            if 'fiscal_quarter' in quarterly_df.columns:
                pivot_df = quarterly_df.pivot_table(
                    index='account_type',
                    columns=['fiscal_year', 'fiscal_quarter'],
                    values='total_amount',
                    aggfunc='sum',
                    fill_value=0
                )
                st.dataframe(pivot_df, use_container_width=True)
            else:
                st.dataframe(quarterly_df, use_container_width=True)
            
            csv = quarterly_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Quarterly P&L CSV",
                data=csv,
                file_name="pnl_quarterly.csv",
                mime="text/csv"
            )
        else:
            st.info("No quarterly data available")
    
    with period_tabs[2]:
        st.markdown("#### Yearly P&L")
        yearly_df = generate_pnl_by_period(con, filters, 'year')
        
        if not yearly_df.empty:
            # Pivot table for better view
            if 'fiscal_year' in yearly_df.columns:
                pivot_df = yearly_df.pivot_table(
                    index='account_type',
                    columns='fiscal_year',
                    values='total_amount',
                    aggfunc='sum',
                    fill_value=0
                )
                st.dataframe(pivot_df, use_container_width=True)
            else:
                st.dataframe(yearly_df, use_container_width=True)
            
            csv = yearly_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Yearly P&L CSV",
                data=csv,
                file_name="pnl_yearly.csv",
                mime="text/csv"
            )
        else:
            st.info("No yearly data available")

