# Retail Store Footfall and Peak Hours Analysis

Cronus Consultants | Data Analytics internship project

An analytics toolkit that turns raw store-entry records into staffing decisions. It cleans the data,
finds peak and quiet hours, compares weekdays with weekends and stores, and presents everything in an
interactive dashboard. Anyone can also upload their own CSV and get the same analysis.

**Live app:** _add the Streamlit link here after deployment_

## What it does

- Cleans raw footfall records (duplicates, missing values, impossible dwell times, wrong time order)
- Calculates KPIs: total footfall, average and median dwell time, busiest and quietest hours and days
- Splits hours into Low / Normal / Peak traffic bands to guide staffing
- Draws 9 charts with Matplotlib and Seaborn, including a day x hour heatmap
- Exports a Power BI-ready Excel workbook (cleaned data plus summary tables)
- Runs an interactive dashboard with filters, auto-generated insights, anomaly detection, a click-to-explore
  chart, a side-by-side comparison and a what-if staffing simulator

## Dashboard pages

| Page | Contents |
|---|---|
| Overview | Headline metric cards, key insights, daily trend, day x hour heatmap, store and dwell-time charts |
| Deep Dive | Click-to-explore hour chart, anomaly detection, comparison of two stores or two date ranges |
| Staffing Tool | What-if simulator: required staff per hour against a roster you choose, with cost per day |
| Data & Export | Data cleaning summary and a preview of the records |

The sidebar lets you switch between the sample dataset and your own CSV, filter by date range, store, day type
and hour, download the Excel workbook, and open the project documentation.

### Using your own CSV

Upload a CSV with these columns (up to 200,000 rows):

| Column | Example |
|---|---|
| Visit_ID | V000001 |
| Date | 2026-07-01 |
| Entry_Time | 09:08:00 |
| Exit_Time | 09:40:00 |
| Store_ID | S01 |
| Entry_Count | 1 |
| Dwell_Time_Min | 32 |

A sample file in this format can be downloaded from the upload screen.

## Method

- **Cleaning:** drop duplicate `Visit_ID`s, fill missing `Entry_Count` with 1, remove rows with a dwell time outside
  0 to 720 minutes or a non-positive `Entry_Count`, remove rows where exit is before entry.
- **Features:** `Datetime`, `Hour`, `Day_Name`, `Day_Type` (Weekday or Weekend), `Month`.
- **Traffic bands:** the hourly totals are split into three equal-width ranges (Low, Normal, Peak).
- **Anomalies:** each day is compared with other days of the same type (weekday or weekend) and flagged when its
  z-score is beyond the chosen number of standard deviations (default 2).
- **Staffing model:** required staff in an hour = average entries per day in that hour divided by the customers one
  person can serve per hour, rounded up. The defaults (12 customers per staff per hour, 200 per staff-hour) are
  adjustable assumptions, not measured values.

## Sample data

`data/raw/retail_footfall.csv` is a simulated sample: 22,430 records for 3 stores from 1 July to 29 August 2026.
It contains a few deliberate data-quality issues so the cleaning step has real work to do. After cleaning, 22,298
records remain. In this sample the busiest hour is 19:00 (14.8% of entries) and Saturday has the highest total footfall.

## Project structure

```
projj/
├── app.py                    Streamlit entry point: sidebar, filters and page navigation
├── main.py                   Command-line pipeline: load, clean, analyze, chart, export
├── config.py                 Paths, column names and constants
├── requirements.txt
├── .streamlit/config.toml    Dashboard theme
├── data/
│   ├── raw/                  Input CSV
│   └── processed/            Cleaned dataset written by the pipeline
├── docs/                     Project documentation PDF
├── outputs/
│   ├── figures/              Charts (PNG)
│   ├── powerbi/              Power BI-ready Excel and CSV
│   └── reports/
├── src/
│   ├── data_loader.py        Load and validate the input
│   ├── preprocessing.py      Time features and cleaning
│   ├── analysis.py           KPIs, summaries, insights, anomalies, staffing model
│   ├── visualization.py      Matplotlib and Seaborn charts
│   ├── chart_options.py      Interactive chart definitions for the dashboard
│   ├── dashboard_sections.py Dashboard sections
│   ├── dashboard_extras.py   Welcome screen, Excel download, documentation viewer
│   ├── powerbi_export.py     Power BI export
│   ├── report_generator.py   Optional PDF report builder (not part of the default pipeline)
│   └── utils.py              Shared formatting helpers
└── views/                    One script per dashboard page
```

## Setup

Requires Python 3.11 or newer.

```powershell
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

## Run

Pipeline (cleans the data, writes `data/processed/`, `outputs/figures/` and `outputs/powerbi/`):

```powershell
python main.py
```

Dashboard:

```powershell
streamlit run app.py
```

## Tech stack

Python, pandas, NumPy, Matplotlib, Seaborn, Streamlit, streamlit-echarts (Apache ECharts), openpyxl, ReportLab.

## Team

Cronus Consultants: Kumar Aditya, Priyanshu Raj, Jit Biswas, Aayush Kumar Purve.