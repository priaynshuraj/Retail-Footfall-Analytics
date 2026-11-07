"""Staffing Tool page: what-if staffing simulator."""
import streamlit as st

from src.dashboard_extras import render_page_title
from src.dashboard_sections import render_staffing_simulator

df = st.session_state["filtered_df"]

render_page_title(
    "🧮 Staffing Tool",
    "Test staffing levels against real footfall and see which hours are short-staffed or over-staffed.",
    st.session_state["source_label"], df,
)
render_staffing_simulator(df)