# NetSuite Close Validator

> Validate your NetSuite period-end close from a single CSV export.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Live:** [validator.suiteclose.co.uk](https://validator.suiteclose.co.uk)

---

## What it does

Upload one flat GL transaction detail CSV exported from NetSuite. The tool generates five report tabs instantly, all processed in-memory — no data is stored.

| Tab | Description |
|-----|-------------|
| Trial Balance | Account balances by subsidiary with debit/credit totals |
| P&L | Revenue vs expenses with net income and margin |
| Periodised P&L | Monthly, quarterly, and yearly P&L pivot |
| Balance Sheet | Assets, liabilities, and equity with balance check |
| Close Health Check | Data quality flags to catch close issues early |

---

## Required CSV format

Export a flat GL transaction detail from NetSuite with these columns:

| Column | Description |
|--------|-------------|
| `transaction_id` | Unique transaction identifier |
| `date` | Transaction date |
| `period` | Accounting period name |
| `account_name` | Account full name |
| `account_type` | NetSuite account type (e.g. Income, Expense, Bank) |
| `subsidiary` | Subsidiary name |
| `department` | Department name |
| `debit` | Debit amount (blank or 0 if credit) |
| `credit` | Credit amount (blank or 0 if debit) |

A sample file is available to download from the app sidebar.

---

## Run locally

```bash
git clone <repository-url>
cd netsuite_data
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`.

---

## Stack

- [Streamlit](https://streamlit.io/) — UI framework
- [DuckDB](https://duckdb.org/) — in-memory SQL analytics
- [Pandas](https://pandas.pydata.org/) — data wrangling

---

## License

MIT — see [LICENSE](LICENSE).
