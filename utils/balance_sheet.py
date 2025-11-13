"""
Balance Sheet Report Generation
"""

import streamlit as st
from .transforms import get_base_query_with_filters
from .calculations import calculate_balance_sheet_totals, display_balance_sheet_metrics


MAX_DISPLAY_ROWS = 5000


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


def display_balance_sheet(bs_df):
    """
    Display balance sheet report in Streamlit
    
    Args:
        bs_df: Balance sheet DataFrame
    """
    st.markdown("### 🏦 Balance Sheet")
    
    if bs_df.empty:
        st.warning("No balance sheet data available for selected filters")
        return
    
    # Calculate and display totals
    totals = calculate_balance_sheet_totals(bs_df)
    display_balance_sheet_metrics(totals)
    
    st.markdown("---")
    
    # Split into sections
    asset_types = ['Bank', 'AcctRec', 'OthCurrAsset', 'FixedAsset', 'OthAsset']
    liability_types = ['AcctPay', 'OthCurrLiab', 'LongTermLiab']
    equity_types = ['Equity']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Assets")
        assets_df = bs_df[bs_df['account_type'].isin(asset_types)]
        if not assets_df.empty:
            st.dataframe(assets_df, use_container_width=True, height=300)
        else:
            st.info("No asset accounts found")
    
    with col2:
        st.markdown("#### Liabilities")
        liabilities_df = bs_df[bs_df['account_type'].isin(liability_types)]
        if not liabilities_df.empty:
            st.dataframe(liabilities_df, use_container_width=True, height=150)
        else:
            st.info("No liability accounts found")
        
        st.markdown("#### Equity")
        equity_df = bs_df[bs_df['account_type'].isin(equity_types)]
        if not equity_df.empty:
            st.dataframe(equity_df, use_container_width=True, height=150)
        else:
            st.info("No equity accounts found")
    
    st.markdown("---")
    st.markdown("#### Complete Balance Sheet")
    
    # Display complete data with limit
    if len(bs_df) > MAX_DISPLAY_ROWS:
        st.warning(f"⚠️ Showing first {MAX_DISPLAY_ROWS:,} of {len(bs_df):,} rows. Download CSV for complete data.")
        st.dataframe(
            bs_df.head(MAX_DISPLAY_ROWS),
            use_container_width=True,
            height=400
        )
    else:
        st.dataframe(
            bs_df,
            use_container_width=True,
            height=400
        )
    
    # Download button
    csv = bs_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Balance Sheet CSV",
        data=csv,
        file_name="balance_sheet.csv",
        mime="text/csv",
        use_container_width=True
    )

