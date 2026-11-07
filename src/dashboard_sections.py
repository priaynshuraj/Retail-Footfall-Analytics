"""Streamlit UI building blocks for the footfall dashboard."""
import io
from datetime import timedelta
from pathlib import Path
import pandas as pd
import streamlit as st
from streamlit_echarts import st_echarts

from config import (
    ANOMALY_STD_DEV_MULTIPLIER,
    DEFAULT_COST_PER_STAFF_HOUR,
    DEFAULT_CUSTOMERS_PER_STAFF,
    MAX_UPLOAD_ROWS,
    RAW_DATA_PATH,
    REQUIRED_COLUMNS,
)
from src import chart_options as charts
from src.analysis import (
    build_staffing_bands,
    compute_dashboard_metrics,
    daily_trend,
    day_hour_matrix,
    detect_anomalies,
    dwell_time_boxplot_stats,
    dwell_time_histogram,
    evaluate_roster,
    filter_data,
    footfall_by_day_of_week,
    generate_insights,
    hour_profile,
    hourly_summary,
    segment_summary,
    staffing_requirements,
    store_summary,
    weekday_vs_weekend,
)
from src.data_loader import load_raw_data, validate_schema
from src.preprocessing import build_datetime_features, clean_data
from src.utils import format_percent_change

_CUSTOM_CSS = """
<style>
.kpi-label {font-size: 0.85rem; color: #6b7280; margin-bottom: 2px;}
.kpi-value {font-size: 2.1rem; font-weight: 600; line-height: 1.2;}
.kpi-badge {display: inline-block; font-size: 0.75rem; font-weight: 600;
            padding: 2px 8px; border-radius: 6px; margin-top: 4px;}
.kpi-up {background: #dcfce7; color: #15803d;}
.kpi-down {background: #fee2e2; color: #b91c1c;}
.kpi-neutral {background: #e0e7ff; color: #3730a3;}
</style>
"""


def inject_css():
    """Add the small amount of custom CSS used by the metric cards."""
    st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- data loading
def _run_pipeline(raw_df):
    """Datetime features + cleaning: the same steps main.py runs."""
    df = build_datetime_features(raw_df)
    return clean_data(df)


@st.cache_data(show_spinner="Loading default dataset...")
def load_default_data():
    """Run the pipeline on the bundled raw CSV."""
    raw_df = load_raw_data(RAW_DATA_PATH)
    validate_schema(raw_df)
    return _run_pipeline(raw_df)


@st.cache_data(show_spinner="Cleaning uploaded dataset...")
def load_uploaded_data(file_bytes):
    """Validate and clean a user-uploaded CSV (given as raw bytes)."""
    raw_df = pd.read_csv(io.BytesIO(file_bytes))
    if len(raw_df) > MAX_UPLOAD_ROWS:
        raise ValueError(
            f"File has {len(raw_df):,} rows; the limit is {MAX_UPLOAD_ROWS:,}."
        )
    validate_schema(raw_df)
    df, stats = _run_pipeline(raw_df)
    if df.empty:
        raise ValueError("No valid rows left after cleaning.")
    return df, stats


def _show_upload_instructions():
    """Main-area help shown until a valid file is uploaded."""
    st.title("📊 Retail Footfall Analytics")
    st.info("Upload a CSV with the columns below to run the same analysis on your own data.")
    st.code(", ".join(REQUIRED_COLUMNS))
    st.caption("Date as YYYY-MM-DD, Entry_Time and Exit_Time as HH:MM:SS, Dwell_Time_Min in minutes.")
    try:
        sample = load_raw_data(RAW_DATA_PATH).head(50)
        st.download_button(
            "Download a sample file in the right format",
            data=sample.to_csv(index=False).encode("utf-8"),
            file_name="sample_footfall_format.csv",
            mime="text/csv",
        )
    except FileNotFoundError:
        pass


def render_data_source():
    """Sidebar dataset picker. Returns (cleaned_df, cleaning_stats, source_label)."""
    st.sidebar.markdown("### Dataset")
    choice = st.sidebar.radio(
        "Data source",
        ["Default dataset", "Upload my own CSV"],
        label_visibility="collapsed",
    )

    if choice == "Default dataset":
        try:
            df, stats = load_default_data()
        except FileNotFoundError:
            st.error(f"Default dataset not found at `{RAW_DATA_PATH}`.")
            st.stop()
        source_label = "Default dataset (retail_footfall.csv)"
        st.session_state["source_name"] = "retail_footfall"
    else:
        uploaded = st.sidebar.file_uploader("Upload a CSV file", type=["csv"])
        if uploaded is None:
            _show_upload_instructions()
            st.stop()
        try:
            df, stats = load_uploaded_data(uploaded.getvalue())
        except Exception as error:
            st.sidebar.error("Could not process this file.")
            st.error(f"**Upload failed:** {error}")
            _show_upload_instructions()
            st.stop()
        source_label = f"Uploaded file ({uploaded.name})"
        st.session_state["source_name"] = Path(uploaded.name).stem

    removed = stats['initial_rows'] - stats['final_rows']
    st.sidebar.caption(f"{stats['final_rows']:,} rows loaded, {removed:,} removed during cleaning.")
    return df, stats, source_label


# ---------------------------------------------------------------------- filters
def render_filters(df):
    """Sidebar filters. Returns the filtered DataFrame."""
    st.sidebar.markdown("### Filters")

    min_date, max_date = df['Date'].min().date(), df['Date'].max().date()
    date_range = st.sidebar.date_input(
        "Reporting Period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if len(date_range) != 2:
        st.sidebar.info("Pick an end date to apply the range.")
        st.stop()
    start_date, end_date = date_range

    stores = st.sidebar.multiselect(
        "Store", sorted(df['Store_ID'].unique()), placeholder="All stores"
    )
    day_types = st.sidebar.multiselect(
        "Day Type", sorted(df['Day_Type'].unique()), placeholder="All days"
    )

    min_hour, max_hour = int(df['Hour'].min()), int(df['Hour'].max())
    if min_hour < max_hour:
        hour_range = st.sidebar.slider(
            "Hour of day", min_hour, max_hour, (min_hour, max_hour), format="%d:00"
        )
    else:
        hour_range = (min_hour, max_hour)

    filtered = filter_data(df, start_date, end_date, stores, day_types, hour_range)
    if filtered.empty:
        st.warning("No records match the selected filters. Widen the filters in the sidebar.")
        st.stop()
    return filtered


# ----------------------------------------------------------------- page header
def render_header(source_label, df):
    """Page title, one-line description and the analysis period."""
    st.title("📊 Retail Footfall Analytics")
    st.markdown(
        "Interactive view of customer traffic, peak hours and staffing needs across your stores."
    )
    st.markdown(
        f"**Analysis period:** {df['Date'].min():%Y-%m-%d} to {df['Date'].max():%Y-%m-%d}"
        f" &nbsp;|&nbsp; **Source:** {source_label}"
    )


# ---------------------------------------------------------------- metric cards
def _sparkline_option(values, kind, color):
    """Minimal ECharts option for the small chart at the bottom of a card."""
    series = {"type": kind, "data": values, "itemStyle": {"color": color}}
    if kind == "line":
        series.update({
            "smooth": True,
            "showSymbol": False,
            "lineStyle": {"color": color, "width": 2},
            "areaStyle": {"color": color, "opacity": 0.12},
        })
    else:
        series["barWidth"] = "55%"
    return {
        "animation": False,
        "grid": {"left": 0, "right": 0, "top": 6, "bottom": 0},
        "xAxis": {"type": "category", "show": False, "data": list(range(len(values)))},
        "yAxis": {"type": "value", "show": False, "scale": kind == "line"},
        "tooltip": {"trigger": "axis"},
        "series": [series],
    }


def _badge_html(text, tone):
    """Small coloured pill: tone is 'up', 'down' or 'neutral'."""
    arrow = {"up": "▲ ", "down": "▼ ", "neutral": ""}[tone]
    return f'<span class="kpi-badge kpi-{tone}">{arrow}{text}</span>'


def _change_badge(change):
    """Badge for a % change vs the previous 7 days (neutral if not enough data)."""
    if change is None:
        return _badge_html("Select 14+ days for trend", "neutral")
    tone = "up" if change >= 0 else "down"
    return _badge_html(f"{abs(change):.1f}% vs prev 7d", tone)


def _metric_card(label, value, badge_html, option, key):
    """One bordered card: label, big value, badge and a sparkline."""
    with st.container(border=True):
        st.markdown(
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>{badge_html}',
            unsafe_allow_html=True,
        )
        st_echarts(options=option, height="70px", key=key)


def render_metric_cards(df):
    """Top row of four headline metric cards."""
    m = compute_dashboard_metrics(df)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        _metric_card(
            "Total Footfall", f"{m['total_entries']:,}",
            _change_badge(m['total_entries_change']),
            _sparkline_option(m['spark_daily_entries'], "line", "#16a34a"),
            key="spark_footfall",
        )
    with col2:
        _metric_card(
            "Avg. Dwell Time", f"{m['avg_dwell']:.1f} min",
            _change_badge(m['avg_dwell_change']),
            _sparkline_option(m['spark_daily_dwell'], "line", "#2563eb"),
            key="spark_dwell",
        )
    with col3:
        _metric_card(
            "Busiest Hour", f"{m['busiest_hour']}:00",
            _badge_html(f"{m['busiest_hour_share']:.1f}% of all entries", "neutral"),
            _sparkline_option(m['spark_hourly'], "bar", "#f59e0b"),
            key="spark_hour",
        )
    with col4:
        _metric_card(
            "Peak Day", m['peak_day'],
            _badge_html(f"{m['peak_day_share']:.1f}% of all entries", "neutral"),
            _sparkline_option(m['spark_by_day'], "bar", "#7c3aed"),
            key="spark_day",
        )


# ------------------------------------------------------------------ raw preview
def render_raw_preview(df, expanded=False):
    """Collapsible preview of the filtered data."""
    with st.expander("🗂️ Raw data preview",expanded=expanded):
        st.caption(f"Showing the first 200 of {len(df):,} filtered rows")
        st.dataframe(df.head(200), width="stretch", hide_index=True)

        

# ----------------------------------------------------------------------- charts
def _render_chart(option, height, key):
    """Draw one ECharts chart."""
    st_echarts(options=option, height=height, key=key)


def _section_header(title, description):
    """Section heading with a one-line description underneath."""
    st.markdown(f"### {title}")
    st.caption(description)


def render_trend_section(df):
    """Daily trend with zoom slider, next to footfall by day of week."""
    _section_header(
        "📈 How are we trending?",
        "Track daily footfall over time (drag the slider to zoom) and compare traffic across days of the week.",
    )
    left, right = st.columns([2, 1])
    with left:
        _render_chart(charts.daily_trend_option(daily_trend(df)), "380px", "chart_daily_trend")
    with right:
        _render_chart(charts.day_of_week_option(footfall_by_day_of_week(df)), "380px", "chart_day_of_week")


def render_where_when_section(df):
    """Heatmap of day x hour, plus hourly bands, store comparison and weekday/weekend split."""
    _section_header(
        "🕒 Where & When?",
        "Find the exact day-hour slots, hours and stores where traffic concentrates.",
    )
    _render_chart(charts.heatmap_option(day_hour_matrix(df)), "400px", "chart_heatmap")

    hourly = build_staffing_bands(hourly_summary(df))
    col1, col2, col3 = st.columns(3)
    with col1:
        _render_chart(charts.hourly_bands_option(hourly), "340px", "chart_hourly_bands")
        st.caption("Bands are relative to the selected data: hours are split into Low / Normal / Peak by equal-width ranges.")
    with col2:
        _render_chart(charts.store_comparison_option(store_summary(df)), "340px", "chart_store")
    with col3:
        _render_chart(charts.weekday_weekend_option(weekday_vs_weekend(df)), "340px", "chart_weekday_weekend")


def render_dwell_section(df):
    """Dwell-time histogram and weekday/weekend box plot."""
    _section_header(
        "⏱️ How long do customers stay?",
        "Distribution of time spent in store, and how it compares between weekdays and weekends.",
    )
    labels, counts = dwell_time_histogram(df)
    categories, boxes, outliers = dwell_time_boxplot_stats(df)
    left, right = st.columns(2)
    with left:
        _render_chart(charts.dwell_histogram_option(labels, counts), "340px", "chart_dwell_hist")
    with right:
        _render_chart(charts.dwell_boxplot_option(categories, boxes, outliers), "340px", "chart_dwell_box")





        

# ------------------------------------------------------------ Part 3: insights
def render_insights_section(df):
    """Auto-generated, plain-language findings for the selected data."""
    _section_header(
        "💡 Key Insights",
        "Plain-language findings generated automatically from the data you have selected.",
    )
    with st.container(border=True):
        st.markdown("\n".join(f"- {text}" for text in generate_insights(df)))


# ------------------------------------------------------------ Part 3: deep dive
def _clicked_hour(chart_result, profile):
    """Hour of the bubble the user clicked, or None if nothing is selected."""
    try:
        indices = chart_result["selection"]["point_indices"]
    except (KeyError, TypeError):
        return None
    if not indices or not 0 <= indices[0] < len(profile):
        return None
    return int(profile.iloc[indices[0]]['Hour'])


@st.fragment
def render_deep_dive_section(df):
    """Bubble chart of hours; clicking a bubble shows that hour's breakdown."""
    _section_header(
        "🔍 Deep Dive: Click to Explore",
        "Each bubble is an hour of the day (busier hours sit further right). "
        "Click a bubble to see that hour broken down by day of week and by store.",
    )
    profile = hour_profile(df)
    with st.container(border=True):
        left, right = st.columns([3, 2])
        with left:
            result = st_echarts(
                options=charts.deep_dive_option(profile), height="380px",
                key="chart_deep_dive", on_select="rerun", selection_mode="points",
            )
        hour = _clicked_hour(result, profile)
        with right:
            if hour is None:
                st.info("👆 Click a bubble to drill into that hour.")
            else:
                row = profile[profile['Hour'] == hour].iloc[0]
                share = row['Total_Entries'] / profile['Total_Entries'].sum() * 100
                st.markdown(f"#### {hour}:00 - {hour + 1}:00")
                st.metric("Total entries", f"{int(row['Total_Entries']):,}")
                st.metric("Share of all entries", f"{share:.1f}%")
                st.metric("Avg. dwell time", f"{row['Avg_Dwell']:.1f} min")

    if hour is not None:
        hour_df = df[df['Hour'] == hour]
        col1, col2 = st.columns(2)
        with col1:
            _render_chart(
                charts.day_of_week_option(footfall_by_day_of_week(hour_df), f"{hour}:00 by Day of Week"),
                "320px", "chart_drill_days",
            )
        with col2:
            _render_chart(
                charts.store_comparison_option(store_summary(hour_df), f"{hour}:00 by Store"),
                "320px", "chart_drill_stores",
            )


# ------------------------------------------------------------ Part 3: anomalies
@st.fragment
def render_anomaly_section(df):
    """Days whose footfall is unusual compared with similar days."""
    _section_header(
        "🚨 Anomaly Detection",
        "Days with unusually high or low footfall, compared with other days of the same type "
        "(weekdays are compared with weekdays, weekends with weekends).",
    )
    sensitivity = st.slider(
        "Sensitivity: flag days more than this many standard deviations from normal",
        min_value=1.5, max_value=3.5, value=float(ANOMALY_STD_DEV_MULTIPLIER), step=0.1,
        key="anomaly_sensitivity",
    )
    daily = detect_anomalies(df, sensitivity)
    _render_chart(charts.anomaly_option(daily), "340px", "chart_anomalies")

    flagged = daily[daily['Is_Anomaly']]
    if flagged.empty:
        st.success("No unusual days at this sensitivity. Lower the slider to flag more days.")
        return
    table = pd.DataFrame({
        "Date": flagged['Date'].dt.strftime("%Y-%m-%d"),
        "Day": flagged['Day_Name'],
        "Entries": flagged['Entries'].astype(int),
        "Normal for this day type": flagged['Expected'].round(0).astype(int),
        "Std devs from normal": flagged['Z_Score'].round(2),
        "Direction": flagged['Direction'],
    })
    st.dataframe(table, width="stretch", hide_index=True)


# ------------------------------------------------------------ Part 3: comparison



def _pick_two_segments(full_df):
    """Let the user choose two stores or two date ranges. Returns (label_a, df_a, label_b, df_b) or None."""
    mode = st.radio("Compare", ["Two stores", "Two date ranges"], horizontal=True, key="compare_mode")
    col_a, col_b = st.columns(2)

    if mode == "Two stores":
        stores = sorted(full_df['Store_ID'].unique())
        if len(stores) < 2:
            st.info("This dataset has only one store, so there is nothing to compare. Try 'Two date ranges'.")
            return None
        store_a = col_a.selectbox("Store A", stores, index=0, key="compare_store_a")
        store_b = col_b.selectbox("Store B", stores, index=1, key="compare_store_b")
        if store_a == store_b:
            st.warning("Pick two different stores.")
            return None
        return (f"Store {store_a}", full_df[full_df['Store_ID'] == store_a],
                f"Store {store_b}", full_df[full_df['Store_ID'] == store_b])

    min_date, max_date = full_df['Date'].min().date(), full_df['Date'].max().date()
    middle = min_date + (max_date - min_date) // 2
    start_b = min(middle + timedelta(days=1), max_date)
    range_a = col_a.date_input("Period A", value=(min_date, middle),
                               min_value=min_date, max_value=max_date, key="compare_range_a")
    range_b = col_b.date_input("Period B", value=(start_b, max_date),
                               min_value=min_date, max_value=max_date, key="compare_range_b")
    if len(range_a) != 2 or len(range_b) != 2:
        st.info("Pick a start and an end date for both periods.")
        return None
    segment_a = filter_data(full_df, range_a[0], range_a[1])
    segment_b = filter_data(full_df, range_b[0], range_b[1])
    label_a = f"{range_a[0]:%d %b} - {range_a[1]:%d %b}"
    label_b = f"{range_b[0]:%d %b} - {range_b[1]:%d %b}"
    return label_a, segment_a, label_b, segment_b


@st.fragment
def render_comparison_section(full_df):
    """Side-by-side comparison of two stores or two date ranges (uses the full dataset)."""
    _section_header(
        "⚖️ Compare Side by Side",
        "Compare two stores or two time periods. This section uses the full dataset, "
        "independent of the sidebar filters.",
    )
    picked = _pick_two_segments(full_df)
    if picked is None:
        return
    label_a, df_a, label_b, df_b = picked
    if df_a.empty or df_b.empty:
        st.warning("One of the selections has no data. Choose a different store or period.")
        return

    a, b = segment_summary(df_a), segment_summary(df_b)
    table = pd.DataFrame({
        "Metric": ["Total footfall", "Days in period", "Avg. entries per day", "Avg. dwell time (min)", "Busiest hour"],
        label_a: [f"{a['total']:,}", a['days'], f"{a['avg_per_day']:.0f}", f"{a['avg_dwell']:.1f}", f"{a['busiest_hour']}:00"],
        label_b: [f"{b['total']:,}", b['days'], f"{b['avg_per_day']:.0f}", f"{b['avg_dwell']:.1f}", f"{b['busiest_hour']}:00"],
        "Change (B vs A)": [
            format_percent_change(a['total'], b['total']),
            format_percent_change(a['days'], b['days']),
            format_percent_change(a['avg_per_day'], b['avg_per_day']),
            format_percent_change(a['avg_dwell'], b['avg_dwell']),
            "same hour" if a['busiest_hour'] == b['busiest_hour'] else "different hour",
        ],
    }).astype(str)

    left, right = st.columns([2, 3])
    with left:
        st.dataframe(table, width="stretch", hide_index=True)
    with right:
        _render_chart(
            charts.comparison_hourly_option(label_a, a['hourly_avg_per_day'], label_b, b['hourly_avg_per_day']),
            "340px", "chart_compare_hourly",
        )


# ------------------------------------------------------------ Part 3: simulator
@st.fragment
def render_staffing_simulator(df):
    """What-if tool: try a roster and see which hours are short-staffed or over-staffed."""
    _section_header(
        "🧮 What-if Staffing Simulator",
        "Set how many customers one person can serve per hour, then try a roster. "
        "Based on the stores and days currently selected in the sidebar.",
    )
    col1, col2, col3 = st.columns(3)
    capacity = col1.number_input(
        "Customers one staff member serves per hour",
        min_value=1, max_value=200, value=DEFAULT_CUSTOMERS_PER_STAFF, step=1, key="sim_capacity",
    )
    requirement = staffing_requirements(df, capacity)
    default_staff = int(min(max(1, round(requirement['Required_Staff'].median())), 50))
    staff = col2.slider("Staff on the floor (every hour)", min_value=1, max_value=50, value=default_staff)
    cost = col3.number_input(
        "Cost per staff-hour (₹)", min_value=0, value=DEFAULT_COST_PER_STAFF_HOUR, step=10, key="sim_cost",
    )

    result = evaluate_roster(requirement, staff, cost)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Short-staffed hours", result['short_hours'], f"{result['staff_hours_short']} staff-hours short per day",
              delta_color="inverse")
    m2.metric("Over-staffed hours", result['over_hours'], f"{result['staff_hours_excess']} staff-hours extra per day",
              delta_color="off")
    m3.metric("Your roster, cost per day", f"₹{result['current_cost']:,}")
    saving = result['current_cost'] - result['recommended_cost']
    m4.metric("Matched-to-demand roster, cost per day", f"₹{result['recommended_cost']:,}",
              f"₹{abs(saving):,} {'saved' if saving >= 0 else 'more than your roster'}",
              delta_color="normal" if saving >= 0 else "inverse")

    _render_chart(charts.staffing_option(requirement, staff), "360px", "chart_staffing")
    st.caption("Bars show the staff each hour needs (average day). Red bars above the dashed line are hours "
               "where your roster is too small; amber bars below it are hours with extra people.")

    with st.expander("Hourly details"):
        details = pd.DataFrame({
            "Hour": requirement['Hour'].astype(int).astype(str) + ":00",
            "Avg. entries per day": requirement['Avg_Entries_Per_Day'].round(1),
            "Traffic band": requirement['Traffic_Band'].astype(str),
            "Required staff": requirement['Required_Staff'],
            "Your roster": staff,
            "Gap (roster - required)": staff - requirement['Required_Staff'],
        })
        st.dataframe(details, width="stretch", hide_index=True)