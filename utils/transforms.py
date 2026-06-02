"""
Data Transformation and Filtering Functions
Handles filtering by period, subsidiary, department, and account type
"""

import streamlit as st


def build_filter_where_clause(filters):
    """Build SQL WHERE clause from filters. Column refs target the 'gl' alias."""
    conditions = []

    if filters.get('subsidiaries'):
        vals = ', '.join([f"'{s}'" for s in filters['subsidiaries']])
        conditions.append(f"gl.subsidiary IN ({vals})")

    if filters.get('periods'):
        vals = ', '.join([f"'{p}'" for p in filters['periods']])
        conditions.append(f"gl.period IN ({vals})")

    if filters.get('departments'):
        vals = ', '.join([f"'{d}'" for d in filters['departments']])
        conditions.append(f"gl.department IN ({vals})")

    if filters.get('account_types'):
        vals = ', '.join([f"'{at}'" for at in filters['account_types']])
        conditions.append(f"gl.account_type IN ({vals})")

    return ("WHERE " + " AND ".join(conditions)) if conditions else ""


def get_base_query_with_filters(filters):
    """
    Return a SQL SELECT over gl_transactions with filters applied.
    Column aliases match what all downstream report queries expect.
    """
    where_clause = build_filter_where_clause(filters)

    return f"""
        SELECT
            gl.subsidiary                   AS subsidiary_name,
            gl.account_name                 AS account_name,
            gl.account_type                 AS account_type,
            gl.period                       AS period_name,
            YEAR(gl.date)                   AS fiscal_year,
            QUARTER(gl.date)                AS fiscal_quarter,
            MONTH(gl.date)                  AS fiscal_month,
            gl.date                         AS transaction_date,
            gl.department                   AS department_id,
            gl.amount                       AS amount
        FROM gl_transactions gl
        {where_clause}
    """


@st.cache_data(ttl=300)
def get_available_filters(_con):
    """Query distinct filter values from gl_transactions."""
    result = {}

    try:
        rows = _con.execute(
            "SELECT DISTINCT subsidiary FROM gl_transactions WHERE subsidiary IS NOT NULL ORDER BY subsidiary"
        ).fetchall()
        result['subsidiaries'] = [r[0] for r in rows]
    except Exception:
        result['subsidiaries'] = []

    try:
        rows = _con.execute(
            "SELECT DISTINCT period FROM gl_transactions WHERE period IS NOT NULL ORDER BY period"
        ).fetchall()
        result['periods'] = [r[0] for r in rows]
    except Exception:
        result['periods'] = []

    try:
        rows = _con.execute(
            "SELECT DISTINCT department FROM gl_transactions WHERE department IS NOT NULL AND department <> '' ORDER BY department"
        ).fetchall()
        result['departments'] = [r[0] for r in rows]
    except Exception:
        result['departments'] = []

    try:
        rows = _con.execute(
            "SELECT DISTINCT account_type FROM gl_transactions WHERE account_type IS NOT NULL ORDER BY account_type"
        ).fetchall()
        result['account_types'] = [r[0] for r in rows]
    except Exception:
        result['account_types'] = []

    return result


def render_filter_sidebar(_con):
    """Render sidebar filters and return selected values."""
    st.sidebar.header("🔍 Filters")

    available = get_available_filters(_con)
    selected = {}

    st.sidebar.markdown("### Filter By:")

    if available['subsidiaries']:
        selected['subsidiaries'] = st.sidebar.multiselect(
            "Subsidiaries",
            options=available['subsidiaries'],
            default=None,
            help="Leave empty to include all subsidiaries."
        )
    else:
        selected['subsidiaries'] = []

    if available['periods']:
        selected['periods'] = st.sidebar.multiselect(
            "Periods",
            options=available['periods'],
            default=None,
            help="Leave empty to include all periods."
        )
    else:
        selected['periods'] = []

    if available['departments']:
        selected['departments'] = st.sidebar.multiselect(
            "Departments",
            options=available['departments'],
            default=None,
            help="Leave empty to include all departments."
        )
    else:
        selected['departments'] = []

    if available['account_types']:
        selected['account_types'] = st.sidebar.multiselect(
            "Account Types",
            options=available['account_types'],
            default=None,
            help="Leave empty to include all account types."
        )
    else:
        selected['account_types'] = []

    active = sum(1 for k in ('subsidiaries', 'periods', 'departments', 'account_types') if selected.get(k))
    if active:
        st.sidebar.success(f"✅ {active} filter(s) active")
    else:
        st.sidebar.info("ℹ️ No filters applied (showing all data)")

    return selected
