import matplotlib
matplotlib.use("Agg")  # prevents GUI window errors, safe for scripts
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os

sns.set_style("whitegrid")

def _save(fig, filename, output_dir):
    """Helper: save a figure and close it to free memory."""
    path = os.path.join(output_dir, filename)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path}")

def plot_hourly_trend(df, output_dir):
    """Line chart: total entries per hour of day."""
    hourly = df.groupby('Hour')['Entry_Count'].sum()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(hourly.index, hourly.values, marker='o', color='#2563eb')
    ax.set_title("Footfall by Hour of Day")
    ax.set_xlabel("Hour")
    ax.set_ylabel("Total Entries")
    _save(fig, "hourly_trend.png", output_dir)

def plot_daily_trend(df, output_dir):
    """Line chart: total entries per calendar day across the dataset."""
    daily = df.groupby(df['Datetime'].dt.date)['Entry_Count'].sum()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(daily.index, daily.values, color='#16a34a')
    ax.set_title("Daily Footfall Trend")
    ax.set_xlabel("Date")
    ax.set_ylabel("Total Entries")
    plt.xticks(rotation=45)
    _save(fig, "daily_trend.png", output_dir)

def plot_day_of_week(df, output_dir):
    """Bar chart: total entries by day name."""
    order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    daily = df.groupby('Day_Name')['Entry_Count'].sum().reindex(order)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(daily.index, daily.values, color='#7c3aed')
    ax.set_title("Footfall by Day of Week")
    ax.set_ylabel("Total Entries")
    plt.xticks(rotation=30)
    _save(fig, "day_of_week.png", output_dir)

def plot_weekday_vs_weekend(df, output_dir):
    """Bar chart: weekday vs weekend total footfall."""
    summary = df.groupby('Day_Type')['Entry_Count'].sum()
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.bar(summary.index, summary.values, color=['#3b82f6', '#f59e0b'])
    ax.set_title("Weekday vs Weekend Footfall")
    ax.set_ylabel("Total Entries")
    _save(fig, "weekday_vs_weekend.png", output_dir)

def plot_store_comparison(df, output_dir):
    """Bar chart: total entries per store."""
    store = df.groupby('Store_ID')['Entry_Count'].sum()
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.bar(store.index, store.values, color='#ef4444')
    ax.set_title("Footfall by Store")
    ax.set_ylabel("Total Entries")
    _save(fig, "store_comparison.png", output_dir)

def plot_day_hour_heatmap(df, output_dir):
    """Heatmap: entries by day of week x hour of day."""
    order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    pivot = df.pivot_table(index='Day_Name', columns='Hour', values='Entry_Count', aggfunc='sum').reindex(order)
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(pivot, cmap="YlOrRd", annot=False, ax=ax)
    ax.set_title("Footfall Heatmap: Day of Week x Hour")
    _save(fig, "day_hour_heatmap.png", output_dir)

def plot_dwell_time_distribution(df, output_dir):
    """Histogram: dwell time distribution."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(df['Dwell_Time_Min'], bins=range(0, 75, 3), color='#06b6d4', edgecolor='black')
    ax.set_title("Dwell Time Distribution")
    ax.set_xlabel("Dwell Time (minutes)")
    ax.set_ylabel("Frequency")
    _save(fig, "dwell_time_distribution.png", output_dir)

def plot_dwell_time_boxplot(df, output_dir):
    """Boxplot: dwell time by weekday vs weekend."""
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.boxplot(data=df, x='Day_Type', y='Dwell_Time_Min', ax=ax)
    ax.set_title("Dwell Time: Weekday vs Weekend")
    _save(fig, "dwell_time_boxplot.png", output_dir)

def plot_peak_hours_by_store(df, output_dir):
    """Grouped bar chart: hourly footfall per store."""
    pivot = df.pivot_table(index='Hour', columns='Store_ID', values='Entry_Count', aggfunc='sum')
    fig, ax = plt.subplots(figsize=(10, 5))
    pivot.plot(kind='bar', ax=ax)
    ax.set_title("Peak Hours by Store")
    ax.set_ylabel("Total Entries")
    _save(fig, "peak_hours_by_store.png", output_dir)

def generate_all_visuals(df, output_dir="outputs/figures/"):
    """Run every chart function in sequence."""
    plot_hourly_trend(df, output_dir)
    plot_daily_trend(df, output_dir)
    plot_day_of_week(df, output_dir)
    plot_weekday_vs_weekend(df, output_dir)
    plot_store_comparison(df, output_dir)
    plot_day_hour_heatmap(df, output_dir)
    plot_dwell_time_distribution(df, output_dir)
    plot_dwell_time_boxplot(df, output_dir)
    plot_peak_hours_by_store(df, output_dir)
    print("\nAll 9 visualizations generated successfully.")