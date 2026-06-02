"""
Dummy Data Generator for NetSuite Financial Reporting
Generates a flat GL transaction detail CSV for testing.

Usage:
    python sample_data/generate_dummy_data.py

Output:
    sample_data/gl_transactions.csv
    Columns: transaction_id, date, period, account_name, account_type,
             subsidiary, department, debit, credit
"""

import pandas as pd
import numpy as np
from datetime import date, timedelta
import random
import os

random.seed(42)
np.random.seed(42)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

print("🚀 Generating flat GL transaction detail CSV...")

# Reference data
SUBSIDIARIES = [
    "US Headquarters", "UK Operations", "Germany GmbH", "France SAS",
    "Canada Inc", "Australia Pty Ltd", "Japan KK", "Singapore Pte Ltd",
]

DEPARTMENTS = ["Engineering", "Sales", "Marketing", "Finance", "Operations", ""]

ACCOUNTS = [
    # (name, type)
    ("Cash - Operating",                 "Bank"),
    ("Cash - Payroll",                   "Bank"),
    ("Accounts Receivable",              "AcctRec"),
    ("Allowance for Doubtful Accounts",  "AcctRec"),
    ("Inventory - Raw Materials",        "OthCurrAsset"),
    ("Inventory - Finished Goods",       "OthCurrAsset"),
    ("Prepaid Expenses",                 "OthCurrAsset"),
    ("Buildings",                        "FixedAsset"),
    ("Equipment",                        "FixedAsset"),
    ("Accumulated Depreciation",         "FixedAsset"),
    ("Intangible Assets",                "OthAsset"),
    ("Accounts Payable",                 "AcctPay"),
    ("Accrued Expenses",                 "AcctPay"),
    ("Sales Tax Payable",                "OthCurrLiab"),
    ("Payroll Liabilities",              "OthCurrLiab"),
    ("Short-term Loans",                 "OthCurrLiab"),
    ("Long-term Debt",                   "LongTermLiab"),
    ("Common Stock",                     "Equity"),
    ("Retained Earnings",                "Equity"),
    ("Product Sales",                    "Income"),
    ("Service Revenue",                  "Income"),
    ("Consulting Revenue",               "Income"),
    ("Interest Income",                  "OthIncome"),
    ("Cost of Goods Sold - Products",    "COGS"),
    ("Cost of Goods Sold - Services",    "COGS"),
    ("Salaries and Wages",               "Expense"),
    ("Rent Expense",                     "Expense"),
    ("Utilities",                        "Expense"),
    ("Office Supplies",                  "Expense"),
    ("Marketing and Advertising",        "Expense"),
    ("Travel and Entertainment",         "Expense"),
    ("Professional Fees",                "Expense"),
    ("IT and Software",                  "Expense"),
    ("Interest Expense",                 "OthExpense"),
]

ACCOUNT_MAP = {name: acct_type for name, acct_type in ACCOUNTS}

income_accounts  = [n for n, t in ACCOUNTS if t in ("Income", "OthIncome")]
expense_accounts = [n for n, t in ACCOUNTS if t in ("Expense", "COGS", "OthExpense")]
asset_accounts   = [n for n, t in ACCOUNTS if t in ("Bank", "AcctRec", "OthCurrAsset")]
liability_accounts = [n for n, t in ACCOUNTS if t in ("AcctPay", "OthCurrLiab")]


def random_date(start=date(2024, 1, 1), end=date(2024, 12, 31)):
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def period_name(d):
    return d.strftime("%b %Y")


rows = []
NUM_TRANSACTIONS = 2000

print(f"  Generating {NUM_TRANSACTIONS} transactions...")

for txn_num in range(NUM_TRANSACTIONS):
    txn_id   = f"TXN{50000 + txn_num}"
    txn_date = random_date()
    period   = period_name(txn_date)
    sub      = random.choice(SUBSIDIARIES)
    dept     = random.choice(DEPARTMENTS)
    amount   = round(random.uniform(100, 50_000), 2)

    txn_type = random.choices(
        ["sale", "expense", "payment", "receipt"],
        weights=[0.35, 0.35, 0.15, 0.15],
    )[0]

    def add(acct, is_debit):
        rows.append({
            "transaction_id": txn_id,
            "date":           txn_date.isoformat(),
            "period":         period,
            "account_name":   acct,
            "account_type":   ACCOUNT_MAP[acct],
            "subsidiary":     sub,
            "department":     dept,
            "debit":          amount if is_debit else 0.0,
            "credit":         0.0    if is_debit else amount,
        })

    if txn_type == "sale":
        add(random.choice(asset_accounts),  True)   # Debit AR/Cash
        add(random.choice(income_accounts), False)  # Credit Revenue
    elif txn_type == "expense":
        add(random.choice(expense_accounts),              True)   # Debit Expense
        add(random.choice(asset_accounts + liability_accounts), False)  # Credit Cash/AP
    elif txn_type == "payment":
        add(random.choice(liability_accounts), True)   # Debit AP
        add(random.choice(asset_accounts),     False)  # Credit Cash
    else:  # receipt
        add(random.choice(asset_accounts), True)   # Debit Cash
        add(random.choice(asset_accounts), False)  # Credit AR

df = pd.DataFrame(rows)
output_path = os.path.join(OUTPUT_DIR, "gl_transactions.csv")
df.to_csv(output_path, index=False)

total_debits  = df["debit"].sum()
total_credits = df["credit"].sum()

print(f"\n{'='*55}")
print("📊 SUMMARY")
print(f"{'='*55}")
print(f"Rows:                      {len(df):>10,}")
print(f"Transactions:              {df['transaction_id'].nunique():>10,}")
print(f"Accounts:                  {df['account_name'].nunique():>10,}")
print(f"Subsidiaries:              {df['subsidiary'].nunique():>10,}")
print(f"Periods:                   {df['period'].nunique():>10,}")
print(f"Total Debits:  ${total_debits:>18,.2f}")
print(f"Total Credits: ${total_credits:>18,.2f}")
print(f"Variance:      ${total_debits - total_credits:>18,.2f}")
print(f"{'='*55}")
print(f"✅ Saved to {output_path}")
print("🚀 Upload gl_transactions.csv in the Streamlit app to test.")
