import math

import pandas as pd

from src.utils import format_hour_ranges

def calculate_kpis(df):
    """Overall KPIs: total entries, avg/median dwell time, peak hour."""
    kpis = {
        "Total_Entries": int(df['Entry_Count'].sum()),
        "Avg_Dwell_Time_Min": round(df['Dwell_Time_Min'].mean(), 2),
        "Median_Dwell_Time_Min": df['Dwell_Time_Min'].median(),
        "Busiest_Hour": int(df.groupby('Hour')['Entry_Count'].sum().idxmax()),
        "Quietest_Hour": int(df.groupby('Hour')['Entry_Count'].sum().idxmin()),
        "Busiest_Day": df.groupby('Day_Name')['Entry_Count'].sum().idxmax(),
    }
    return kpis

def hourly_summary(df):
    """Total entries per hour."""
    return df.groupby('Hour')['Entry_Count'].sum().reset_index(name='Total_Entries')

def daily_summary(df):
    """Total entries per day of week, in Mon-Sun order."""
    order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    result = df.groupby('Day_Name')['Entry_Count'].sum().reindex(order).reset_index(name='Total_Entries')
    return result

def weekday_vs_weekend(df):
    """Compare weekday vs weekend traffic."""
    return df.groupby('Day_Type')['Entry_Count'].sum().reset_index(name='Total_Entries')

def store_summary(df):
    """Compare footfall and dwell time across stores."""
    return df.groupby('Store_ID').agg(
        Total_Entries=('Entry_Count', 'sum'),
        Avg_Dwell_Time=('Dwell_Time_Min', 'mean')
    ).reset_index()

def build_staffing_bands(hourly_df):
    """Categorize each hour into Low/Normal/Peak traffic bands."""
    hourly_df['Traffic_Band'] = pd.cut(
        hourly_df['Total_Entries'],
        bins=3,
        labels=['Low', 'Normal', 'Peak']
    )
    return hourly_df



















DAY_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def filter_data(df, start_date, end_date, stores=None, day_types=None, hour_range=None):
    """Filter the cleaned data by date range, stores, day types and hour range.

    Empty or None for stores/day_types/hour_range means "no filter on that field".
    """
    mask = (df['Date'] >= pd.Timestamp(start_date)) & (df['Date'] <= pd.Timestamp(end_date))
    if stores:
        mask &= df['Store_ID'].isin(stores)
    if day_types:
        mask &= df['Day_Type'].isin(day_types)
    if hour_range:
        mask &= df['Hour'].between(hour_range[0], hour_range[1])
    return df[mask]


def _period_change_pct(series, window=7, how="sum"):
    """% change of the latest `window` periods vs the `window` before them.

    Returns None when there is not enough data (fewer than 2 * window periods)
    or when the previous period is zero.
    """
    if len(series) < 2 * window:
        return None
    recent = series.iloc[-window:]
    previous = series.iloc[-2 * window:-window]
    if how == "sum":
        recent_value, previous_value = recent.sum(), previous.sum()
    else:
        recent_value, previous_value = recent.mean(), previous.mean()
    if previous_value == 0:
        return None
    return float((recent_value - previous_value) / previous_value * 100)


def compute_dashboard_metrics(df):
    """Headline numbers and sparkline series for the dashboard's metric cards."""
    daily = df.groupby(df['Date'].dt.normalize()).agg(
        entries=('Entry_Count', 'sum'),
        avg_dwell=('Dwell_Time_Min', 'mean'),
    ).sort_index()
    hourly = df.groupby('Hour')['Entry_Count'].sum().sort_index()
    by_day = df.groupby('Day_Name')['Entry_Count'].sum().reindex(DAY_ORDER).fillna(0)
    total_entries = float(df['Entry_Count'].sum())

    return {
        "total_entries": int(total_entries),
        "total_entries_change": _period_change_pct(daily['entries'], how="sum"),
        "avg_dwell": float(df['Dwell_Time_Min'].mean()),
        "avg_dwell_change": _period_change_pct(daily['avg_dwell'], how="mean"),
        "busiest_hour": int(hourly.idxmax()),
        "busiest_hour_share": float(hourly.max() / total_entries * 100),
        "peak_day": str(by_day.idxmax()),
        "peak_day_share": float(by_day.max() / total_entries * 100),
        "spark_daily_entries": daily['entries'].round(0).tolist(),
        "spark_daily_dwell": daily['avg_dwell'].round(2).tolist(),
        "spark_hourly": hourly.tolist(),
        "spark_by_day": by_day.tolist(),
    }



def daily_trend(df):
    """Daily total entries plus a 7-day moving average.

    The moving average is only computed when the selected days are contiguous
    (no gaps, e.g. no day-type filter); otherwise that column is NaN.
    """
    daily = df.groupby(df['Date'].dt.normalize())['Entry_Count'].sum().sort_index()
    result = daily.to_frame('Entries')
    span_days = (daily.index.max() - daily.index.min()).days + 1
    if len(daily) == span_days:
        result['Moving_Avg_7d'] = daily.rolling(7).mean().round(1)
    else:
        result['Moving_Avg_7d'] = float('nan')
    return result


def footfall_by_day_of_week(df):
    """Total entries for each day of the week (Mon-Sun, 0 if the day has no data)."""
    return df.groupby('Day_Name')['Entry_Count'].sum().reindex(DAY_ORDER).fillna(0)


def day_hour_matrix(df):
    """Total entries for every (day of week, hour); days with no data are dropped."""
    hours = list(range(int(df['Hour'].min()), int(df['Hour'].max()) + 1))
    matrix = df.pivot_table(index='Day_Name', columns='Hour', values='Entry_Count', aggfunc='sum')
    return matrix.reindex(index=DAY_ORDER, columns=hours).dropna(how='all').fillna(0)


def dwell_time_histogram(df, bin_width=3):
    """Dwell-time histogram: returns (bin labels, counts per bin)."""
    max_dwell = int(df['Dwell_Time_Min'].max())
    edges = list(range(0, max_dwell + bin_width + 1, bin_width))
    counts = pd.cut(df['Dwell_Time_Min'], bins=edges, right=False).value_counts(sort=False)
    labels = [f"{edge}-{edge + bin_width}" for edge in edges[:-1]]
    return labels, [int(c) for c in counts.tolist()]


def dwell_time_boxplot_stats(df, max_outliers_per_group=300):
    """Box-plot statistics of dwell time for each day type.

    Returns (categories, boxes, outliers) where each box is
    [whisker_low, Q1, median, Q3, whisker_high] (1.5 * IQR whiskers) and
    outliers is a list of [category_index, value].
    """
    categories, boxes, outliers = [], [], []
    for index, day_type in enumerate(sorted(df['Day_Type'].unique())):
        values = df.loc[df['Day_Type'] == day_type, 'Dwell_Time_Min']
        q1, median, q3 = values.quantile([0.25, 0.5, 0.75]).tolist()
        spread = q3 - q1
        low_fence, high_fence = q1 - 1.5 * spread, q3 + 1.5 * spread
        inside = values[(values >= low_fence) & (values <= high_fence)]
        outside = sorted(set(values[(values < low_fence) | (values > high_fence)].tolist()))
        categories.append(day_type)
        boxes.append([float(inside.min()), float(q1), float(median), float(q3), float(inside.max())])
        outliers.extend([index, float(v)] for v in outside[:max_outliers_per_group])
    return categories, boxes, outliers



# ------------------------------------------------------------ Part 3: insights



def generate_insights(df):
    """Plain-language findings (markdown strings) computed from the selected data."""
    insights = []
    total = float(df['Entry_Count'].sum())

    hourly = hourly_summary(df)
    peak = hourly.loc[hourly['Total_Entries'].idxmax()]
    text = f"**Peak hour is {int(peak['Hour'])}:00**, with {peak['Total_Entries'] / total * 100:.1f}% of all entries"
    if len(hourly) > 1:
        quiet = hourly.loc[hourly['Total_Entries'].idxmin()]
        text += (f"; the quietest hour is **{int(quiet['Hour'])}:00** "
                 f"({quiet['Total_Entries'] / total * 100:.1f}%)")
    insights.append(text + ".")

    banded = build_staffing_bands(hourly.copy())
    peak_hours = banded.loc[banded['Traffic_Band'] == 'Peak', 'Hour'].astype(int).tolist()
    if peak_hours:
        insights.append(
            f"**Add staff during {format_hour_ranges(peak_hours)}**: these hours fall in the Peak traffic band."
        )

    daily = df.groupby(['Date', 'Day_Name', 'Day_Type'])['Entry_Count'].sum().reset_index()
    by_day = daily.groupby('Day_Name')['Entry_Count'].mean()
    if len(by_day) > 1:
        gap = (by_day.max() - by_day.min()) / by_day.min() * 100
        insights.append(
            f"**{by_day.idxmax()} has the highest average footfall per day** (about {by_day.max():.0f} entries), "
            f"{gap:.0f}% more than {by_day.idxmin()}, the quietest ({by_day.min():.0f})."
        )
    by_type = daily.groupby('Day_Type')['Entry_Count'].mean()
    if {'Weekday', 'Weekend'} <= set(by_type.index):
        diff = (by_type['Weekend'] - by_type['Weekday']) / by_type['Weekday'] * 100
        more_or_fewer = "more" if diff >= 0 else "fewer"
        insights.append(
            f"**A typical weekend day sees {abs(diff):.0f}% {more_or_fewer} customers** than a weekday "
            f"({by_type['Weekend']:.0f} vs {by_type['Weekday']:.0f} entries)."
        )

    text = (f"**Customers stay {df['Dwell_Time_Min'].mean():.1f} minutes on average** "
            f"(median {df['Dwell_Time_Min'].median():.0f}).")
    dwell_by_type = df.groupby('Day_Type')['Dwell_Time_Min'].mean()
    if len(dwell_by_type) == 2:
        dwell_gap = dwell_by_type['Weekend'] - dwell_by_type['Weekday']
        if abs(dwell_gap) < 1:
            text += " Dwell time is almost identical on weekdays and weekends."
        else:
            text += f" Weekend visits last {abs(dwell_gap):.1f} min {'longer' if dwell_gap > 0 else 'shorter'}."
    insights.append(text)

    stores = store_summary(df)
    if len(stores) > 1:
        top = stores.loc[stores['Total_Entries'].idxmax()]
        low = stores.loc[stores['Total_Entries'].idxmin()]
        lead = (top['Total_Entries'] - low['Total_Entries']) / low['Total_Entries'] * 100
        insights.append(
            f"**Store {top['Store_ID']} draws the most footfall** "
            f"({top['Total_Entries'] / total * 100:.1f}% of entries), {lead:.1f}% ahead of Store {low['Store_ID']}."
        )

    change = _period_change_pct(daily.groupby('Date')['Entry_Count'].sum().sort_index(), how="sum")
    if change is not None:
        higher_or_lower = "higher" if change >= 0 else "lower"
        insights.append(
            f"**Footfall over the last 7 days is {abs(change):.1f}% {higher_or_lower}** than the 7 days before."
        )
    return insights


# ------------------------------------------------------------ Part 3: anomalies
def detect_anomalies(df, multiplier=2.0, min_days_per_group=8):
    """Flag days whose footfall is unusual compared with similar days.

    Each day is compared with other days of the same type (weekday or weekend),
    so normal weekend peaks are not flagged. A day is an anomaly when its
    z-score is beyond +/- `multiplier` standard deviations. Groups with fewer
    than `min_days_per_group` days are never flagged.
    """
    daily = df.groupby(['Date', 'Day_Type'])['Entry_Count'].sum().reset_index(name='Entries')
    group = daily.groupby('Day_Type')['Entries']
    daily['Expected'] = group.transform('mean')
    daily['Std'] = group.transform('std')
    daily['Days_In_Group'] = group.transform('count')
    daily['Z_Score'] = ((daily['Entries'] - daily['Expected']) / daily['Std']).fillna(0.0)
    enough_data = (daily['Days_In_Group'] >= min_days_per_group) & (daily['Std'] > 0)
    daily['Is_Anomaly'] = enough_data & (daily['Z_Score'].abs() > multiplier)
    daily['Direction'] = daily['Z_Score'].apply(lambda z: 'High' if z > 0 else 'Low')
    daily['Day_Name'] = daily['Date'].dt.day_name()
    return daily.sort_values('Date').reset_index(drop=True)


# ----------------------------------------------------------- Part 3: deep dive
def hour_profile(df):
    """Total entries and average dwell time for each hour of the day."""
    return df.groupby('Hour').agg(
        Total_Entries=('Entry_Count', 'sum'),
        Avg_Dwell=('Dwell_Time_Min', 'mean'),
    ).reset_index()


# ----------------------------------------------------------- Part 3: comparison
def segment_summary(df):
    """Headline numbers for one segment (a store or a date range) used in comparisons."""
    n_days = max(int(df['Date'].nunique()), 1)
    hourly = df.groupby('Hour')['Entry_Count'].sum()
    total = float(df['Entry_Count'].sum())
    return {
        "total": int(total),
        "days": n_days,
        "avg_per_day": total / n_days,
        "avg_dwell": float(df['Dwell_Time_Min'].mean()),
        "busiest_hour": int(hourly.idxmax()),
        "hourly_avg_per_day": hourly / n_days,
    }


# ----------------------------------------------------------- Part 3: staffing
def staffing_requirements(df, customers_per_staff):
    """Staff needed in each hour so that no one serves more than `customers_per_staff` customers."""
    n_days = max(int(df['Date'].nunique()), 1)
    hourly = hourly_summary(df)
    hourly['Avg_Entries_Per_Day'] = hourly['Total_Entries'] / n_days
    hourly['Required_Staff'] = hourly['Avg_Entries_Per_Day'].apply(
        lambda entries: max(1, math.ceil(entries / customers_per_staff))
    )
    return build_staffing_bands(hourly)


def evaluate_roster(requirement, staff, cost_per_staff_hour):
    """Compare a flat roster of `staff` people in every hour with the required staffing."""
    required = requirement['Required_Staff']
    return {
        "short_hours": int((required > staff).sum()),
        "balanced_hours": int((required == staff).sum()),
        "over_hours": int((required < staff).sum()),
        "staff_hours_short": int((required - staff).clip(lower=0).sum()),
        "staff_hours_excess": int((staff - required).clip(lower=0).sum()),
        "current_cost": int(staff * len(requirement) * cost_per_staff_hour),
        "recommended_cost": int(required.sum() * cost_per_staff_hour),
    }