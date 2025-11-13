# NetSuite Financial Reporting MVP

> **Professional financial reporting from NetSuite CSV exports**  
> Built with Streamlit, DuckDB, and Python

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

---

## 🎯 Overview

A production-ready web application for analyzing NetSuite financial data. Upload CSV exports and instantly generate:

- **Trial Balance** - Complete account balances by subsidiary
- **Profit & Loss** - Revenue and expenses with periodization
- **Balance Sheet** - Assets, liabilities, and equity

**Key Features:**
- ✅ 100% client-side processing (no data stored)
- ✅ Advanced filtering (subsidiary, period, department, account type)
- ✅ Periodised P&L (monthly, quarterly, yearly)
- ✅ PDF and CSV exports
- ✅ Data quality validations
- ✅ Handles incomplete data gracefully

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd netsuite_data

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Test with Sample Data

Sample data is included in `sample_data/` folder. Upload these files to test:
- account.csv
- subsidiary.csv  
- transaction.csv
- transactionline.csv
- transactionaccountingline.csv

---

## 📁 Required CSV Files

### 1. account.csv
**Columns:** `id`, `fullname`, `accttype`

Chart of accounts with account types:
- **Assets**: Bank, AcctRec, OthCurrAsset, FixedAsset, OthAsset
- **Liabilities**: AcctPay, OthCurrLiab, LongTermLiab
- **Equity**: Equity
- **Revenue**: Income, OthIncome
- **Expenses**: Expense, COGS, OthExpense, DeferExpense

### 2. subsidiary.csv
**Columns:** `id`, `name`

List of company subsidiaries.

### 3. transaction.csv
**Columns:** `id`, `trandate` (optional), `postingperiod` (optional), `posting` (optional)

Transaction headers. The app automatically handles the `posting` field to filter out non-posting transactions.

### 4. transactionline.csv
**Columns:** `transaction`, `subsidiary`, `department` (optional)

Transaction line items linking transactions to subsidiaries.

### 5. transactionaccountingline.csv
**Columns:** `transaction`, `account`, `amount`

Accounting entries with amounts (positive = debit, negative = credit).

### 6. accountingperiod.csv (Optional)
**Columns:** `id`, `periodname`, `fiscalyear`, `quarter`, `month`

Enables period-based filtering and periodised P&L reports.

---

## 🎛️ Features

### Advanced Filtering

Use the sidebar to filter reports by:
- **Subsidiaries** - Multi-select specific entities
- **Periods** - Select accounting periods  
- **Departments** - Filter by department
- **Account Types** - Filter by account classification
- **Non-Posting** - Optional checkbox to exclude non-posting transactions

### Financial Reports

#### Trial Balance
- All accounts with balances by subsidiary
- Debit and credit totals
- Export to CSV/PDF

#### Profit & Loss
- Revenue vs Expenses
- Net Income calculation
- Profit margin %
- Export to CSV/PDF

#### Periodised P&L (New!)
- **Monthly View** - P&L by month with pivot tables
- **Quarterly View** - P&L by quarter
- **Yearly View** - P&L by fiscal year
- Separate CSV exports for each view

#### Balance Sheet
- Assets, Liabilities, Equity
- Accounting equation check (A = L + E)
- Sectioned view for easy analysis
- Export to CSV/PDF

### Data Quality Checks

Automatic validations:
- Null account detection
- Missing subsidiary detection
- Non-posting transaction counts
- Accounting equation balance verification

### Export Options

- **CSV Export** - Complete data with no row limits
- **PDF Export** - Professional formatted reports with metrics

---

## 🏗️ Project Structure

```
netsuite_data/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore rules
│
├── utils/                          # Core utilities (modular)
│   ├── load_data.py               # Data loading & normalization
│   ├── transforms.py              # Filtering & transformations
│   ├── calculations.py            # Validations & calculations
│   ├── trial_balance.py           # Trial Balance report
│   ├── p_and_l.py                 # P&L reports
│   ├── balance_sheet.py           # Balance Sheet report
│   └── export.py                  # PDF/CSV export
│
├── sample_data/                    # Sample data for testing
│   ├── generate_dummy_data.py     # Data generator script
│   └── *.csv                      # Sample CSV files
│
├── config/                         # Configuration
│   └── account_type_map.csv       # Account type mappings
│
├── sql/                            # SQL query templates (legacy)
│   ├── 01_create_tables.sql
│   ├── 02_trial_balance.sql
│   ├── 03_pnl.sql
│   └── 04_balance_sheet.sql
│
└── docs/                           # Documentation
    ├── QUICKSTART.md              # Quick start guide
    └── DEPLOYMENT.md              # Deployment guide
```

---

## 🔧 Configuration

### Column Name Flexibility

The app automatically detects common column name variations:
- `id` / `account_id` / `subsidiary_id` / `transaction_id`
- `name` / `fullname` / `account_name`
- `accttype` / `accounttype` / `account_type`
- `posting` / `nonposting` / `isnonposting`

### Handling Incomplete Data

The app gracefully handles missing master data:
- Missing accounts show as: `Unknown Account [ID]`
- Missing subsidiaries show as: `Unknown Subsidiary`
- Missing account types show as: `Unknown`

This allows testing with partial/sample data exports.

---

## 📊 Use Cases

### 1. Monthly Financial Close
- Upload current month data
- Filter by period
- Generate all reports
- Download PDFs for review

### 2. Multi-Subsidiary Analysis
- Upload consolidated data
- Filter by specific subsidiaries
- Compare performance
- Export for detailed analysis

### 3. YTD P&L Review
- Upload full year data
- View periodised P&L (monthly tab)
- Track trends and patterns
- Download quarterly summaries

### 4. Department Profitability
- Upload data with department info
- Filter by department
- Generate department P&L
- Compare cost centers

---

## ⚙️ Performance

### Dataset Size Guidelines

| Rows | Processing Time | Recommendation |
|------|-----------------|----------------|
| < 10K | < 5 seconds | ✅ Excellent |
| 10K - 100K | 5-30 seconds | ✅ Good |
| 100K - 500K | 30-90 seconds | ⚠️ Acceptable |
| > 500K | 1-3 minutes | ⚠️ Use filters |

### Optimization Tips

1. **Use Filters** - Period filters significantly improve performance
2. **Limit Display** - Browser shows max 5,000 rows (complete data in CSV)
3. **Upload Period CSV** - Enables efficient period-based filtering
4. **Close Unused Tabs** - Free up browser memory

---

## 🚀 Deployment

### Local Deployment
```bash
streamlit run app.py
```

### Streamlit Cloud (Easiest)
1. Push code to GitHub
2. Connect at [share.streamlit.io](https://share.streamlit.io)
3. Deploy with one click

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment guides including:
- Azure App Service
- AWS EC2
- Kubernetes
- Security considerations

---

## 🔒 Security & Privacy

### Data Privacy
- ✅ All processing happens in browser memory
- ✅ No data sent to external servers
- ✅ No data persistence
- ✅ Session-based only
- ✅ No authentication required (configurable)

### Production Recommendations
- Use HTTPS/SSL certificates
- Add authentication for multi-user deployments
- Implement rate limiting
- Enable audit logging
- Use `.gitignore` to prevent committing real data

---

## 🐛 Troubleshooting

### Common Issues

**"No data available for selected filters"**
- Check that filters aren't too restrictive
- Uncheck "Exclude Non-Posting" if applicable
- Verify subsidiary/period selections

**"Books may be out of balance"**
- Normal for sample/incomplete data
- Check if equity accounts are included
- Verify you're using complete period data

**Slow performance**
- Filter by specific periods
- Check dataset size (should be < 500K rows)
- Close unused browser tabs

**Missing accounts in reports**
- The app handles this gracefully
- Missing accounts show as "Unknown Account [ID]"
- Check that accounts.csv contains all referenced IDs

### Getting Help

1. Check [QUICKSTART.md](QUICKSTART.md) for setup help
2. Review [DEPLOYMENT.md](DEPLOYMENT.md) for deployment issues
3. Try sample data to isolate data vs app issues
4. Check browser console for JavaScript errors

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with:
- [Streamlit](https://streamlit.io/) - Web framework
- [DuckDB](https://duckdb.org/) - In-memory analytics
- [Pandas](https://pandas.pydata.org/) - Data manipulation
- [ReportLab](https://www.reportlab.com/) - PDF generation

---

## 📞 Support

For questions or issues:
1. Check the documentation in `docs/`
2. Review common troubleshooting scenarios above
3. Test with sample data to isolate issues
4. Open an issue on GitHub (if applicable)

---

## 🎯 Roadmap

Potential future enhancements:
- Cash flow statement
- Budget vs actual comparison
- Multi-currency support
- Custom report builder
- Historical trend analysis
- Drill-down capabilities
- Email report automation

---

**Version:** 2.0.0  
**Status:** Production Ready  
**Last Updated:** 2025-11-13

---

*Professional financial reporting made simple* 🚀
