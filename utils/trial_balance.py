"""
Trial Balance Report Generation
"""

import streamlit as st
from .transforms import get_base_query_with_filters


MAX_DISPLAY_ROWS = 5000


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


def display_trial_balance(tb_df):
    """
    Display trial balance report in Streamlit
    
    Args:
        tb_df: Trial balance DataFrame
    """
    st.markdown("### 📋 Trial Balance")
    
    if tb_df.empty:
        st.warning("No data available for selected filters")
        return
    
    # Display data with limit
    if len(tb_df) > MAX_DISPLAY_ROWS:
        st.warning(f"⚠️ Showing first {MAX_DISPLAY_ROWS:,} of {len(tb_df):,} rows. Download CSV for complete data.")
        st.dataframe(
            tb_df.head(MAX_DISPLAY_ROWS),
            use_container_width=True,
            height=500
        )
    else:
        st.dataframe(
            tb_df,
            use_container_width=True,
            height=500
        )
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Accounts", f"{len(tb_df):,}")
    
    with col2:
        total_debits = tb_df[tb_df['total_amount'] > 0]['total_amount'].sum()
        st.metric("Total Debits", f"${total_debits:,.2f}")
    
    with col3:
        total_credits = abs(tb_df[tb_df['total_amount'] < 0]['total_amount'].sum())
        st.metric("Total Credits", f"${total_credits:,.2f}")
    
    # Download button
    csv = tb_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Trial Balance CSV",
        data=csv,
        file_name="trial_balance.csv",
        mime="text/csv",
        use_container_width=True
    )

