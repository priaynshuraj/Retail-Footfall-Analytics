"""Overview page: headline numbers, insights and the main charts."""
import streamlit as st

from src.dashboard_sections import (
    render_dwell_section,
    render_header,
    render_insights_section,
    render_metric_cards,
    render_trend_section,
    render_where_when_section,
)

df = st.session_state["filtered_df"]

render_header(st.session_state["source_label"], df)
render_metric_cards(df)
render_insights_section(df)
render_trend_section(df)
render_where_when_section(df)
render_dwell_section(df)