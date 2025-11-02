import pandas as pd

def merge_transactions_accounts(transactions: pd.DataFrame, accounts: pd.DataFrame) -> pd.DataFrame:
    """
    Merge transactions with accounts to attach account details like name and type.
    """
    # Identify common fields in both dataframes
    common_cols = set(transactions.columns).intersection(set(accounts.columns))
    
    # Join on account_id
    df = transactions.merge(
        accounts[['account_id', 'account_name', 'type', 'parent_id']],
        on='account_id', how='left'
    )

    # Rename overlapping 'type' columns for clarity
    if 'type_x' in df.columns and 'type_y' in df.columns:
        df.rename(columns={'type_x': 'transaction_type', 'type_y': 'account_type'}, inplace=True)
    elif 'type' in df.columns:
        df.rename(columns={'type': 'transaction_type'}, inplace=True)

    print(f"Merged transactions ({len(transactions)}) with accounts ({len(accounts)}). Result: {len(df)} rows.")
    return df


def compute_pnl(df: pd.DataFrame):
    """
    Compute monthly and overall Profit & Loss summary.
    Performs a ledger balance check to verify accounting integrity.
    """

    # Date Parsing
    if 'date' not in df.columns:
        raise KeyError("Expected a 'date' column in transactions data.")

    # dayfirst=True for EU-style dates (dd/mm/yyyy)
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df["month"] = df["date"].dt.to_period("M")

    # Filter P&L Accounts
    pnl_data = df[df["account_type"].isin(["Income", "Expense", "COGS"])].copy()

    # Reverse income sign to follow accounting standards
    if (pnl_data.loc[pnl_data["account_type"] == "Income", "amount"] > 0).any():
      pnl_data.loc[pnl_data["account_type"] == "Income", "amount"] *= -1

    # Monthly Aggregation
    pnl_monthly = (
        pnl_data.groupby(["month", "account_type"])["amount"]
        .sum()
        .reset_index()
    )

    # Overall Summary
    pnl_summary = (
        pnl_data.groupby("account_type")["amount"]
        .sum()
        .reset_index()
    )

    # Ledger Balance Validation
    total_balance = round(pnl_summary["amount"].sum(), 2)
    if total_balance != 0:
        print(f"Warning: Ledger imbalance detected (Total = {total_balance}). "
              "Verify Income/Expense/COGS signs or data integrity.")
    else:
        print(f"P&L summary generated for {pnl_monthly['month'].nunique()} months. "
              "Ledger balanced correctly.")

    return pnl_summary, pnl_monthly

