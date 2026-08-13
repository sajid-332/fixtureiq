import pandas as pd
from pathlib import Path

raw_folder = Path("data/historical/raw")

files = sorted(raw_folder.glob("epl_*.csv"))

required_columns = [
    "Date",
    "HomeTeam",
    "AwayTeam",
    "FTHG",
    "FTAG",
    "FTR"
]

for file in files:
    df = pd.read_csv(file)

    print(f"\n--- {file.name} ---")
    print("Matches:", len(df))

    print("Missing values:")
    print(df[required_columns].isnull().sum().sum())

    print("Duplicate rows:")
    print(df.duplicated().sum())