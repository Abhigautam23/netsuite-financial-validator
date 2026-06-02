"""
Close Health Check
Debit/credit balance checks per period and per transaction
"""

import streamlit as st


def _period_balance(con):
    return con.execute("""
        SELECT
            period,
            ROUND(SUM(debit),  2) AS total_debits,
            ROUND(SUM(credit), 2) AS total_credits,
            ROUND(SUM(debit) - SUM(credit), 2) AS variance
        FROM gl_transactions
        GROUP BY period
        ORDER BY period
    """).fetchdf()


def _unbalanced_transactions(con):
    return con.execute("""
        SELECT
            transaction_id,
            period,
            ROUND(SUM(debit),  2) AS total_debits,
            ROUND(SUM(credit), 2) AS total_credits,
            ROUND(SUM(debit) - SUM(credit), 2) AS variance
        FROM gl_transactions
        GROUP BY transaction_id, period
        HAVING ABS(SUM(debit) - SUM(credit)) > 0.01
        ORDER BY ABS(SUM(debit) - SUM(credit)) DESC
    """).fetchdf()


def _missing_data(con):
    return con.execute("""
        SELECT
            COUNT(*) FILTER (WHERE account_name  IS NULL OR account_name  = '') AS missing_account,
            COUNT(*) FILTER (WHERE subsidiary     IS NULL OR subsidiary    = '') AS missing_subsidiary,
            COUNT(*) FILTER (WHERE period         IS NULL OR period        = '') AS missing_period,
            COUNT(*) FILTER (WHERE date           IS NULL)                       AS missing_date
        FROM gl_transactions
    """).fetchone()


def display_close_health(con):
    st.markdown("### 🔒 Close Health Check")

    # Overall debit/credit balance
    row = con.execute("""
        SELECT
            ROUND(SUM(debit),  2) AS total_debits,
            ROUND(SUM(credit), 2) AS total_credits,
            ROUND(SUM(debit) - SUM(credit), 2) AS variance
        FROM gl_transactions
    """).fetchone()

    total_debits  = row[0] or 0.0
    total_credits = row[1] or 0.0
    variance      = row[2] or 0.0

    st.markdown("#### Overall Debit / Credit Balance")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Debits",  f"${total_debits:,.2f}")
    with col2:
        st.metric("Total Credits", f"${total_credits:,.2f}")
    with col3:
        st.metric("Variance", f"${variance:,.2f}")
        if abs(variance) < 0.01:
            st.success("✅ Books balanced")
        elif abs(variance) < 100:
            st.warning("⚠️ Minor variance")
        else:
            st.error("❌ Out of balance")

    st.markdown("---")

    # Per-period balance
    st.markdown("#### Balance by Period")
    period_df = _period_balance(con)
    if period_df.empty:
        st.info("No period data found.")
    else:
        balanced_count   = int((period_df['variance'].abs() < 0.01).sum())
        unbalanced_count = len(period_df) - balanced_count

        col1, col2 = st.columns(2)
        col1.metric("Balanced Periods",   balanced_count)
        col2.metric("Unbalanced Periods", unbalanced_count, delta_color="inverse")

        st.dataframe(period_df, use_container_width=True, height=300)

        csv = period_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Period Balance CSV",
            csv,
            "period_balance.csv",
            "text/csv",
        )

    st.markdown("---")

    # Unbalanced transactions
    st.markdown("#### Unbalanced Transactions")
    unbal_df = _unbalanced_transactions(con)
    if unbal_df.empty:
        st.success("✅ All transactions are balanced.")
    else:
        st.warning(f"⚠️ {len(unbal_df):,} unbalanced transaction(s) found.")
        st.dataframe(unbal_df, use_container_width=True, height=300)

        csv = unbal_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Unbalanced Transactions CSV",
            csv,
            "unbalanced_transactions.csv",
            "text/csv",
        )

    st.markdown("---")

    # Data completeness
    st.markdown("#### Data Completeness")
    m = _missing_data(con)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Missing Account",    m[0], delta_color="inverse")
    col2.metric("Missing Subsidiary", m[1], delta_color="inverse")
    col3.metric("Missing Period",     m[2], delta_color="inverse")
    col4.metric("Missing Date",       m[3], delta_color="inverse")
