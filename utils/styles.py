"""
Design system for NetSuite Close Validator.

Single source of truth for colours, spacing, typography, and reusable UI
fragments. No other module should contain raw hex values or ad-hoc CSS.
"""

import html
from string import Template

import streamlit as st

# ── Palette ───────────────────────────────────────────────────────────────────
BG            = "#0B0F17"
SURFACE       = "#121826"
SURFACE_2     = "#192133"
BORDER        = "#222C3F"
BORDER_STRONG = "#31405C"

ACCENT     = "#5B8DEF"
ACCENT_BG  = "rgba(91, 141, 239, 0.10)"

TEXT       = "#E7ECF4"
TEXT_MUTED = "#94A0B5"
TEXT_FAINT = "#5C6878"

SUCCESS    = "#46A580"
SUCCESS_BG = "rgba(70, 165, 128, 0.12)"
WARNING    = "#D9A03F"
WARNING_BG = "rgba(217, 160, 63, 0.12)"
DANGER     = "#D65A5E"
DANGER_BG  = "rgba(214, 90, 94, 0.12)"

# ── Icons (feather-style inline SVG, stroke = currentColor) ──────────────────
_ICON_PATHS = {
    "balance":   '<line x1="5" y1="9" x2="19" y2="9"/><line x1="5" y1="15" x2="19" y2="15"/>',
    "activity":  '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "copy":      '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
    "rotate":    '<polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>',
    "table":     '<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="9" x2="9" y2="21"/>',
    "trend":     '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
    "calendar":  '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
    "layers":    '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    "shield":    '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "lock":      '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "inbox":     '<polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>',
    "check":     '<polyline points="20 6 9 17 4 12"/>',
}


def icon(name, size=14):
    """Return an inline SVG icon string for use inside HTML fragments."""
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round" style="vertical-align:-2px;">{_ICON_PATHS[name]}</svg>'
    )


# NetSuite internal account-type codes → human-readable display labels.
# Display layer only — filters and queries keep the raw codes.
ACCOUNT_TYPE_LABELS = {
    "Bank":          "Bank",
    "AcctRec":       "Accounts Receivable",
    "OthCurrAsset":  "Other Current Asset",
    "FixedAsset":    "Fixed Asset",
    "OthAsset":      "Other Asset",
    "AcctPay":       "Accounts Payable",
    "CredCard":      "Credit Card",
    "OthCurrLiab":   "Other Current Liability",
    "LongTermLiab":  "Long-Term Liability",
    "Equity":        "Equity",
    "Income":        "Income",
    "OthIncome":     "Other Income",
    "Expense":       "Expense",
    "COGS":          "COGS",
    "OthExpense":    "Other Expense",
    "DeferExpense":  "Deferred Expense",
    "DeferRevenue":  "Deferred Revenue",
    "UnbilledRec":   "Unbilled Receivable",
    "Stat":          "Statistical",
}


def humanize_account_types(df, column="account_type"):
    """Return a display copy of df with account-type codes mapped to labels."""
    if column not in df.columns:
        return df
    out = df.copy()
    out[column] = out[column].map(ACCOUNT_TYPE_LABELS).fillna(out[column])
    return out


def fmt_money(v):
    """Accounting-style currency: negatives in parentheses."""
    if v < 0:
        return f"(${abs(v):,.2f})"
    return f"${v:,.2f}"


# ── Stylesheet ────────────────────────────────────────────────────────────────
_CSS = Template("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg: $bg;
    --surface: $surface;
    --border: $border;
    --border-strong: $border_strong;
    --accent: $accent;
    --accent-bg: $accent_bg;
    --text: $text;
    --muted: $muted;
    --faint: $faint;
    --success: $success;       --success-bg: $success_bg;
    --warning: $warning;       --warning-bg: $warning_bg;
    --danger: $danger;         --danger-bg: $danger_bg;
    --sp-1: 4px;  --sp-2: 8px;  --sp-3: 12px;  --sp-4: 16px;  --sp-6: 24px;
    --radius: 10px;  --radius-sm: 6px;
    --fs-h1: 0.95rem;          /* app name in top bar          */
    --fs-section: 1rem;        /* section / report titles      */
    --fs-body: 0.875rem;       /* default body                 */
    --fs-caption: 0.78rem;     /* captions, hints, chip labels */
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
                 'Helvetica Neue', Arial, sans-serif;
}

/* ── Streamlit chrome ───────────────────────────────────────────────────── */
#MainMenu, footer { visibility: hidden; }
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stMainMenu"] { display: none; }
header[data-testid="stHeader"] { background: transparent; }

.block-container { padding-top: 1.1rem; padding-bottom: 2.5rem; max-width: 1280px; }

/* ── Top bar ────────────────────────────────────────────────────────────── */
.sc-topbar {
    display: flex; justify-content: space-between; align-items: center;
    padding: var(--sp-2) 0 var(--sp-3);
    border-bottom: 1px solid var(--border);
    margin-bottom: var(--sp-4);
}
.sc-brand { display: flex; align-items: center; gap: 10px; }
.sc-brand-mark {
    width: 26px; height: 26px; border-radius: var(--radius-sm);
    background: var(--accent-bg); color: var(--accent);
    display: inline-flex; align-items: center; justify-content: center;
}
.sc-brand-name { font-size: var(--fs-h1); font-weight: 600; color: var(--text); letter-spacing: -0.01em; }
.sc-trust {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: var(--fs-caption); color: var(--muted);
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 999px; padding: 4px 12px;
}

/* ── Section headers ────────────────────────────────────────────────────── */
/* Doubled class selectors out-specify Streamlit's stMarkdownContainer p rule */
.sc-section { margin: var(--sp-1) 0 var(--sp-3); }
p.sc-section-title.sc-section-title { font-size: var(--fs-section); font-weight: 600; color: var(--text); margin: 0; }
p.sc-section-caption.sc-section-caption { font-size: var(--fs-caption); color: var(--muted); margin: 2px 0 0; line-height: 1.5; }

/* Inline code chips — keep them on the design system, not Streamlit green */
[data-testid="stMarkdownContainer"] code {
    color: var(--muted);
    background: var(--accent-bg);
    border: 1px solid var(--border);
    border-radius: 4px;
    font-size: 0.72rem;
    padding: 1px 5px;
}

/* ── Cards ──────────────────────────────────────────────────────────────── */
.sc-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: var(--sp-4);
}
p.sc-card-title.sc-card-title { font-size: var(--fs-body); font-weight: 600; color: var(--text); margin: 0 0 var(--sp-1); }
p.sc-card-caption.sc-card-caption { font-size: var(--fs-caption); color: var(--muted); margin: 0 0 var(--sp-3); line-height: 1.5; }

[data-testid="stVerticalBlockBorderWrapper"] { background: var(--surface); border-radius: var(--radius); }

/* ── Report list (landing right column) ─────────────────────────────────── */
.sc-report-list { list-style: none; margin: 0; padding: 0; }
.sc-report-list li {
    display: flex; align-items: flex-start; gap: 10px;
    padding: var(--sp-2) 0; font-size: var(--fs-body); color: var(--text);
}
.sc-report-list li + li { border-top: 1px solid var(--border); }
.sc-report-list .sc-ric { color: var(--accent); margin-top: 1px; }
.sc-report-list small { display: block; color: var(--muted); font-size: var(--fs-caption); margin-top: 1px; }

/* ── File uploader dropzone ─────────────────────────────────────────────── */
[data-testid="stFileUploaderDropzone"] {
    background: rgba(91, 141, 239, 0.03);
    border: 1.5px dashed var(--border-strong);
    border-radius: var(--radius);
    padding: var(--sp-6) var(--sp-4);
    transition: border-color .15s ease, background .15s ease;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--accent);
    background: var(--accent-bg);
}

/* ── Stat chips ─────────────────────────────────────────────────────────── */
.sc-chips { display: flex; flex-wrap: wrap; gap: var(--sp-2); align-items: center; }
.sc-chip {
    display: inline-flex; align-items: baseline; gap: 7px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-sm); padding: 5px 11px; white-space: nowrap;
}
.sc-chip-label {
    font-size: 0.68rem; font-weight: 500; text-transform: uppercase;
    letter-spacing: 0.05em; color: var(--faint);
}
.sc-chip-value { font-size: 0.82rem; font-weight: 600; color: var(--text); font-variant-numeric: tabular-nums; }
.sc-chip-value.ok   { color: var(--success); }
.sc-chip-value.warn { color: var(--warning); }
.sc-chip-value.bad  { color: var(--danger); }

/* ── Status pills ───────────────────────────────────────────────────────── */
.sc-pill {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.02em;
    padding: 3px 10px; border-radius: 999px; white-space: nowrap;
}
.sc-pill-pass  { color: var(--success); background: var(--success-bg); border: 1px solid var(--success); }
.sc-pill-warn  { color: var(--warning); background: var(--warning-bg); border: 1px solid var(--warning); }
.sc-pill-fail  { color: var(--danger);  background: var(--danger-bg);  border: 1px solid var(--danger); }
.sc-pill-muted { color: var(--muted);   background: var(--surface);    border: 1px solid var(--border); }

/* ── Close-health check cards ───────────────────────────────────────────── */
a.sc-check-card, a.sc-check-card:visited {
    display: block; height: 100%;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: var(--sp-3) var(--sp-4);
    text-decoration: none !important;
    transition: border-color .15s ease;
}
a.sc-check-card:hover { border-color: var(--accent); }
.sc-check-head {
    display: flex; justify-content: space-between; align-items: center;
    color: var(--muted); margin-bottom: var(--sp-2);
}
.sc-check-name { font-size: 0.85rem; font-weight: 600; color: var(--text); }
.sc-check-count { font-size: var(--fs-caption); color: var(--muted); margin-top: 2px; }
.sc-check-desc {
    font-size: 0.72rem; color: var(--faint); line-height: 1.4;
    border-top: 1px solid var(--border);
    margin-top: var(--sp-2); padding-top: var(--sp-2);
}

.sc-anchor { scroll-margin-top: 80px; }

/* ── Health score line ──────────────────────────────────────────────────── */
.sc-score {
    display: flex; align-items: center; gap: var(--sp-3);
    margin: var(--sp-2) 0 var(--sp-3);
}
.sc-score-text { font-size: 0.95rem; font-weight: 600; color: var(--text); }
.sc-score-sub  { font-size: var(--fs-caption); color: var(--muted); }

/* ── Toolbar above tables ───────────────────────────────────────────────── */
p.sc-toolbar-caption.sc-toolbar-caption { font-size: var(--fs-caption); color: var(--muted); margin: 0; padding-top: 6px; }

/* ── Total rows under tables ────────────────────────────────────────────── */
.sc-total-row {
    display: flex; flex-wrap: wrap; gap: var(--sp-6);
    border-top: 2px solid var(--border-strong);
    margin-top: var(--sp-1); padding: var(--sp-2) var(--sp-1) 0;
}
.sc-total-item { display: flex; align-items: baseline; gap: 8px; }
.sc-total-label { font-size: var(--fs-caption); color: var(--muted); }
.sc-total-value { font-size: 0.875rem; font-weight: 700; color: var(--text); font-variant-numeric: tabular-nums; }
.sc-total-value.ok  { color: var(--success); }
.sc-total-value.bad { color: var(--danger); }

/* ── Empty state ────────────────────────────────────────────────────────── */
.sc-empty {
    text-align: center; padding: 40px var(--sp-4);
    background: var(--surface); border: 1px dashed var(--border-strong);
    border-radius: var(--radius); color: var(--muted); margin: var(--sp-2) 0;
}
.sc-empty-icon { color: var(--faint); margin-bottom: var(--sp-2); }
.sc-empty-title { font-size: var(--fs-body); font-weight: 600; color: var(--text); margin: 0; }
.sc-empty-hint { font-size: var(--fs-caption); color: var(--muted); margin: var(--sp-1) 0 0; }

/* ── Inline pass note (clean check detail) ──────────────────────────────── */
.sc-pass-note {
    display: inline-flex; align-items: center; gap: 7px;
    font-size: var(--fs-body); color: var(--success); padding: var(--sp-1) 0;
}

/* ── Sidebar ────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] { border-right: 1px solid var(--border); }
.sc-side-title {
    display: flex; align-items: center; gap: 8px;
    font-size: 0.72rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.07em; color: var(--muted); margin: 0 0 var(--sp-1);
}
.sc-filter-badge {
    background: var(--accent); color: #fff; font-size: 0.66rem; font-weight: 700;
    border-radius: 999px; padding: 1px 7px; letter-spacing: 0;
}

/* ── Tabs ───────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { gap: var(--sp-6); border-bottom: 1px solid var(--border); }
.stTabs [data-baseweb="tab"] { font-size: 0.85rem; padding: var(--sp-2) var(--sp-1); }

/* ── Expanders ──────────────────────────────────────────────────────────── */
[data-testid="stExpander"] details {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
}
[data-testid="stExpander"] summary { font-size: var(--fs-body); font-weight: 500; }

/* ── Tertiary buttons (toolbars, ghost actions) ─────────────────────────── */
[data-testid="stBaseButton-tertiary"] {
    font-size: 0.8rem; font-weight: 500; color: var(--muted);
    padding: 2px 8px; min-height: 0;
}
[data-testid="stBaseButton-tertiary"]:hover { color: var(--accent); }

/* ── Footer ─────────────────────────────────────────────────────────────── */
.sc-footer {
    text-align: center; font-size: var(--fs-caption); color: var(--faint);
    border-top: 1px solid var(--border);
    margin-top: var(--sp-6); padding: var(--sp-4) 0 var(--sp-2);
}
.sc-footer a, .sc-footer a:visited { color: var(--faint); text-decoration: none; }
.sc-footer a:hover { color: var(--accent); }
</style>
""").substitute(
    bg=BG, surface=SURFACE, border=BORDER, border_strong=BORDER_STRONG,
    accent=ACCENT, accent_bg=ACCENT_BG, text=TEXT, muted=TEXT_MUTED, faint=TEXT_FAINT,
    success=SUCCESS, success_bg=SUCCESS_BG,
    warning=WARNING, warning_bg=WARNING_BG,
    danger=DANGER, danger_bg=DANGER_BG,
)


def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)


# ── Reusable fragments ────────────────────────────────────────────────────────

def render_topbar():
    st.markdown(
        f"""
        <div class="sc-topbar">
          <div class="sc-brand">
            <span class="sc-brand-mark">{icon('shield', 15)}</span>
            <span class="sc-brand-name">NetSuite Close Validator</span>
          </div>
          <span class="sc-trust">{icon('lock', 12)} No data stored &middot; processed in-session</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer():
    st.markdown(
        """
        <div class="sc-footer">
          NetSuite Close Validator &middot; built with Streamlit &amp; DuckDB &middot;
          <a href="https://suiteclose.co.uk" target="_blank">SuiteClose</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title, caption=None):
    cap = f'<p class="sc-section-caption">{caption}</p>' if caption else ""
    st.markdown(
        f'<div class="sc-section"><p class="sc-section-title">{html.escape(title)}</p>{cap}</div>',
        unsafe_allow_html=True,
    )


def pill(label, kind):
    """kind: pass | warn | fail | muted"""
    return f'<span class="sc-pill sc-pill-{kind}">{html.escape(label)}</span>'


def stat_chips(items):
    """Render a row of stat chips. items: iterable of (label, value[, kind])."""
    chips = []
    for item in items:
        label, value = item[0], item[1]
        kind = item[2] if len(item) > 2 and item[2] else ""
        chips.append(
            f'<span class="sc-chip"><span class="sc-chip-label">{html.escape(str(label))}</span>'
            f'<span class="sc-chip-value {kind}">{html.escape(str(value))}</span></span>'
        )
    st.markdown(f'<div class="sc-chips">{"".join(chips)}</div>', unsafe_allow_html=True)


def total_row(items):
    """Render a bold totals bar. items: iterable of (label, value[, kind])."""
    parts = []
    for item in items:
        label, value = item[0], item[1]
        kind = item[2] if len(item) > 2 and item[2] else ""
        parts.append(
            f'<span class="sc-total-item"><span class="sc-total-label">{html.escape(str(label))}</span>'
            f'<span class="sc-total-value {kind}">{html.escape(str(value))}</span></span>'
        )
    st.markdown(f'<div class="sc-total-row">{"".join(parts)}</div>', unsafe_allow_html=True)


def empty_state(title, hint=None, icon_name="inbox"):
    hint_html = f'<p class="sc-empty-hint">{html.escape(hint)}</p>' if hint else ""
    st.markdown(
        f"""
        <div class="sc-empty">
          <div class="sc-empty-icon">{icon(icon_name, 26)}</div>
          <p class="sc-empty-title">{html.escape(title)}</p>
          {hint_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def pass_note(text):
    st.markdown(
        f'<span class="sc-pass-note">{icon("check", 14)} {html.escape(text)}</span>',
        unsafe_allow_html=True,
    )
