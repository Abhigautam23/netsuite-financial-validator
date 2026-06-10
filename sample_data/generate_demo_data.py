"""
Demo Data Generator — gl_transactions_demo.csv
Produces a realistic GL with four deliberately planted errors.

Errors planted:
  1. Period balance error   — Mar 2024: $12,500 debit with no matching credit
  2. Volume anomaly         — Jun 2024: 150 extra transactions (~3× monthly average)
  3. Duplicate posting      — Jul 2024: two transaction IDs with identical lines
  4. Missing accrual reversal — Sep 2024: Accrued Payroll posted, no Oct 2024 reversal
"""

import pandas as pd
import random
from datetime import date, timedelta
import os

random.seed(42)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

SUBSIDIARIES = [
    "US Headquarters", "UK Operations", "Germany GmbH",
    "France SAS", "Canada Inc", "Australia Pty Ltd",
]

DEPARTMENTS = ["Engineering", "Sales", "Marketing", "Finance", "Operations", ""]

# Accrual accounts are intentionally excluded from the random pool so the
# accrual-reversal check fires only for the planted error.
ACCOUNTS = [
    ("Cash - Operating",           "Bank"),
    ("Cash - Payroll",             "Bank"),
    ("Accounts Receivable",        "AcctRec"),
    ("Inventory - Finished Goods", "OthCurrAsset"),
    ("Prepaid Insurance",          "OthCurrAsset"),
    ("Equipment",                  "FixedAsset"),
    ("Accumulated Depreciation",   "FixedAsset"),
    ("Accounts Payable",           "AcctPay"),
    ("Payroll Liabilities",        "OthCurrLiab"),
    ("Sales Tax Payable",          "OthCurrLiab"),
    ("Long-term Debt",             "LongTermLiab"),
    ("Common Stock",               "Equity"),
    ("Retained Earnings",          "Equity"),
    ("Product Sales",              "Income"),
    ("Service Revenue",            "Income"),
    ("Interest Income",            "OthIncome"),
    ("Cost of Goods Sold",         "COGS"),
    ("Salaries and Wages",         "Expense"),
    ("Rent Expense",               "Expense"),
    ("Utilities",                  "Expense"),
    ("Marketing and Advertising",  "Expense"),
    ("Professional Fees",          "Expense"),
    ("Interest Expense",           "OthExpense"),
]

ACCOUNT_MAP     = {n: t for n, t in ACCOUNTS}
income_accts    = [n for n, t in ACCOUNTS if t in ("Income", "OthIncome")]
expense_accts   = [n for n, t in ACCOUNTS if t in ("Expense", "COGS", "OthExpense")]
asset_accts     = [n for n, t in ACCOUNTS if t in ("Bank", "AcctRec", "OthCurrAsset")]
liability_accts = [n for n, t in ACCOUNTS if t in ("AcctPay", "OthCurrLiab")]

rows = []
_txn_seq = 50000


def _next_id():
    global _txn_seq
    tid = f"TXN{_txn_seq}"
    _txn_seq += 1
    return tid


def _random_date(year, month):
    start = date(year, month, 1)
    end   = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))


def _period(d):
    return d.strftime("%b %Y")


def _add(txn_id, txn_date, sub, dept, debit_acct, credit_acct, amount):
    period = _period(txn_date)
    for acct, dr, cr in [(debit_acct, amount, 0.0), (credit_acct, 0.0, amount)]:
        rows.append({
            "transaction_id": txn_id,
            "date":           txn_date.isoformat(),
            "period":         period,
            "account_name":   acct,
            "account_type":   ACCOUNT_MAP.get(acct, "Expense"),
            "subsidiary":     sub,
            "department":     dept,
            "debit":          dr,
            "credit":         cr,
        })


# ── Base transactions: 70 per month, all balanced ────────────────────────────
for month in range(1, 13):
    for _ in range(70):
        d    = _random_date(2024, month)
        sub  = random.choice(SUBSIDIARIES)
        dept = random.choice(DEPARTMENTS)
        amt  = round(random.uniform(500, 50_000), 2)
        kind = random.choices(["sale", "expense", "payment"], weights=[0.4, 0.4, 0.2])[0]
        if kind == "sale":
            _add(_next_id(), d, sub, dept, random.choice(asset_accts),    random.choice(income_accts),   amt)
        elif kind == "expense":
            _add(_next_id(), d, sub, dept, random.choice(expense_accts),  random.choice(asset_accts + liability_accts), amt)
        else:
            _add(_next_id(), d, sub, dept, random.choice(liability_accts), random.choice(asset_accts),   amt)

# ── Error 1: Period Balance (Mar 2024) ───────────────────────────────────────
rows.append({
    "transaction_id": "ERR_BAL_001",
    "date":           "2024-03-31",
    "period":         "Mar 2024",
    "account_name":   "Salaries and Wages",
    "account_type":   "Expense",
    "subsidiary":     "US Headquarters",
    "department":     "Finance",
    "debit":          12500.00,
    "credit":         0.0,
})

# ── Error 2: Volume Anomaly (Jun 2024) ───────────────────────────────────────
for _ in range(150):
    d    = _random_date(2024, 6)
    sub  = random.choice(SUBSIDIARIES)
    dept = random.choice(DEPARTMENTS)
    amt  = round(random.uniform(500, 50_000), 2)
    _add(_next_id(), d, sub, dept, random.choice(expense_accts), random.choice(asset_accts + liability_accts), amt)

# ── Error 3: Duplicate Posting (Jul 2024) ────────────────────────────────────
DUP_DATE = date(2024, 7, 15)
DUP_AMT  = 33333.33
DUP_SUB  = "Germany GmbH"
DUP_DEPT = "Finance"
for txn_id in ["TXN_ORIG_001", "TXN_DUPE_001"]:
    _add(txn_id, DUP_DATE, DUP_SUB, DUP_DEPT,
         "Marketing and Advertising", "Accounts Payable", DUP_AMT)

# ── Error 4: Missing Accrual Reversal (Sep 2024) ─────────────────────────────
# Accrual posted in Sep 2024; no reversal in Oct 2024.
_add("ACCR_SEP_001", date(2024, 9, 30), "UK Operations", "Finance",
     "Salaries and Wages", "Accrued Payroll", 8750.00)
# Oct 2024 reversal intentionally omitted.

df = pd.DataFrame(rows)
out = os.path.join(OUTPUT_DIR, "gl_transactions_demo.csv")
df.to_csv(out, index=False)

total_debits  = df["debit"].sum()
total_credits = df["credit"].sum()
by_period     = df.groupby("period")["transaction_id"].nunique()

print(f"Rows:         {len(df):,}")
print(f"Transactions: {df['transaction_id'].nunique():,}")
print(f"Periods:      {df['period'].nunique()}")
print(f"Variance:     ${total_debits - total_credits:,.2f}  (expected $12,500 from planted error 1)")
print(f"Jun 2024 txns:{by_period.get('Jun 2024', 0)}  (expected 220)")
print(f"Saved to {out}")
