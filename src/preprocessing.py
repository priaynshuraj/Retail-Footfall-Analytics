import pandas as pd

def build_datetime_features(df):
    """Create Datetime, Hour, Day_Name, Day_Type, Month columns."""
    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Entry_Time'])
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Datetime').reset_index(drop=True)
    df['Hour'] = df['Datetime'].dt.hour
    df['Day_Name'] = df['Datetime'].dt.day_name()
    df['Day_Type'] = df['Datetime'].dt.dayofweek.apply(lambda x: 'Weekday' if x < 5 else 'Weekend')
    df['Month'] = df['Datetime'].dt.month_name()
    return df

def clean_data(df):
    """Remove duplicates, nulls, invalid dwell times. Returns (df, stats_dict)."""
    stats = {}
    stats['initial_rows'] = len(df)

    before = len(df)
    df = df.drop_duplicates(subset='Visit_ID')
    stats['duplicates_removed'] = before - len(df)

    stats['missing_entry_count_filled'] = int(df['Entry_Count'].isnull().sum())
    df['Entry_Count'] = df['Entry_Count'].fillna(1)

    before = len(df)
    df = df[(df['Dwell_Time_Min'] >= 0) & (df['Dwell_Time_Min'] <= 720)]
    df = df[df['Entry_Count'] > 0]
    stats['invalid_dwell_or_count_removed'] = before - len(df)

    before = len(df)
    exit_dt = pd.to_datetime(df['Date'].dt.strftime('%Y-%m-%d') + ' ' + df['Exit_Time'])
    entry_dt = pd.to_datetime(df['Date'].dt.strftime('%Y-%m-%d') + ' ' + df['Entry_Time'])
    df = df[exit_dt >= entry_dt]
    stats['invalid_time_order_removed'] = before - len(df)

    stats['final_rows'] = len(df)
    print(f"Cleaning stats: {stats}")
    return df, stats

def save_processed_data(df, path):
    """Write the cleaned dataset to a CSV file."""
    df.to_csv(path, index=False)