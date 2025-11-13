"""
Dummy Data Generator for NetSuite Financial Reporting MVP
Generates realistic sample data for testing without real NetSuite exports

Usage:
    python sample_data/generate_dummy_data.py

Output:
    Creates 5 CSV files in sample_data/ directory:
    - account.csv
    - subsidiary.csv
    - transaction.csv
    - transactionline.csv
    - transactionaccountingline.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# Set seed for reproducibility
random.seed(42)
np.random.seed(42)

# Output directory
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

print("🚀 Starting NetSuite dummy data generation...")
print(f"📁 Output directory: {OUTPUT_DIR}")

# ============================================================================
# 1. Generate Subsidiaries (10 subsidiaries)
# ============================================================================
print("\n📊 Generating subsidiaries...")

subsidiaries = [
    {"id": 1, "name": "US Headquarters"},
    {"id": 2, "name": "UK Operations"},
    {"id": 3, "name": "Germany GmbH"},
    {"id": 4, "name": "France SAS"},
    {"id": 5, "name": "Canada Inc"},
    {"id": 6, "name": "Australia Pty Ltd"},
    {"id": 7, "name": "Japan KK"},
    {"id": 8, "name": "Singapore Pte Ltd"},
    {"id": 9, "name": "Mexico SA"},
    {"id": 10, "name": "Brazil Ltda"},
]

df_subsidiary = pd.DataFrame(subsidiaries)
print(f"✅ Generated {len(df_subsidiary)} subsidiaries")

# ============================================================================
# 2. Generate Chart of Accounts (200 accounts)
# ============================================================================
print("\n📊 Generating chart of accounts...")

# Define account structure
account_definitions = [
    # Assets - Bank
    ("Cash - Operating", "Bank", 10),
    ("Cash - Payroll", "Bank", 1),
    ("Cash - Savings", "Bank", 2),
    
    # Assets - Accounts Receivable
    ("Accounts Receivable", "AcctRec", 15),
    ("Allowance for Doubtful Accounts", "AcctRec", 2),
    
    # Assets - Other Current Assets
    ("Inventory - Raw Materials", "OthCurrAsset", 8),
    ("Inventory - Finished Goods", "OthCurrAsset", 8),
    ("Prepaid Expenses", "OthCurrAsset", 5),
    ("Employee Advances", "OthCurrAsset", 3),
    
    # Assets - Fixed Assets
    ("Buildings", "FixedAsset", 5),
    ("Equipment", "FixedAsset", 10),
    ("Furniture and Fixtures", "FixedAsset", 5),
    ("Vehicles", "FixedAsset", 5),
    ("Accumulated Depreciation", "FixedAsset", 8),
    
    # Assets - Other Assets
    ("Intangible Assets", "OthAsset", 5),
    ("Long-term Investments", "OthAsset", 3),
    ("Security Deposits", "OthAsset", 2),
    
    # Liabilities - Accounts Payable
    ("Accounts Payable", "AcctPay", 15),
    ("Accrued Expenses", "AcctPay", 8),
    
    # Liabilities - Other Current Liabilities
    ("Sales Tax Payable", "OthCurrLiab", 5),
    ("Payroll Liabilities", "OthCurrLiab", 8),
    ("Credit Cards Payable", "OthCurrLiab", 5),
    ("Short-term Loans", "OthCurrLiab", 3),
    
    # Liabilities - Long Term
    ("Long-term Debt", "LongTermLiab", 5),
    ("Deferred Tax Liability", "LongTermLiab", 3),
    
    # Equity
    ("Common Stock", "Equity", 2),
    ("Retained Earnings", "Equity", 2),
    ("Additional Paid-in Capital", "Equity", 2),
    
    # Income
    ("Product Sales", "Income", 15),
    ("Service Revenue", "Income", 10),
    ("Consulting Revenue", "Income", 5),
    
    # Other Income
    ("Interest Income", "OthIncome", 3),
    ("Gain on Asset Sales", "OthIncome", 2),
    
    # Cost of Goods Sold
    ("Cost of Goods Sold - Products", "COGS", 10),
    ("Cost of Goods Sold - Services", "COGS", 8),
    ("Freight and Shipping", "COGS", 5),
    
    # Expenses
    ("Salaries and Wages", "Expense", 12),
    ("Rent Expense", "Expense", 8),
    ("Utilities", "Expense", 6),
    ("Office Supplies", "Expense", 5),
    ("Marketing and Advertising", "Expense", 8),
    ("Travel and Entertainment", "Expense", 6),
    ("Insurance", "Expense", 4),
    ("Professional Fees", "Expense", 5),
    ("Depreciation Expense", "Expense", 4),
    ("IT and Software", "Expense", 5),
    
    # Other Expenses
    ("Interest Expense", "OthExpense", 3),
    ("Loss on Asset Disposal", "OthExpense", 2),
]

accounts = []
account_id = 1000

for base_name, acct_type, count in account_definitions:
    for i in range(count):
        if count == 1:
            fullname = base_name
        else:
            fullname = f"{base_name} - {i+1:02d}"
        
        accounts.append({
            "id": account_id,
            "fullname": fullname,
            "accttype": acct_type
        })
        account_id += 1

df_account = pd.DataFrame(accounts)
print(f"✅ Generated {len(df_account)} accounts")

# ============================================================================
# 3. Generate Transactions (2,000 transactions)
# ============================================================================
print("\n📊 Generating transactions...")

num_transactions = 2000
transaction_ids = list(range(50000, 50000 + num_transactions))

df_transaction = pd.DataFrame({
    "id": transaction_ids
})
print(f"✅ Generated {len(df_transaction)} transactions")

# ============================================================================
# 4. Generate Transaction Lines (4,000 lines)
# ============================================================================
print("\n📊 Generating transaction lines...")

# Each transaction gets 1-3 lines on average (targeting 4000 total)
transaction_lines = []
line_id = 1

for txn_id in transaction_ids:
    # Randomly assign 1-3 lines per transaction
    num_lines = random.choices([1, 2, 3], weights=[0.3, 0.5, 0.2])[0]
    
    for _ in range(num_lines):
        transaction_lines.append({
            "transaction": txn_id,
            "subsidiary": random.choice(df_subsidiary["id"].tolist())
        })
        line_id += 1

df_transactionline = pd.DataFrame(transaction_lines)
print(f"✅ Generated {len(df_transactionline)} transaction lines")

# ============================================================================
# 5. Generate Transaction Accounting Lines (4,000+ lines)
# ============================================================================
print("\n📊 Generating transaction accounting lines...")

# For each transaction, create balanced accounting entries (debits = credits)
accounting_lines = []

for txn_id in transaction_ids:
    # Get account type categories for realistic transactions
    income_accounts = df_account[df_account["accttype"].isin(["Income", "OthIncome"])]["id"].tolist()
    expense_accounts = df_account[df_account["accttype"].isin(["Expense", "COGS", "OthExpense"])]["id"].tolist()
    asset_accounts = df_account[df_account["accttype"].isin(["Bank", "AcctRec", "OthCurrAsset"])]["id"].tolist()
    liability_accounts = df_account[df_account["accttype"].isin(["AcctPay", "OthCurrLiab"])]["id"].tolist()
    
    # Generate different transaction types
    txn_type = random.choices(
        ["sale", "expense", "payment", "receipt"],
        weights=[0.35, 0.35, 0.15, 0.15]
    )[0]
    
    # Base amount for transaction
    amount = round(random.uniform(100, 50000), 2)
    
    if txn_type == "sale":
        # Debit: AR or Cash, Credit: Revenue
        accounting_lines.append({
            "transaction": txn_id,
            "account": random.choice(asset_accounts),
            "amount": amount  # Debit (positive)
        })
        accounting_lines.append({
            "transaction": txn_id,
            "account": random.choice(income_accounts),
            "amount": -amount  # Credit (negative)
        })
        
    elif txn_type == "expense":
        # Debit: Expense, Credit: Cash or AP
        accounting_lines.append({
            "transaction": txn_id,
            "account": random.choice(expense_accounts),
            "amount": amount  # Debit (positive)
        })
        accounting_lines.append({
            "transaction": txn_id,
            "account": random.choice(asset_accounts + liability_accounts),
            "amount": -amount  # Credit (negative)
        })
        
    elif txn_type == "payment":
        # Debit: AP, Credit: Cash
        accounting_lines.append({
            "transaction": txn_id,
            "account": random.choice(liability_accounts),
            "amount": amount  # Debit (positive)
        })
        accounting_lines.append({
            "transaction": txn_id,
            "account": random.choice(asset_accounts),
            "amount": -amount  # Credit (negative)
        })
        
    else:  # receipt
        # Debit: Cash, Credit: AR
        accounting_lines.append({
            "transaction": txn_id,
            "account": random.choice(asset_accounts),
            "amount": amount  # Debit (positive)
        })
        accounting_lines.append({
            "transaction": txn_id,
            "account": random.choice(asset_accounts),
            "amount": -amount  # Credit (negative)
        })

df_tal = pd.DataFrame(accounting_lines)
print(f"✅ Generated {len(df_tal)} transaction accounting lines")

# ============================================================================
# 6. Save all files to CSV
# ============================================================================
print("\n💾 Saving CSV files...")

files = {
    "account.csv": df_account,
    "subsidiary.csv": df_subsidiary,
    "transaction.csv": df_transaction,
    "transactionline.csv": df_transactionline,
    "transactionaccountingline.csv": df_tal
}

for filename, df in files.items():
    filepath = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(filepath, index=False)
    print(f"  ✅ {filename} ({len(df):,} rows)")

# ============================================================================
# 7. Print Summary Statistics
# ============================================================================
print("\n" + "="*60)
print("📊 SUMMARY STATISTICS")
print("="*60)
print(f"Subsidiaries:               {len(df_subsidiary):>10,}")
print(f"Accounts:                   {len(df_account):>10,}")
print(f"Transactions:               {len(df_transaction):>10,}")
print(f"Transaction Lines:          {len(df_transactionline):>10,}")
print(f"Accounting Lines:           {len(df_tal):>10,}")
print("="*60)

# Verify accounting balance
total_debits = df_tal[df_tal["amount"] > 0]["amount"].sum()
total_credits = abs(df_tal[df_tal["amount"] < 0]["amount"].sum())
balance_diff = total_debits - total_credits

print(f"\n💰 ACCOUNTING VERIFICATION")
print(f"Total Debits:               ${total_debits:>15,.2f}")
print(f"Total Credits:              ${total_credits:>15,.2f}")
print(f"Difference:                 ${balance_diff:>15,.2f}")

if abs(balance_diff) < 1:
    print("✅ Books are balanced!")
else:
    print("⚠️  Minor rounding difference detected")

print("\n✨ Data generation complete!")
print(f"📁 Files saved to: {OUTPUT_DIR}")
print("\n🚀 Ready to test! Upload these files in the Streamlit app.")




