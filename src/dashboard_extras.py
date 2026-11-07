"""Dashboard extras: welcome screen, Excel download, documentation viewer and page helpers."""
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from config import DOCUMENTATION_PDF_PATH, PROJECT_TITLE, TEAM_MEMBERS, TEAM_NAME
from src.analysis import (
    build_staffing_bands,
    footfall_by_day_of_week,
    hourly_summary,
    store_summary,
    weekday_vs_weekend,
)
from src.powerbi_export import build_powerbi_excel

_WELCOME_CSS = """
<style>
@keyframes welcomeFade {from {opacity: 0; transform: translateY(8px);} to {opacity: 1; transform: none;}}
.welcome-hero {background: linear-gradient(135deg, #0f1b33 0%, #2563eb 100%); color: #ffffff;
               border-radius: 14px; padding: 22px 26px; margin-bottom: 18px;
               animation: welcomeFade 0.5s ease-out;}
.welcome-eyebrow {font-size: 0.72rem; letter-spacing: 0.14em; opacity: 0.75; font-weight: 600;}
.welcome-title {font-size: 1.7rem; font-weight: 700; line-height: 1.25; margin-top: 2px;}
.member-grid {display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 6px;}
.member-card {display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-radius: 12px;
              border: 1px solid rgba(128, 128, 128, 0.28); background: rgba(37, 99, 235, 0.06);
              animation: welcomeFade 0.5s ease-out both;}
.member-card:nth-child(2) {animation-delay: 0.08s;}
.member-card:nth-child(3) {animation-delay: 0.16s;}
.member-card:nth-child(4) {animation-delay: 0.24s;}
.avatar {width: 42px; height: 42px; border-radius: 50%; display: flex; align-items: center;
         justify-content: center; background: linear-gradient(135deg, #2563eb, #7c3aed);
         color: #ffffff; font-weight: 700; flex-shrink: 0;}
.member-name {font-weight: 600;}
.member-id {font-family: monospace; font-size: 0.8rem; opacity: 0.7;}
@media (max-width: 640px) {.member-grid {grid-template-columns: 1fr;}}
</style>
"""


# --------------------------------------------------------------- welcome screen
def _initials(name):
    """First letters of the first and last word of a name, e.g. 'Kumar Aditya' -> 'KA'."""
    words = name.split()
    return (words[0][0] + words[-1][0]).upper() if len(words) > 1 else name[:2].upper()


def _mark_welcome_seen():
    """Remember that this browser session has already seen the welcome pop-up."""
    st.session_state["welcome_seen"] = True


@st.dialog(TEAM_NAME, width="large", on_dismiss=_mark_welcome_seen)
def _welcome_dialog():
    """Pop-up shown once per browser session with the project and team details."""
    st.markdown(_WELCOME_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="welcome-hero"><div class="welcome-eyebrow">PROJECT</div>'
        f'<div class="welcome-title">{escape(PROJECT_TITLE)}</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("#### Project Team Members")
    cards = "".join(
        f'<div class="member-card"><div class="avatar">{escape(_initials(name))}</div>'
        f'<div><div class="member-name">{escape(name)}</div>'
        f'<div class="member-id">{escape(enrollment)}</div></div></div>'
        for name, enrollment in TEAM_MEMBERS
    )
    st.markdown(f'<div class="member-grid">{cards}</div>', unsafe_allow_html=True)
    st.caption("Click below to continue to the dashboard.")
    if st.button("Continue to Dashboard", type="primary", width="stretch"):
        _mark_welcome_seen()
        st.rerun()


def maybe_show_welcome():
    """Show the welcome pop-up first and hold the rest of the app until it is closed.

    Both the "Continue to Dashboard" button and the close (X) button mark the
    pop-up as seen and rerun the app. Nothing heavy runs before that, so both
    respond instantly even on the very first load.
    """
    if not st.session_state.get("welcome_seen"):
        _welcome_dialog()
        st.stop()


# ---------------------------------------------------------------- Excel download
@st.cache_data(show_spinner="Preparing Excel file...")
def _excel_bytes(df):
    """Build the Power BI-ready workbook for a cleaned dataset (cached per dataset)."""
    return build_powerbi_excel(
        df=df,
        hourly_df=build_staffing_bands(hourly_summary(df)),
        daily_df=footfall_by_day_of_week(df).rename_axis('Day_Name').reset_index(name='Total_Entries'),
        weekday_weekend_df=weekday_vs_weekend(df),
        store_df=store_summary(df),
    )


def render_export_button(full_df):
    """Sidebar button that downloads an Excel workbook built from the whole dataset."""
    file_name = f"{st.session_state.get('source_name', 'retail_footfall')}_powerbi.xlsx"
    st.sidebar.download_button(
        "⬇️ Download Excel (Power BI)",
        data=_excel_bytes(full_df),
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Cleaned data and summary tables of the full dataset, ready to import into Power BI.",
        width="stretch",
    )


# ------------------------------------------------------- project documentation
@st.dialog("Project Documentation", width="large")
def _documentation_dialog():
    """Pop-up to read and download the project documentation PDF."""
    path = Path(DOCUMENTATION_PDF_PATH)
    if not path.exists():
        st.info("The project documentation has not been added yet.")
        return
    pdf_bytes = path.read_bytes()
    st.download_button(
        "⬇️ Download PDF", data=pdf_bytes, file_name=path.name,
        mime="application/pdf", type="primary", on_click="ignore",
    )
    try:
        st.pdf(pdf_bytes, height=600)
    except Exception:
        st.caption("In-browser preview is not available here. Please use the download button.")


def render_documentation_button():
    """Sidebar button that opens the project documentation viewer."""
    if st.sidebar.button("📄 Project Documentation", width="stretch"):
        _documentation_dialog()


# ------------------------------------------------------------------ page helpers
def render_page_title(title, description, source_label, df):
    """Title, one-line description and the analysis period of a page."""
    st.title(title)
    st.markdown(description)
    st.markdown(
        f"**Analysis period:** {df['Date'].min():%Y-%m-%d} to {df['Date'].max():%Y-%m-%d}"
        f" &nbsp;|&nbsp; **Source:** {source_label}"
    )


def render_data_quality_section(stats):
    """Table of what the cleaning step did to the loaded dataset."""
    st.markdown("### 🧹 Data Cleaning Summary")
    st.caption("What the cleaning step changed in the dataset behind this dashboard.")
    table = pd.DataFrame({
        "Check performed": [
            "Records loaded",
            "Duplicate Visit_ID records removed",
            "Missing Entry_Count values filled",
            "Invalid dwell time or entry count removed",
            "Exit time before entry time removed",
            "Records after cleaning",
        ],
        "Rows": [
            stats['initial_rows'], stats['duplicates_removed'], stats['missing_entry_count_filled'],
            stats['invalid_dwell_or_count_removed'], stats['invalid_time_order_removed'], stats['final_rows'],
        ],
    })
    st.dataframe(table, width="stretch", hide_index=True)