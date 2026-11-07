"""Data & Export page: cleaning summary and a preview of the dataset."""
import streamlit as st

from src.dashboard_extras import render_data_quality_section, render_page_title
from src.dashboard_sections import render_raw_preview

df = st.session_state["filtered_df"]

render_page_title(
    "🗂️ Data & Export",
    "See how the data was cleaned and preview the records. "
    "Use the sidebar button to download the full dataset as an Excel file for Power BI.",
    st.session_state["source_label"], df,
)
render_data_quality_section(st.session_state["cleaning_stats"])
render_raw_preview(df, expanded=True)