import pandas as pd
from config import REQUIRED_COLUMNS

def load_raw_data(path):
    """Load raw CSV into a DataFrame."""
    df = pd.read_csv(path)
    return df

def validate_schema(df):
    """Check all required columns exist."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    return True

def inspect_data(df):
    """Print shape, dtypes, missing values."""
    print("Shape:", df.shape)
    print(df.dtypes)
    print(df.isnull().sum())