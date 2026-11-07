"""ECharts option builders: plain dicts only, no Streamlit rendering code."""
import pandas as pd
from streamlit_echarts import JsCode

BLUE = "#2563eb"
GREEN = "#16a34a"
AMBER = "#f59e0b"
PURPLE = "#7c3aed"
RED = "#ef4444"
LIGHT_BLUE = "#60a5fa"

BAND_COLORS = {"Low": LIGHT_BLUE, "Normal": AMBER, "Peak": RED}
HEATMAP_COLORS = ["#ffffcc", "#fed976", "#fd8d3c", "#e31a1c", "#800026"]


def _title(text):
    """Centered chart title block."""
    return {"text": text, "left": "center", "textStyle": {"fontSize": 14, "fontWeight": 600}}


def daily_trend_option(trend_df):
    """Daily footfall line with area fill, optional 7-day average and zoom slider."""
    dates = [d.strftime("%Y-%m-%d") for d in trend_df.index]
    entries = [int(v) for v in trend_df['Entries']]
    moving_avg = [None if pd.isna(v) else float(v) for v in trend_df['Moving_Avg_7d']]

    series = [{
        "name": "Daily footfall", "type": "line", "smooth": True, "showSymbol": False,
        "data": entries, "itemStyle": {"color": BLUE},
        "lineStyle": {"width": 2}, "areaStyle": {"opacity": 0.15},
    }]
    legend = ["Daily footfall"]
    if any(v is not None for v in moving_avg):
        series.append({
            "name": "7-day average", "type": "line", "smooth": True, "showSymbol": False,
            "data": moving_avg, "itemStyle": {"color": AMBER},
            "lineStyle": {"width": 2, "type": "dashed"},
        })
        legend.append("7-day average")

    return {
        "title": _title("Daily Footfall Trend"),
        "tooltip": {"trigger": "axis"},
        "legend": {"data": legend, "top": 34},
        "grid": {"left": 55, "right": 25, "top": 70, "bottom": 70},
        "xAxis": {"type": "category", "data": dates, "boundaryGap": False},
        "yAxis": {"type": "value"},
        "dataZoom": [{"type": "inside"}, {"type": "slider", "height": 18, "bottom": 10}],
        "series": series,
    }


def day_of_week_option(by_day, title="Footfall by Day of Week"):
    """Bar chart of footfall per weekday; weekends highlighted in amber."""
    days = list(by_day.index)
    data = [
        {"value": int(value), "itemStyle": {"color": AMBER if day in ("Saturday", "Sunday") else BLUE}}
        for day, value in zip(days, by_day.tolist())
    ]
    return {
        "title": _title(title),
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": 55, "right": 20, "top": 60, "bottom": 40},
        "xAxis": {"type": "category", "data": [d[:3] for d in days]},
        "yAxis": {"type": "value"},
        "series": [{"type": "bar", "data": data, "barWidth": "60%"}],
    }


def heatmap_option(matrix):
    """Day x hour heatmap with a colour scale and a readable tooltip."""
    days = list(matrix.index)
    hours = list(matrix.columns)
    data = [
        {"name": f"{day}, {hour}:00", "value": [x, y, int(matrix.loc[day, hour])]}
        for y, day in enumerate(days)
        for x, hour in enumerate(hours)
    ]
    max_value = max(1, int(matrix.values.max()))
    tooltip_js = JsCode(
        "function (p) { return p.name + '<br/><b>' + p.value[2].toLocaleString() + '</b> entries'; }"
    )
    return {
        "title": _title("Footfall Heatmap: Day of Week x Hour"),
        "tooltip": {"position": "top", "formatter": tooltip_js},
        "grid": {"left": 95, "right": 30, "top": 50, "bottom": 100},
        "xAxis": {"type": "category", "data": [f"{h}:00" for h in hours], "splitArea": {"show": True}},
        "yAxis": {"type": "category", "data": days, "inverse": True, "splitArea": {"show": True}},
        "visualMap": {
            "min": 0, "max": max_value, "calculable": True, "orient": "horizontal",
            "left": "center", "bottom": 5, "inRange": {"color": HEATMAP_COLORS},
        },
        "series": [{
            "type": "heatmap", "data": data, "label": {"show": False},
            "emphasis": {"itemStyle": {"shadowBlur": 8, "shadowColor": "rgba(0,0,0,0.4)"}},
        }],
    }


def hourly_bands_option(hourly_df):
    """Hourly footfall bars coloured by staffing band (Low / Normal / Peak)."""
    hours = [f"{int(h)}:00" for h in hourly_df['Hour']]
    bands = [str(b) for b in hourly_df['Traffic_Band']]
    values = [int(v) for v in hourly_df['Total_Entries']]

    series = [
        {
            "name": band, "type": "bar", "stack": "footfall", "barWidth": "65%",
            "itemStyle": {"color": color},
            "data": [value if b == band else None for value, b in zip(values, bands)],
        }
        for band, color in BAND_COLORS.items()
    ]
    return {
        "title": _title("Hourly Footfall by Staffing Band"),
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {"data": list(BAND_COLORS), "top": 34},
        "grid": {"left": 50, "right": 15, "top": 65, "bottom": 50},
        "xAxis": {"type": "category", "data": hours, "axisLabel": {"rotate": 45, "interval": 0, "fontSize": 10}},
        "yAxis": {"type": "value"},
        "series": series,
    }


def store_comparison_option(store_df, title="Store Comparison"):
    """Footfall per store (bars) with average dwell time (line, right axis)."""
    stores = [str(s) for s in store_df['Store_ID']]
    return {
        "title": _title(title),
        "tooltip": {"trigger": "axis"},
        "legend": {"data": ["Total entries", "Avg dwell (min)"], "top": 34},
        "grid": {"left": 55, "right": 55, "top": 65, "bottom": 40},
        "xAxis": {"type": "category", "data": stores},
        "yAxis": [
            {"type": "value", "name": "Entries"},
            {"type": "value", "name": "Minutes", "min": 0, "splitLine": {"show": False}},
        ],
        "series": [
            {"name": "Total entries", "type": "bar", "barWidth": "45%",
             "itemStyle": {"color": BLUE}, "data": [int(v) for v in store_df['Total_Entries']]},
            {"name": "Avg dwell (min)", "type": "line", "yAxisIndex": 1, "symbolSize": 8,
             "itemStyle": {"color": AMBER}, "lineStyle": {"width": 2},
             "data": [round(float(v), 2) for v in store_df['Avg_Dwell_Time']]},
        ],
    }


def weekday_weekend_option(ww_df):
    """Donut chart: share of footfall on weekdays vs weekends."""
    colors = {"Weekday": BLUE, "Weekend": AMBER}
    data = [
        {"name": str(row['Day_Type']), "value": int(row['Total_Entries']),
         "itemStyle": {"color": colors.get(str(row['Day_Type']), PURPLE)}}
        for _, row in ww_df.iterrows()
    ]
    return {
        "title": _title("Weekday vs Weekend"),
        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
        "legend": {"bottom": 0},
        "series": [{
            "type": "pie", "radius": ["45%", "70%"], "center": ["50%", "52%"], "data": data,
            "label": {"formatter": "{b}\n{d}%"},
        }],
    }


def dwell_histogram_option(labels, counts):
    """Histogram of dwell time (minutes) as a gapless bar chart."""
    return {
        "title": _title("Dwell Time Distribution"),
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": 55, "right": 20, "top": 60, "bottom": 60},
        "xAxis": {"type": "category", "data": labels, "name": "Dwell time (min)",
                  "nameLocation": "middle", "nameGap": 38,
                  "axisLabel": {"rotate": 45, "fontSize": 10}},
        "yAxis": {"type": "value", "name": "Visits"},
        "series": [{"type": "bar", "data": counts, "barCategoryGap": "4%", "itemStyle": {"color": "#06b6d4"}}],
    }


def dwell_boxplot_option(categories, boxes, outliers):
    """Box plot of dwell time per day type, with outlier points."""
    palette = {"Weekday": ("#bfdbfe", BLUE), "Weekend": ("#fde68a", AMBER)}
    box_data = [
        {"value": box, "itemStyle": {
            "color": palette.get(cat, ("#ddd6fe", PURPLE))[0],
            "borderColor": palette.get(cat, ("#ddd6fe", PURPLE))[1]}}
        for cat, box in zip(categories, boxes)
    ]
    return {
        "title": _title("Dwell Time: Weekday vs Weekend"),
        "tooltip": {"trigger": "item"},
        "grid": {"left": 55, "right": 20, "top": 60, "bottom": 40},
        "xAxis": {"type": "category", "data": categories},
        "yAxis": {"type": "value", "name": "Minutes"},
        "series": [
            {"name": "Dwell time", "type": "boxplot", "data": box_data},
            {"name": "Outliers", "type": "scatter", "data": outliers, "silent": True,
             "symbolSize": 6, "itemStyle": {"color": RED, "opacity": 0.6}},
        ],
    }



# ------------------------------------------------------------------ Part 3
STATUS_COLORS = {"Short-staffed": RED, "Balanced": GREEN, "Over-staffed": AMBER}


def deep_dive_option(profile_df):
    """Bubble chart: each bubble is an hour (x = total entries, y = average dwell time)."""
    data = [
        {"name": f"{int(row['Hour'])}:00",
         "value": [int(row['Total_Entries']), round(float(row['Avg_Dwell']), 2)]}
        for _, row in profile_df.iterrows()
    ]
    tooltip_js = JsCode(
        "function (p) { return '<b>' + p.name + '</b><br/>Entries: ' + p.value[0].toLocaleString()"
        " + '<br/>Avg dwell: ' + p.value[1] + ' min<br/><i>Click to drill down</i>'; }"
    )
    return {
        "title": _title("Hours of the Day: Footfall vs Dwell Time"),
        "tooltip": {"trigger": "item", "formatter": tooltip_js},
        "grid": {"left": 70, "right": 30, "top": 60, "bottom": 60},
        "xAxis": {"type": "value", "name": "Total entries in the hour", "nameLocation": "middle", "nameGap": 32},
        "yAxis": {"type": "value", "name": "Avg dwell (min)", "scale": True},
        "series": [{
            "type": "scatter", "data": data, "symbolSize": 44,
            "itemStyle": {"color": BLUE, "opacity": 0.75},
            "label": {"show": True, "formatter": "{b}", "color": "#ffffff", "fontSize": 10},
            "selectedMode": "single",
            "select": {"itemStyle": {"borderColor": "#111827", "borderWidth": 3, "opacity": 1}},
            "emphasis": {"itemStyle": {"opacity": 1}},
        }],
    }


def anomaly_option(daily_df):
    """Daily footfall line with anomalous days highlighted as red points."""
    dates = [d.strftime("%Y-%m-%d") for d in daily_df['Date']]
    entries = [int(v) for v in daily_df['Entries']]
    flagged = [
        [d, int(v)] for d, v, flag in zip(dates, entries, daily_df['Is_Anomaly']) if flag
    ]
    return {
        "title": _title("Daily Footfall with Unusual Days Highlighted"),
        "tooltip": {"trigger": "axis"},
        "legend": {"data": ["Daily footfall", "Unusual day"], "top": 34},
        "grid": {"left": 55, "right": 25, "top": 70, "bottom": 50},
        "xAxis": {"type": "category", "data": dates, "boundaryGap": False},
        "yAxis": {"type": "value"},
        "series": [
            {"name": "Daily footfall", "type": "line", "showSymbol": False, "data": entries,
             "itemStyle": {"color": BLUE}, "lineStyle": {"width": 2}},
            {"name": "Unusual day", "type": "scatter", "data": flagged, "symbolSize": 14,
             "itemStyle": {"color": RED, "borderColor": "#ffffff", "borderWidth": 1.5}},
        ],
    }


def comparison_hourly_option(label_a, series_a, label_b, series_b):
    """Two lines: average entries per day in each hour, for segment A and segment B."""
    hours = sorted(set(series_a.index) | set(series_b.index))
    values_a = [round(float(series_a.get(h, 0.0)), 1) for h in hours]
    values_b = [round(float(series_b.get(h, 0.0)), 1) for h in hours]
    return {
        "title": _title("Average Entries per Day, by Hour"),
        "tooltip": {"trigger": "axis"},
        "legend": {"data": [label_a, label_b], "top": 34},
        "grid": {"left": 55, "right": 25, "top": 70, "bottom": 40},
        "xAxis": {"type": "category", "data": [f"{h}:00" for h in hours], "boundaryGap": False},
        "yAxis": {"type": "value"},
        "series": [
            {"name": label_a, "type": "line", "smooth": True, "data": values_a,
             "itemStyle": {"color": BLUE}, "lineStyle": {"width": 3}, "areaStyle": {"opacity": 0.1}},
            {"name": label_b, "type": "line", "smooth": True, "data": values_b,
             "itemStyle": {"color": AMBER}, "lineStyle": {"width": 3}, "areaStyle": {"opacity": 0.1}},
        ],
    }


def staffing_option(requirement_df, staff):
    """Required staff per hour (coloured by status) against a flat roster line."""
    hours = [f"{int(h)}:00" for h in requirement_df['Hour']]
    required = [int(v) for v in requirement_df['Required_Staff']]

    def status_of(needed):
        """Staffing status of one hour compared with the roster."""
        if needed > staff:
            return "Short-staffed"
        return "Balanced" if needed == staff else "Over-staffed"

    statuses = [status_of(needed) for needed in required]
    series = [
        {"name": status, "type": "bar", "stack": "required", "barWidth": "60%",
         "itemStyle": {"color": color},
         "data": [needed if s == status else None for needed, s in zip(required, statuses)]}
        for status, color in STATUS_COLORS.items()
    ]
    series.append({
        "name": "Your roster", "type": "line", "data": [staff] * len(hours), "symbol": "none",
        "itemStyle": {"color": PURPLE}, "lineStyle": {"width": 3, "type": "dashed"},
    })
    return {
        "title": _title("Required Staff per Hour vs Your Roster"),
        "tooltip": {"trigger": "axis"},
        "legend": {"data": list(STATUS_COLORS) + ["Your roster"], "top": 34},
        "grid": {"left": 55, "right": 25, "top": 70, "bottom": 50},
        "xAxis": {"type": "category", "data": hours},
        "yAxis": {"type": "value", "name": "Staff", "minInterval": 1},
        "series": series,
    }