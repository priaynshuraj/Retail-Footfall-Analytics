"""Export the cleaned data and summary tables in Power BI-ready formats."""
import io
import os

import pandas as pd

_GUIDE_TEXT = (
    "POWER BI IMPORT GUIDE\n"
    "=====================\n"
    "File: retail_footfall_powerbi.xlsx\n\n"
    "Sheet -> Suggested visual\n"
    "-------------------------\n"
    "Cleaned_Data        -> Main fact table (use for slicers: Store_ID, Day_Type, Date)\n"
    "Hourly_Summary      -> Line chart of footfall by hour + staffing band\n"
    "Daily_Summary       -> Column chart of footfall by day of week\n"
    "Weekday_vs_Weekend  -> Clustered column / donut chart\n"
    "Store_Summary       -> Store comparison (entries and avg dwell time)\n\n"
    "Steps: Power BI Desktop -> Get Data -> Excel Workbook -> select all sheets -> Load.\n"
)


def _autofit_columns(worksheet):
    """Set each column's width to fit its longest value (capped at 40 characters)."""
    for column_cells in worksheet.columns:
        longest = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
        worksheet.column_dimensions[column_cells[0].column_letter].width = min(longest + 3, 40)


def build_powerbi_excel(df, hourly_df, daily_df, weekday_weekend_df, store_df):
    """Return the Power BI-ready workbook as bytes (nothing is written to disk)."""
    data = df.copy()
    data['Date'] = data['Date'].dt.date
    hourly = hourly_df.copy()
    hourly['Traffic_Band'] = hourly['Traffic_Band'].astype(str)
    stores = store_df.copy()
    stores['Avg_Dwell_Time'] = stores['Avg_Dwell_Time'].round(2)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        data.to_excel(writer, sheet_name="Cleaned_Data", index=False)
        hourly.to_excel(writer, sheet_name="Hourly_Summary", index=False)
        daily_df.to_excel(writer, sheet_name="Daily_Summary", index=False)
        weekday_weekend_df.to_excel(writer, sheet_name="Weekday_vs_Weekend", index=False)
        stores.to_excel(writer, sheet_name="Store_Summary", index=False)
        for sheet in writer.sheets.values():
            _autofit_columns(sheet)
    return buffer.getvalue()


def export_for_powerbi(df, hourly_df, daily_df, weekday_weekend_df, store_df,
                       output_dir="outputs/powerbi/"):
    """Write the Excel workbook, a flat CSV and an import guide to `output_dir`."""
    os.makedirs(output_dir, exist_ok=True)

    xlsx_path = os.path.join(output_dir, "retail_footfall_powerbi.xlsx")
    with open(xlsx_path, "wb") as file:
        file.write(build_powerbi_excel(df, hourly_df, daily_df, weekday_weekend_df, store_df))
    print(f"Saved: {xlsx_path}")

    csv_path = os.path.join(output_dir, "retail_footfall_powerbi.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved: {csv_path}")

    guide_path = os.path.join(output_dir, "README_PowerBI.txt")
    with open(guide_path, "w", encoding="utf-8") as file:
        file.write(_GUIDE_TEXT)
    print(f"Saved: {guide_path}")