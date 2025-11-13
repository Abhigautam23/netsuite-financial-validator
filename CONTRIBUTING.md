# Contributing to NetSuite Financial Reporting MVP

Thank you for considering contributing to this project! This document provides guidelines for developers.

---

## 🏗️ Development Setup

### Prerequisites
- Python 3.9+
- Git
- Virtual environment tool

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd netsuite_data

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install pylint black pytest
```

---

## 📁 Project Structure

```
netsuite_data/
├── app.py                    # Main Streamlit application
├── utils/                    # Modular utilities
│   ├── load_data.py         # Data loading & normalization
│   ├── transforms.py        # Filtering & transformations
│   ├── calculations.py      # Validations & calculations
│   ├── trial_balance.py     # Trial Balance report
│   ├── p_and_l.py           # P&L reports
│   ├── balance_sheet.py     # Balance Sheet report
│   └── export.py            # PDF/CSV export
├── sample_data/             # Sample test data
├── config/                  # Configuration files
└── docs/                    # Documentation
```

---

## 🔧 Code Guidelines

### Python Style
- Follow PEP 8 style guide
- Use meaningful variable names
- Add docstrings to all functions
- Keep functions focused and small

### Example Function Structure
```python
def function_name(param1, param2):
    """
    Brief description of what the function does
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
    """
    # Implementation
    return result
```

### SQL Guidelines
- Use meaningful table aliases
- Format multi-line queries for readability
- Add comments for complex logic
- Use LEFT JOIN for optional relationships

---

## 🧪 Testing

### Manual Testing
1. Test with sample data in `sample_data/`
2. Test with various filter combinations
3. Verify PDF and CSV exports work
4. Check data validations are accurate

### Test Cases to Cover
- Empty files
- Missing columns
- NULL values
- Large datasets (> 100K rows)
- Filter edge cases
- Missing master data (accounts, subsidiaries)

---

## 📝 Making Changes

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes
- Keep commits focused and atomic
- Write clear commit messages
- Test thoroughly

### 3. Update Documentation
- Update README.md if adding features
- Add comments to complex code
- Update QUICKSTART.md if changing user flow

### 4. Test Your Changes
```bash
# Run the app
streamlit run app.py

# Test with sample data
# Test with filters
# Test exports
```

### 5. Submit Pull Request
- Clear description of changes
- Reference any related issues
- Include screenshots if UI changes

---

## 🐛 Reporting Bugs

### Bug Report Template
```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Upload files '...'
2. Apply filters '...'
3. Click on '...'
4. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g. Windows 10]
- Python Version: [e.g. 3.9.7]
- Browser: [e.g. Chrome 95]

**Additional context**
Any other context about the problem.
```

---

## 💡 Feature Requests

We welcome feature suggestions! Please provide:
1. Clear description of the feature
2. Use case / problem it solves
3. Proposed implementation (if you have ideas)
4. Any relevant examples or mockups

---

## 🔄 Development Workflow

### Adding a New Report

1. **Create utility module** in `utils/`
```python
# utils/new_report.py
def generate_new_report(con, filters):
    """Generate new report"""
    # Implementation
    pass

def display_new_report(df):
    """Display new report in Streamlit"""
    # Implementation
    pass
```

2. **Import in app.py**
```python
from utils.new_report import generate_new_report, display_new_report
```

3. **Add new tab**
```python
with tab_new:
    df = generate_new_report(con, filters)
    display_new_report(df)
```

### Adding a New Filter

1. **Update `get_available_filters()` in `utils/transforms.py`**
2. **Add UI in `render_filter_sidebar()` in `utils/transforms.py`**
3. **Update `build_filter_where_clause()` to use new filter**
4. **Test with various filter combinations**

---

## 📊 Performance Considerations

### Optimization Guidelines
- Use `@st.cache_data` for expensive operations
- Limit DataFrame operations in loops
- Use DuckDB for aggregations (not Pandas)
- Profile with large datasets before merging

### DuckDB Best Practices
- Use LEFT JOIN for optional relationships
- Add WHERE clauses early in query
- Use COALESCE for NULL handling
- Cast types explicitly with TRY_CAST

---

## 🔒 Security Considerations

### Data Handling
- Never commit real client data
- Use `.gitignore` properly
- No hardcoded credentials
- Validate all user inputs

### SQL Injection Prevention
- Use parameterized queries
- Validate column names before using in f-strings
- Don't concatenate user input directly into SQL

---

## 📚 Resources

### Streamlit
- [Streamlit Docs](https://docs.streamlit.io/)
- [Streamlit API Reference](https://docs.streamlit.io/library/api-reference)

### DuckDB
- [DuckDB Docs](https://duckdb.org/docs/)
- [DuckDB SQL Reference](https://duckdb.org/docs/sql/introduction)

### Python
- [PEP 8 Style Guide](https://pep8.org/)
- [Python Docs](https://docs.python.org/3/)

---

## 🤝 Code Review Process

### What We Look For
- ✅ Code follows style guidelines
- ✅ Functions have docstrings
- ✅ Changes are tested
- ✅ Documentation is updated
- ✅ No hardcoded values
- ✅ Error handling is present
- ✅ Performance is acceptable

### Review Checklist
- [ ] Code is clean and readable
- [ ] Tests pass with sample data
- [ ] Documentation is updated
- [ ] No linting errors
- [ ] No security issues
- [ ] Performance is acceptable

---

## 📞 Getting Help

- Check existing issues on GitHub
- Review documentation in `docs/`
- Test with sample data first
- Ask questions in discussions

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing!** 🙏

