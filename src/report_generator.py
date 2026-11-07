import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)
from reportlab.lib.units import inch

# =========================================================
# STYLES
# =========================================================
styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "TitleStyle", parent=styles["Title"],
    alignment=TA_CENTER, fontSize=22, spaceAfter=20
)
heading_style = ParagraphStyle(
    "HeadingStyle", parent=styles["Heading2"],
    fontSize=16, spaceBefore=15, spaceAfter=10
)
normal_style = ParagraphStyle(
    "NormalStyle", parent=styles["BodyText"],
    fontSize=10, leading=15
)
subtitle_style = ParagraphStyle(
    "Subtitle", parent=normal_style,
    alignment=TA_CENTER, fontSize=12
)
footer_style = ParagraphStyle(
    "Footer", parent=normal_style,
    alignment=TA_CENTER, fontSize=9
)


def _make_table(data, col_widths):
    """Build a styled reportlab Table from a list-of-lists."""
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def generate_report(df, kpis, hourly_df, daily_df, weekday_weekend_df, store_df,
                     cleaning_stats, figures_dir, output_path):
    """Build the full PDF report end to end."""
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    story = []

    # ============================================================
    # COVER PAGE
    # ============================================================
    story.append(Paragraph("RETAIL STORE FOOTFALL & PEAK HOURS ANALYSIS", title_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("Python | Pandas | Matplotlib | Seaborn | ReportLab", subtitle_style))
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        "This report analyzes retail store customer footfall data to identify "
        "peak and off-peak hours, compare weekday vs weekend traffic, and "
        "provide data-driven staffing recommendations for store management.",
        normal_style
    ))
    story.append(Spacer(1, 25))

    story.append(Paragraph("Dataset Overview", heading_style))
    overview_text = f"""
    Raw Records Collected: {cleaning_stats['initial_rows']:,}<br/>
    Records After Cleaning: {cleaning_stats['final_rows']:,}<br/>
    Stores Covered: {store_df['Store_ID'].nunique()}<br/>
    Metrics Tracked: Entry Time, Exit Time, Dwell Time, Store ID<br/>
    Analysis Granularity: Hourly, Daily, Weekly, Store-level
    """
    story.append(Paragraph(overview_text, normal_style))
    story.append(Spacer(1, 25))

    story.append(Paragraph("Objectives", heading_style))
    objectives_text = """
    1. Identify the busiest and quietest hours of store operation<br/>
    2. Compare weekday vs weekend customer traffic patterns<br/>
    3. Analyze customer dwell-time behavior across the store<br/>
    4. Compare footfall performance across multiple store locations<br/>
    5. Generate data-driven staffing recommendations by hour
    """
    story.append(Paragraph(objectives_text, normal_style))
    story.append(PageBreak())

    # ============================================================
    # 1. DATA CLEANING SUMMARY
    # ============================================================
    story.append(Paragraph("1. Data Cleaning Summary", heading_style))
    story.append(Paragraph(
        "Before analysis, the raw dataset was validated and cleaned using the following checks:",
        normal_style
    ))
    story.append(Spacer(1, 10))
    cleaning_table_data = [
        ["Check Performed", "Rows Affected"],
        ["Duplicate Visit_ID records removed", f"{cleaning_stats['duplicates_removed']:,}"],
        ["Missing Entry_Count values filled", f"{cleaning_stats['missing_entry_count_filled']:,}"],
        ["Invalid dwell time / entry count removed", f"{cleaning_stats['invalid_dwell_or_count_removed']:,}"],
        ["Invalid time-order (Exit before Entry) removed", f"{cleaning_stats['invalid_time_order_removed']:,}"],
        ["Final clean record count", f"{cleaning_stats['final_rows']:,}"],
    ]
    story.append(_make_table(cleaning_table_data, [3.5 * inch, 2 * inch]))
    story.append(PageBreak())

    # ============================================================
    # 2. EXECUTIVE SUMMARY
    # ============================================================
    story.append(Paragraph("2. Executive Summary", heading_style))
    summary_text = f"""
    Total Customer Entries: {kpis['Total_Entries']:,}<br/>
    Average Dwell Time: {kpis['Avg_Dwell_Time_Min']} minutes<br/>
    Median Dwell Time: {kpis['Median_Dwell_Time_Min']} minutes<br/>
    Busiest Hour: {kpis['Busiest_Hour']}:00<br/>
    Quietest Hour: {kpis['Quietest_Hour']}:00<br/>
    Busiest Day: {kpis['Busiest_Day']}
    """
    story.append(Paragraph(summary_text, normal_style))
    story.append(Spacer(1, 20))

    # ============================================================
    # 3. HOURLY FOOTFALL & STAFFING
    # ============================================================
    story.append(Paragraph("3. Hourly Footfall & Staffing Recommendation", heading_style))
    hourly_table_data = [["Hour", "Total Entries", "Traffic Band"]]
    for _, row in hourly_df.iterrows():
        hourly_table_data.append([str(int(row['Hour'])), f"{row['Total_Entries']:,.0f}", str(row['Traffic_Band'])])
    story.append(_make_table(hourly_table_data, [1.5 * inch, 2 * inch, 2 * inch]))
    story.append(Spacer(1, 20))
    story.append(Image(os.path.join(figures_dir, "hourly_trend.png"), width=6.5 * inch, height=4 * inch))
    story.append(PageBreak())

    # ============================================================
    # 4. DAY OF WEEK
    # ============================================================
    story.append(Paragraph("4. Footfall by Day of Week", heading_style))
    day_table_data = [["Day", "Total Entries"]]
    for _, row in daily_df.iterrows():
        day_table_data.append([str(row['Day_Name']), f"{row['Total_Entries']:,.0f}"])
    story.append(_make_table(day_table_data, [3 * inch, 2 * inch]))
    story.append(Spacer(1, 20))
    story.append(Image(os.path.join(figures_dir, "day_of_week.png"), width=6.5 * inch, height=4 * inch))
    story.append(PageBreak())

    # ============================================================
    # 5. WEEKDAY VS WEEKEND
    # ============================================================
    story.append(Paragraph("5. Weekday vs Weekend Comparison", heading_style))
    ww_table_data = [["Day Type", "Total Entries"]]
    for _, row in weekday_weekend_df.iterrows():
        ww_table_data.append([str(row['Day_Type']), f"{row['Total_Entries']:,.0f}"])
    story.append(_make_table(ww_table_data, [3 * inch, 2 * inch]))
    story.append(Spacer(1, 20))
    story.append(Image(os.path.join(figures_dir, "weekday_vs_weekend.png"), width=6.5 * inch, height=4 * inch))
    story.append(PageBreak())

    # ============================================================
    # 6. STORE COMPARISON
    # ============================================================
    story.append(Paragraph("6. Store-wise Comparison", heading_style))
    store_table_data = [["Store ID", "Total Entries", "Avg Dwell Time (min)"]]
    for _, row in store_df.iterrows():
        store_table_data.append([str(row['Store_ID']), f"{row['Total_Entries']:,.0f}", f"{row['Avg_Dwell_Time']:.2f}"])
    story.append(_make_table(store_table_data, [2 * inch, 2 * inch, 2 * inch]))
    story.append(Spacer(1, 20))
    story.append(Image(os.path.join(figures_dir, "store_comparison.png"), width=6.5 * inch, height=4 * inch))
    story.append(PageBreak())

    # ============================================================
    # 7. DAY x HOUR HEATMAP  (+ Top 5 table)
    # ============================================================
    story.append(Paragraph("7. Day x Hour Heatmap", heading_style))
    story.append(Paragraph(
        "This heatmap highlights exactly which day-hour combinations see the highest footfall. "
        "The table below lists the top 5 busiest day-hour combinations.",
        normal_style
    ))
    story.append(Spacer(1, 10))

    pivot = df.pivot_table(index='Day_Name', columns='Hour', values='Entry_Count', aggfunc='sum')
    stacked = pivot.stack().reset_index()
    stacked.columns = ['Day_Name', 'Hour', 'Total_Entries']
    top5 = stacked.sort_values('Total_Entries', ascending=False).head(5)

    top5_table_data = [["Day", "Hour", "Total Entries"]]
    for _, row in top5.iterrows():
        top5_table_data.append([str(row['Day_Name']), f"{int(row['Hour'])}:00", f"{row['Total_Entries']:,.0f}"])
    story.append(_make_table(top5_table_data, [2.5 * inch, 1.5 * inch, 2 * inch]))
    story.append(Spacer(1, 15))
    story.append(Image(os.path.join(figures_dir, "day_hour_heatmap.png"), width=7 * inch, height=4 * inch))
    story.append(PageBreak())

    # ============================================================
    # 8. DWELL TIME ANALYSIS  (+ summary stats table)
    # ============================================================
    story.append(Paragraph("8. Dwell Time Analysis", heading_style))
    story.append(Paragraph("Summary statistics by day type:", normal_style))
    story.append(Spacer(1, 10))

    dwell_stats = df.groupby('Day_Type')['Dwell_Time_Min'].agg(['mean', 'median', 'min', 'max', 'std']).reset_index()
    dwell_table_data = [["Day Type", "Mean", "Median", "Min", "Max", "Std Dev"]]
    for _, row in dwell_stats.iterrows():
        dwell_table_data.append([
            str(row['Day_Type']), f"{row['mean']:.2f}", f"{row['median']:.1f}",
            f"{row['min']:.0f}", f"{row['max']:.0f}", f"{row['std']:.2f}"
        ])
    story.append(_make_table(dwell_table_data, [1.3 * inch, 1 * inch, 1 * inch, 0.8 * inch, 0.8 * inch, 1 * inch]))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Distribution of how long customers stay in-store:", normal_style))
    story.append(Spacer(1, 10))
    story.append(Image(os.path.join(figures_dir, "dwell_time_distribution.png"), width=6.5 * inch, height=4 * inch))
    story.append(Spacer(1, 15))
    story.append(PageBreak())
    story.append(Paragraph("Dwell Time: Weekday vs Weekend Spread", heading_style))
    story.append(Paragraph(
        "The boxplot below compares the quartile spread of dwell time between "
        "weekdays and weekends. Key quartile values are summarized first:",
        normal_style
    ))
    story.append(Spacer(1, 10))

    quartile_data = [["Day Type", "25th Percentile", "Median (50th)", "75th Percentile"]]
    for day_type in ['Weekday', 'Weekend']:
        subset = df[df['Day_Type'] == day_type]['Dwell_Time_Min']
        quartile_data.append([
            day_type,
            f"{subset.quantile(0.25):.1f}",
            f"{subset.quantile(0.50):.1f}",
            f"{subset.quantile(0.75):.1f}"
        ])
    story.append(_make_table(quartile_data, [1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch]))
    story.append(Spacer(1, 15))
    story.append(Image(os.path.join(figures_dir, "dwell_time_boxplot.png"), width=6 * inch, height=4 * inch))
    story.append(PageBreak())

    # ============================================================
    # 9. PEAK HOURS BY STORE  (+ per-store peak table)
    # ============================================================
    story.append(Paragraph("9. Peak Hours by Store", heading_style))
    story.append(Paragraph("Each store's single busiest hour and its footfall:", normal_style))
    story.append(Spacer(1, 10))

    store_peak = df.groupby(['Store_ID', 'Hour'])['Entry_Count'].sum().reset_index()
    peak_rows = store_peak.loc[store_peak.groupby('Store_ID')['Entry_Count'].idxmax()]
    peak_table_data = [["Store ID", "Peak Hour", "Entries at Peak"]]
    for _, row in peak_rows.iterrows():
        peak_table_data.append([str(row['Store_ID']), f"{int(row['Hour'])}:00", f"{row['Entry_Count']:,.0f}"])
    story.append(_make_table(peak_table_data, [2 * inch, 2 * inch, 2 * inch]))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Each store's full hourly footfall pattern, compared side by side:", normal_style))
    story.append(Spacer(1, 10))
    story.append(Image(os.path.join(figures_dir, "peak_hours_by_store.png"), width=7 * inch, height=4 * inch))
    story.append(PageBreak())

    # ============================================================
    # 10. DAILY TREND  (+ top/bottom days table)
    # ============================================================
    story.append(Paragraph("10. Daily Footfall Trend", heading_style))
    story.append(Paragraph("Top 3 busiest and bottom 3 quietest days in the dataset:", normal_style))
    story.append(Spacer(1, 10))

    daily_totals = df.groupby(df['Datetime'].dt.date)['Entry_Count'].sum().reset_index()
    daily_totals.columns = ['Date', 'Total_Entries']
    top3 = daily_totals.sort_values('Total_Entries', ascending=False).head(3)
    bottom3 = daily_totals.sort_values('Total_Entries', ascending=True).head(3)

    trend_table_data = [["Date", "Total Entries", "Type"]]
    for _, row in top3.iterrows():
        trend_table_data.append([str(row['Date']), f"{row['Total_Entries']:,.0f}", "Busiest"])
    for _, row in bottom3.iterrows():
        trend_table_data.append([str(row['Date']), f"{row['Total_Entries']:,.0f}", "Quietest"])
    story.append(_make_table(trend_table_data, [2 * inch, 2 * inch, 2 * inch]))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Footfall trend across the full dataset period:", normal_style))
    story.append(Spacer(1, 10))
    story.append(Image(os.path.join(figures_dir, "daily_trend.png"), width=7 * inch, height=4 * inch))
    story.append(PageBreak())

    # ============================================================
    # 11. KEY INSIGHTS & STAFFING RECOMMENDATION
    # ============================================================
    story.append(Paragraph("11. Key Insights & Staffing Recommendation", heading_style))
    insights = f"""
    <b>Busiest Hour:</b> {kpis['Busiest_Hour']}:00<br/><br/>
    <b>Quietest Hour:</b> {kpis['Quietest_Hour']}:00<br/><br/>
    <b>Busiest Day:</b> {kpis['Busiest_Day']}<br/><br/>
    <b>Weekend vs Weekday Gap:</b> Weekend traffic is significantly higher per day
    than weekday traffic, indicating customer behavior shifts notably on
    Saturdays and Sundays.<br/><br/>
    <b>Dwell Time Behavior:</b> Average dwell time remains consistent at around
    {kpis['Avg_Dwell_Time_Min']} minutes regardless of day type, suggesting that
    while visitor volume changes, individual shopping duration does not.<br/><br/>
    <b>Store Performance:</b> All three stores show broadly similar footfall,
    with no single location significantly outperforming the others.<br/><br/>
    <b>Recommendation:</b> Increase staffing during hours flagged as "Peak" in
    the staffing table (Section 3), particularly between 6 PM and 8 PM on
    weekends, to reduce customer wait times and improve service quality.
    Conversely, staffing can be reduced during "Low" traffic hours (9 AM-11 AM,
    9 PM) to optimize labor costs.
    """
    story.append(Paragraph(insights, normal_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "<i>Report generated using Python, Pandas, Matplotlib, Seaborn, and ReportLab.</i>",
        footer_style
    ))

    # ============================================================
    # BUILD
    # ============================================================
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.build(story)
    print("\n====================================")
    print("PDF REPORT CREATED SUCCESSFULLY")
    print("====================================")
    print(f"File: {output_path}")