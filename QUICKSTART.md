# 🚀 Quick Start Guide

Get up and running with NetSuite Financial Reporting in 5 minutes.

---

## Step 1: Installation (2 minutes)

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Install

```bash
# Navigate to project directory
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

---

## Step 2: Run the App (30 seconds)

```bash
streamlit run app.py
```

Your browser will automatically open to `http://localhost:8501`

---

## Step 3: Upload CSV Files (1 minute)

### Option A: Use Sample Data (Recommended First)

Upload these files from the `sample_data/` folder:
1. account.csv
2. subsidiary.csv
3. transaction.csv
4. transactionline.csv
5. transactionaccountingline.csv

### Option B: Use Your NetSuite Data

Export and upload these files from NetSuite:
1. **account.csv** - Chart of accounts
2. **subsidiary.csv** - Subsidiaries
3. **transaction.csv** - Transaction headers
4. **transactionline.csv** - Transaction lines
5. **transactionaccountingline.csv** - Accounting entries

# In order to use the original data refresh the browser and start again

## Step 4: Generate Reports (30 seconds)

1. Click **"🚀 Generate Reports"** button
2. Wait for processing (5-10 seconds for sample data)
3. View reports in tabs:
   - Trial Balance
   - Profit & Loss
   - Periodised P&L
   - Balance Sheet

---

## Step 5: Apply Filters (Optional)

Use the sidebar to filter by:
- **Subsidiaries** - Select specific entities
- **Periods** - Filter by accounting period
- **Departments** - Filter by department
- **Account Types** - Filter by account classification
- **Non-Posting** - Checkbox to exclude non-posting transactions

---

## Step 6: Download Reports

- **CSV** - Click CSV download button for complete data
- **PDF** - Click PDF button for formatted report

---

## ✅ Success Checklist

After completing the quick start, you should see:
- [x] App running in browser
- [x] All 5 CSV files uploaded successfully
- [x] Data quality metrics displayed
- [x] All 4 report tabs populated with data
- [x] Download buttons working
- [x] Filters in sidebar functional

---

## 🆘 Troubleshooting

### App Won't Start
```bash
# Check Python version (needs 3.9+)
python --version

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Upload Errors
- Check CSV files have correct column names
- Ensure files are UTF-8 encoded
- Try sample data first to verify app works

### No Data Showing
- Check that you clicked "Generate Reports"
- Verify all 5 required files are uploaded
- Try unchecking "Exclude Non-Posting" filter

### Performance Issues
- Normal for datasets > 100K rows (takes 30-60 seconds)
- Use period filters to improve performance
- Close unused browser tabs

---

## 🎓 Next Steps

### 1. Explore Features
- Try different filter combinations
- View periodised P&L reports
- Download CSV and open in Excel

### 2. Use Your Own Data
- Export CSV files from NetSuite
- Upload and generate reports
- Compare with NetSuite reports for validation

### 3. Deploy to Production
- See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment options
- Configure HTTPS and authentication if needed
- Share URL with your team

---

## 📚 Additional Resources

- **README.md** - Complete documentation
- **DEPLOYMENT.md** - Deployment guides
- **Sample Data** - Test data in `sample_data/` folder
- **Config** - Account type mappings in `config/` folder

---

## 🎉 You're Ready!

That's it! You now have a fully functional NetSuite financial reporting tool.

**Questions?** Check the main [README.md](README.md) or troubleshooting section above.

---

**Happy Reporting!** 📊✨
