from config import RAW_DATA_PATH, PROCESSED_DATA_PATH
from src.data_loader import load_raw_data, validate_schema, inspect_data
from src.preprocessing import build_datetime_features, clean_data, save_processed_data
from src.analysis import (
    calculate_kpis, hourly_summary, daily_summary,
    weekday_vs_weekend, store_summary, build_staffing_bands
)
from src.visualization import generate_all_visuals
# from src.report_generator import generate_report
from src.powerbi_export import export_for_powerbi

# ---------------- Load & Validate ----------------
df = load_raw_data(RAW_DATA_PATH)
validate_schema(df)
inspect_data(df)

# ---------------- Preprocess & Clean ----------------
df = build_datetime_features(df)
df, cleaning_stats = clean_data(df)
save_processed_data(df, PROCESSED_DATA_PATH)

# ---------------- Analysis ----------------
kpis = calculate_kpis(df)
print("\n--- KPIs ---")
print(kpis)

hourly = hourly_summary(df)
hourly = build_staffing_bands(hourly)
print("\n--- Hourly Summary with Staffing Bands ---")
print(hourly)

print("\n--- Daily Summary ---")
print(daily_summary(df))

print("\n--- Weekday vs Weekend ---")
print(weekday_vs_weekend(df))

print("\n--- Store Summary ---")
print(store_summary(df))

# ---------------- Visualizations ----------------
generate_all_visuals(df)

# ---------------- PDF Report ----------------
# generate_report(
#     df=df,
#     kpis=kpis,
#     hourly_df=hourly,
#     daily_df=daily_summary(df),
#     weekday_weekend_df=weekday_vs_weekend(df),
#     store_df=store_summary(df),
#     cleaning_stats=cleaning_stats,
#     figures_dir="outputs/figures/",
#     output_path="outputs/reports/footfall_report.pdf"
# )

# export_for_powerbi(
#     df=df,
#     hourly_df=hourly,
#     daily_df=daily_summary(df),
#     weekday_weekend_df=weekday_vs_weekend(df),
#     store_df=store_summary(df),
# )

# print("\nPipeline complete. Cleaned file saved.")

