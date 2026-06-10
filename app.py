"""
NetSuite Close Validator
Streamlit app for analysing a flat NetSuite GL transaction detail export.
"""

import streamlit as st

from utils.styles import (
    inject_css, render_topbar, render_footer, section_header,
    stat_chips, empty_state, icon,
)
from utils.load_data import load_flat_csv, validate_columns, build_database
from utils.transforms import render_filter_sidebar, FILTER_KEYS
from utils.calculations import run_data_validations, display_validation_metrics
from utils.trial_balance import generate_trial_balance, display_trial_balance
from utils.p_and_l import generate_pnl, display_pnl, display_periodised_pnl
from utils.balance_sheet import generate_balance_sheet, display_balance_sheet
from utils.close_health import display_close_health

st.set_page_config(
    page_title="NetSuite Close Validator",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="auto",
)

inject_css()

# Landing-only overrides; colour/radius tokens come from the design system
# variables defined in utils/styles.py.
st.markdown("""
<style>
.st-key-demo_dl button {
    width: 100%;
    border: 1px solid var(--accent);
    border-radius: var(--radius);
    padding: 8px 12px;
    background: transparent;
    color: var(--text);
    font-size: 0.85rem;
    font-weight: 500;
    transition: background .15s ease;
}
.st-key-demo_dl button:hover {
    background: var(--accent-bg);
    border-color: var(--accent);
    color: var(--text);
}
/* Match the rendered height of the "What you'll get" card alongside */
.st-key-upload_card { min-height: 474px; }
</style>
""", unsafe_allow_html=True)

render_topbar()

if "uploader_seq" not in st.session_state:
    st.session_state.uploader_seq = 0


def reset_data():
    for key in ("con", "stats", "data_loaded", "file_key", "file_name",
                "failed_key", "fail_msg", *FILTER_KEYS.values()):
        st.session_state.pop(key, None)
    st.session_state.uploader_seq += 1


def process_upload(uploaded_file):
    """Parse, validate, and load the export with a visible progress sequence."""
    file_key = f"{uploaded_file.name}:{uploaded_file.size}"

    if st.session_state.get("failed_key") == file_key:
        st.error(st.session_state.get("fail_msg", "This file could not be processed."))
        return

    try:
        with st.status("Processing export…", expanded=True) as status:
            st.write("Parsing CSV…")
            df = load_flat_csv(uploaded_file)
            if df is None:
                raise ValueError("Could not read the CSV file.")

            st.write("Validating columns…")
            validate_columns(df)

            st.write("Building reports…")
            if len(df) > 500_000:
                st.caption("Large dataset — this may take 1–2 minutes.")
            con, stats = build_database(df)

            status.update(label="Reports ready", state="complete", expanded=False)
    except Exception as e:
        st.session_state.failed_key = file_key
        st.session_state.fail_msg = f"Could not process this file: {e}"
        st.error(st.session_state.fail_msg)
        return

    st.session_state.con = con
    st.session_state.stats = stats
    st.session_state.file_key = file_key
    st.session_state.file_name = uploaded_file.name
    st.session_state.data_loaded = True
    st.rerun()


# ── Landing / upload state ────────────────────────────────────────────────────
if not st.session_state.get("data_loaded", False):
    left, right = st.columns([1.5, 1], gap="large")

    with left:
        with st.container(border=True, key="upload_card"):
            st.markdown(
                '<p class="sc-card-title">Upload GL transaction detail</p>'
                '<p class="sc-card-caption">Drop a flat CSV export below — reports '
                'generate automatically.</p>',
                unsafe_allow_html=True,
            )
            uploaded_file = st.file_uploader(
                "Upload GL transaction detail CSV",
                type=["csv"],
                key=f"gl_csv_{st.session_state.uploader_seq}",
                label_visibility="collapsed",
            )
            st.markdown(
                '<p class="sc-card-caption" style="margin:4px 0 0;">Required columns: '
                '<code>transaction_id</code> · <code>date</code> · <code>period</code> · '
                '<code>account_name</code> · <code>account_type</code> · '
                '<code>subsidiary</code> · <code>debit</code> · <code>credit</code></p>',
                unsafe_allow_html=True,
            )

            with st.expander("How to export from NetSuite"):
                st.markdown("""
**Reports → Saved Searches → Transaction Detail**

Include these columns: `Internal ID` · `Date` · `Posting Period` · `Account` ·
`Account Type` · `Subsidiary` · `Department` · `Debit` · `Credit`

Export as CSV and upload it here. Nothing is stored — all processing runs in
your browser session.
""")

            if uploaded_file is not None:
                process_upload(uploaded_file)

    with right:
        with st.container(border=True, key="benefits_card"):
            st.markdown(
                f"""
                <p class="sc-card-title">What you'll get</p>
                <ul class="sc-report-list">
                  <li><span class="sc-ric">{icon('table')}</span>
                      <span>Trial Balance<small>Net balance by account and subsidiary</small></span></li>
                  <li><span class="sc-ric">{icon('trend')}</span>
                      <span>Profit &amp; Loss<small>Revenue, expenses, and net income</small></span></li>
                  <li><span class="sc-ric">{icon('calendar')}</span>
                      <span>Periodised P&amp;L<small>Monthly, quarterly, and yearly views</small></span></li>
                  <li><span class="sc-ric">{icon('layers')}</span>
                      <span>Balance Sheet<small>Assets, liabilities, and equity</small></span></li>
                  <li><span class="sc-ric">{icon('shield')}</span>
                      <span>Close Health Check<small>Four automated anomaly checks on your GL</small></span></li>
                </ul>
                """,
                unsafe_allow_html=True,
            )

            try:
                with open("sample_data/gl_transactions_demo.csv", "rb") as f:
                    st.download_button(
                        "Download demo file",
                        f,
                        file_name="gl_transactions_demo.csv",
                        mime="text/csv",
                        type="secondary",
                        icon=":material/download:",
                        width="stretch",
                        key="demo_dl",
                    )
                st.caption(
                    "1,987-row sample with four planted errors — upload it to see "
                    "every Close Health check fire."
                )
            except FileNotFoundError:
                pass

# ── Loaded state ──────────────────────────────────────────────────────────────
else:
    con = st.session_state["con"]
    stats = st.session_state["stats"]

    period_range = "—"
    if stats.get("date_min") and stats.get("date_max"):
        period_range = (
            f"{stats['date_min'].strftime('%b %Y')} – {stats['date_max'].strftime('%b %Y')}"
        )

    strip_left, strip_right = st.columns([5, 1.2], vertical_alignment="center")
    with strip_left:
        stat_chips([
            ("File", st.session_state.get("file_name", "—")),
            ("Rows", f"{stats['total_rows']:,}"),
            ("Transactions", f"{stats['transactions']:,}"),
            ("Accounts", f"{stats['accounts']:,}"),
            ("Subsidiaries", f"{stats['subsidiaries']:,}"),
            ("Periods", f"{stats['periods']:,}"),
            ("Range", period_range),
        ])
    with strip_right:
        st.button(
            "Load different file",
            type="tertiary",
            icon=":material/restart_alt:",
            on_click=reset_data,
        )

    filters = render_filter_sidebar(con)

    validations = run_data_validations(con, filters)
    display_validation_metrics(validations)

    tab_tb, tab_pnl, tab_ppnl, tab_bs, tab_health = st.tabs([
        "Trial Balance",
        "Profit & Loss",
        "Periodised P&L",
        "Balance Sheet",
        "Close Health Check",
    ])

    with tab_tb:
        try:
            with st.spinner("Generating Trial Balance…"):
                tb_df = generate_trial_balance(con, filters)
            display_trial_balance(tb_df, filters)
        except Exception as e:
            st.error(f"Trial Balance unavailable: {e}")

    with tab_pnl:
        try:
            with st.spinner("Generating Profit & Loss…"):
                pnl_df = generate_pnl(con, filters)
            display_pnl(pnl_df, filters)
        except Exception as e:
            st.error(f"Profit & Loss unavailable: {e}")

    with tab_ppnl:
        try:
            with st.spinner("Generating Periodised P&L…"):
                display_periodised_pnl(con, filters)
        except Exception as e:
            st.error(f"Periodised P&L unavailable: {e}")

    with tab_bs:
        try:
            with st.spinner("Generating Balance Sheet…"):
                bs_df = generate_balance_sheet(con, filters)
            display_balance_sheet(bs_df, filters)
        except Exception as e:
            st.error(f"Balance Sheet unavailable: {e}")

    with tab_health:
        try:
            display_close_health(con)
        except Exception as e:
            st.error(f"Close Health Check unavailable: {e}")

render_footer()
