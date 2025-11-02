import streamlit as st
from src.data_loader import load_csv, load_sql
from src.transform import merge_transactions_accounts, compute_pnl
from src.utils import CONFIG


def run_cli():
    """Run in terminal/console mode."""
    # --- Load Data ---
    if CONFIG["data_source"] == "csv":
        transactions = load_csv("transactions.csv", CONFIG["csv_base_path"])
        accounts = load_csv("accounts.csv", CONFIG["csv_base_path"])
    else:
        transactions = load_sql("SELECT * FROM transactions", CONFIG["sql_connection_string"])
        accounts = load_sql("SELECT * FROM accounts", CONFIG["sql_connection_string"])

    # --- Transform ---
    merged_df = merge_transactions_accounts(transactions, accounts)
    pnl_summary, pnl_monthly = compute_pnl(merged_df)

    # --- Output ---
    print("\nP&L Summary:")
    print(pnl_summary)


def run_streamlit():
    """Run Streamlit dashboard mode."""
    st.title("🧾 NetSuite P&L Validator")

    # Data source selection
    data_source = st.radio("Select Data Source:", ("CSV", "SQL"), horizontal=True)

    if data_source == "CSV":
        st.write("Using local CSV files from the `data/` folder.")
        transactions = load_csv("transactions.csv", "data/")
        accounts = load_csv("accounts.csv", "data/")
    else:
        st.write("Using SQL connection from config.")
        transactions = load_sql("SELECT * FROM transactions", CONFIG["sql_connection_string"])
        accounts = load_sql("SELECT * FROM accounts", CONFIG["sql_connection_string"])

    # Process and Display
    merged = merge_transactions_accounts(transactions, accounts)
    summary, monthly = compute_pnl(merged)

    st.subheader("📊 P&L Summary")
    st.dataframe(summary)

    # Monthly visualization
    if not monthly.empty:
        st.subheader("📈 Monthly P&L Trends")
        pivot = monthly.pivot(index="month", columns="account_type", values="amount").fillna(0)
        st.line_chart(pivot)


if __name__ == "__main__":
    run_streamlit()
