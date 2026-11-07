"""Deep Dive page: click-to-explore hours, anomaly detection and side-by-side comparison."""
import streamlit as st

from src.dashboard_extras import render_page_title
from src.dashboard_sections import (
    render_anomaly_section,
    render_comparison_section,
    render_deep_dive_section,
)

df = st.session_state["filtered_df"]

render_page_title(
    "🔍 Deep Dive",
    "Drill into individual hours, spot unusual days and compare stores or time periods.",
    st.session_state["source_label"], df,
)
render_deep_dive_section(df)
render_anomaly_section(df)
render_comparison_section(st.session_state["full_df"])