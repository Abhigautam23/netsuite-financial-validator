"""
Close Health Check
Scorecard of four targeted GL anomaly checks plus overall balance metrics.
Each check renders independently — one failure cannot block the others.
"""

import streamlit as st

from utils.styles import (
    DANGER, section_header, pill, icon, stat_chips, pass_note, empty_state,
)
from utils.validation_checks import (
    check_period_balance_errors,
    check_volume_anomalies,
    check_duplicate_postings,
    check_missing_accrual_reversals,
)

# severity: how serious findings from this check are when present.
# 'high' → "Action required" (red); 'low' → "Review" (amber).
CHECK_DEFS = [
    {
        "key": "period_balance",
        "label": "Period Balance",
        "icon": "balance",
        "severity": "high",
        "noun": "period",
        "fn": check_period_balance_errors,
        "filename": "period_balance_errors.csv",
        "caption": (
            "Every closed period must net to zero (debits = credits). "
            "A non-zero variance indicates a missing posting or data-export issue."
        ),
        "clean": "All periods balance.",
        "blurb": "Debits must equal credits per period",
    },
    {
        "key": "volume_anomalies",
        "label": "Volume Anomalies",
        "icon": "activity",
        "severity": "low",
        "noun": "period",
        "fn": check_volume_anomalies,
        "filename": "volume_anomalies.csv",
        "caption": (
            "Periods more than 2 standard deviations above the mean transaction count "
            "or posting volume. High z-scores often indicate a duplicate batch import."
        ),
        "clean": "No unusual posting volumes detected.",
        "blurb": "z-score &gt; 2σ above mean volume",
    },
    {
        "key": "duplicate_postings",
        "label": "Duplicate Postings",
        "icon": "copy",
        "severity": "high",
        "noun": "duplicate line",
        "fn": check_duplicate_postings,
        "filename": "duplicate_postings.csv",
        "caption": (
            "Lines that share the same date, account, subsidiary, and amount across "
            "two or more distinct transaction IDs. Likely a double-posted journal "
            "entry or batch import error."
        ),
        "clean": "No duplicate postings detected.",
        "blurb": "Same date · account · amount · two distinct IDs",
    },
    {
        "key": "accrual_reversals",
        "label": "Accrual Reversals",
        "icon": "rotate",
        "severity": "low",
        "noun": "accrual",
        "fn": check_missing_accrual_reversals,
        "filename": "missing_accrual_reversals.csv",
        "caption": (
            "Accrual accounts with a net balance in period N but no offsetting entry "
            "in period N+1. Standard practice requires accruals to be reversed at the "
            "start of the following period."
        ),
        "clean": "All accruals appear to be reversed.",
        "blurb": "Expected reversal not found in following period",
    },
]

_STATUS_PILL = {
    "pass":    ("Pass", "pass"),
    "review":  ("Review", "warn"),
    "action":  ("Action required", "fail"),
    "unavail": ("Unavailable", "muted"),
}

_CHECK_COLUMN_CONFIG = {
    "period":           st.column_config.TextColumn("Period"),
    "account_name":     st.column_config.TextColumn("Account"),
    "subsidiary":       st.column_config.TextColumn("Subsidiary"),
    "date":             st.column_config.DatetimeColumn("Date", format="YYYY-MM-DD"),
    "transaction_ids":  st.column_config.TextColumn("Transaction IDs"),
    "total_debits":     st.column_config.NumberColumn("Total Debits", format="accounting"),
    "total_credits":    st.column_config.NumberColumn("Total Credits", format="accounting"),
    "variance":         st.column_config.NumberColumn("Variance", format="accounting"),
    "net_amount":       st.column_config.NumberColumn("Net Amount", format="accounting"),
    "debit":            st.column_config.NumberColumn("Debit", format="accounting"),
    "credit":           st.column_config.NumberColumn("Credit", format="accounting"),
    "total_volume":     st.column_config.NumberColumn("Total Volume", format="accounting"),
    "txn_count":        st.column_config.NumberColumn("Transactions", format="localized"),
    "num_transactions": st.column_config.NumberColumn("Times Posted", format="localized"),
    "count_z_score":    st.column_config.NumberColumn("Count z-score", format="%.2f"),
    "volume_z_score":   st.column_config.NumberColumn("Volume z-score", format="%.2f"),
}

# Columns whose values are flagged in red when materially non-zero.
_VARIANCE_COLUMNS = {"variance", "net_amount"}


def _run_check(fn, con):
    """Run a check function; return (dataframe, error_message)."""
    try:
        df = fn(con)
        return df, None
    except Exception as e:
        return None, str(e)


def _overall_balance(con):
    try:
        row = con.execute("""
            SELECT
                ROUND(SUM(debit),  2),
                ROUND(SUM(credit), 2),
                ROUND(SUM(debit) - SUM(credit), 2)
            FROM gl_transactions
        """).fetchone()
        return row[0] or 0.0, row[1] or 0.0, row[2] or 0.0
    except Exception:
        return 0.0, 0.0, 0.0


def _missing_data(con):
    try:
        return con.execute("""
            SELECT
                COUNT(*) FILTER (WHERE account_name IS NULL OR account_name = '') AS missing_account,
                COUNT(*) FILTER (WHERE subsidiary   IS NULL OR subsidiary   = '') AS missing_subsidiary,
                COUNT(*) FILTER (WHERE period       IS NULL OR period       = '') AS missing_period,
                COUNT(*) FILTER (WHERE date         IS NULL)                      AS missing_date
            FROM gl_transactions
        """).fetchone()
    except Exception:
        return (0, 0, 0, 0)


def _check_status(count, err, severity):
    if err:
        return "unavail"
    if count == 0:
        return "pass"
    return "action" if severity == "high" else "review"


def _findings_text(count, noun):
    if count == 0:
        return "No findings"
    return f"{count} {noun}{'s' if count != 1 else ''} flagged"


def _check_table(df):
    """Render a check detail table with formatted, right-aligned numerics and
    colour-coded variance values."""
    styled = df.style
    for col in _VARIANCE_COLUMNS & set(df.columns):
        styled = styled.map(
            lambda v: f"color: {DANGER}; font-weight: 600;"
            if isinstance(v, (int, float)) and abs(v) > 0.01 else "",
            subset=[col],
        )
    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        column_config={k: v for k, v in _CHECK_COLUMN_CONFIG.items() if k in df.columns},
    )


def display_close_health(con):
    if con is None:
        empty_state("No data loaded", "Upload a GL export to run the Close Health Check.")
        return

    section_header(
        "Close Health Check",
        "Four automated checks run against your GL export. "
        "Click a card or expand a section to review the flagged rows.",
    )

    with st.spinner("Running close health checks…"):
        results = []
        for check in CHECK_DEFS:
            df, err = _run_check(check["fn"], con)
            count = 0 if (err or df is None) else len(df)
            results.append({
                **check,
                "df": df,
                "err": err,
                "count": count,
                "status": _check_status(count, err, check["severity"]),
            })

    # ── Health score summary ────────────────────────────────────────────────
    passed = sum(1 for r in results if r["status"] == "pass")
    n_action = sum(1 for r in results if r["status"] == "action")
    n_review = sum(1 for r in results if r["status"] == "review")

    if n_action:
        overall = pill("Action required", "fail")
    elif n_review:
        overall = pill("Review", "warn")
    elif passed == len(results):
        overall = pill("All clear", "pass")
    else:
        overall = pill("Partially unavailable", "muted")

    detail_bits = []
    if n_action:
        detail_bits.append(f"{n_action} need{'s' if n_action == 1 else ''} action")
    if n_review:
        detail_bits.append(f"{n_review} to review")
    detail = f' · {" · ".join(detail_bits)}' if detail_bits else ""

    st.markdown(
        f'<div class="sc-score">{overall}'
        f'<span class="sc-score-text">{passed} of {len(results)} checks passed</span>'
        f'<span class="sc-score-sub">{detail}</span></div>',
        unsafe_allow_html=True,
    )

    # ── Check cards (linked to detail sections below) ───────────────────────
    cols = st.columns(len(results))
    for col, r in zip(cols, results):
        label, kind = _STATUS_PILL[r["status"]]
        count_text = "Check unavailable" if r["err"] else _findings_text(r["count"], r["noun"])
        col.markdown(
            f"""
            <a class="sc-check-card" href="#check-{r['key']}">
              <div class="sc-check-head">{icon(r['icon'], 16)}{pill(label, kind)}</div>
              <div class="sc-check-name">{r['label']}</div>
              <div class="sc-check-count">{count_text}</div>
              <div class="sc-check-desc">{r['blurb']}</div>
            </a>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")

    # ── Detail sections ─────────────────────────────────────────────────────
    for r in results:
        st.markdown(
            f'<div class="sc-anchor" id="check-{r["key"]}"></div>',
            unsafe_allow_html=True,
        )
        title = f"{r['label']} — {'unavailable' if r['err'] else _findings_text(r['count'], r['noun']).lower()}"
        with st.expander(title, expanded=r["count"] > 0):
            st.caption(r["caption"])
            if r["err"]:
                st.warning(f"Check unavailable: {r['err']}")
            elif r["df"] is None or r["df"].empty:
                pass_note(r["clean"])
            else:
                _check_table(r["df"])
                st.download_button(
                    "Download CSV",
                    r["df"].to_csv(index=False).encode(),
                    r["filename"],
                    "text/csv",
                    type="tertiary",
                    icon=":material/download:",
                    key=f"dl_{r['key']}",
                )

    st.markdown("")

    # ── Ledger balance ──────────────────────────────────────────────────────
    section_header("Ledger Balance")
    total_debits, total_credits, variance = _overall_balance(con)

    if abs(variance) < 0.01:
        var_kind, var_pill = "ok", pill("Balanced", "pass")
    elif abs(variance) < 100:
        var_kind, var_pill = "warn", pill("Minor variance", "warn")
    else:
        var_kind, var_pill = "bad", pill("Out of balance", "fail")

    bal_left, bal_right = st.columns([5, 1], vertical_alignment="center")
    with bal_left:
        stat_chips([
            ("Total debits", f"${total_debits:,.2f}"),
            ("Total credits", f"${total_credits:,.2f}"),
            ("Variance", f"${variance:,.2f}", var_kind),
        ])
    with bal_right:
        st.markdown(var_pill, unsafe_allow_html=True)

    st.markdown("")

    # ── Data completeness ───────────────────────────────────────────────────
    section_header("Data Completeness")
    m = _missing_data(con)
    stat_chips([
        ("Missing account", f"{m[0]:,}", "bad" if m[0] else "ok"),
        ("Missing subsidiary", f"{m[1]:,}", "bad" if m[1] else "ok"),
        ("Missing period", f"{m[2]:,}", "bad" if m[2] else "ok"),
        ("Missing date", f"{m[3]:,}", "bad" if m[3] else "ok"),
    ])
    if not any(m):
        st.caption("No missing fields detected across the export.")
