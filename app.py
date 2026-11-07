"""Retail Footfall Analytics: entry point. Sets up the shared sidebar and routes to the pages."""
import streamlit as st

from src.dashboard_extras import maybe_show_welcome, render_documentation_button, render_export_button
from src.dashboard_sections import inject_css, render_data_source, render_filters

st.set_page_config(page_title="Retail Footfall Analytics", page_icon="📊", layout="wide")
inject_css()
maybe_show_welcome()

full_df, cleaning_stats, source_label = render_data_source()
render_export_button(full_df)
render_documentation_button()
filtered_df = render_filters(full_df)

# Share the data with the page scripts in views/
st.session_state["full_df"] = full_df
st.session_state["filtered_df"] = filtered_df
st.session_state["cleaning_stats"] = cleaning_stats
st.session_state["source_label"] = source_label

pages = [
    st.Page("views/overview.py", title="Overview", icon="📊", default=True),
    st.Page("views/deep_dive.py", title="Deep Dive", icon="🔍"),
    st.Page("views/staffing_tool.py", title="Staffing Tool", icon="🧮"),
    st.Page("views/data_export.py", title="Data & Export", icon="🗂️"),
]
st.navigation(pages).run()