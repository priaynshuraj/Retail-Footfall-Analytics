RAW_DATA_PATH = "data/raw/retail_footfall.csv"
PROCESSED_DATA_PATH = "data/processed/retail_footfall_cleaned.csv"

REQUIRED_COLUMNS = ["Visit_ID", "Date", "Entry_Time", "Exit_Time", "Store_ID", "Entry_Count", "Dwell_Time_Min"]

FIGURES_DIR = "outputs/figures/"

MAX_UPLOAD_ROWS = 200_000


# Dashboard defaults
ANOMALY_STD_DEV_MULTIPLIER = 2.0
DEFAULT_CUSTOMERS_PER_STAFF = 12
DEFAULT_COST_PER_STAFF_HOUR = 200


# Welcome screen and documentation
TEAM_NAME = "Cronus Consultants"
PROJECT_TITLE = "Footfall Analysis Project"
TEAM_MEMBERS = [
    ("Kumar Aditya", "430124010142"),
    ("Priyanshu Raj", "430124010172"),
    ("Jit Biswas", "430124010135"),
    ("Aayush Kumar Purve", "430124010191"),
]
DOCUMENTATION_PDF_PATH = "docs/Retail_Footfall_Report.pdf"