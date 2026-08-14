import json
import pandas as pd
from pathlib import Path

raw_folder = Path("data/historical/raw")
output_file = Path("data/historical/processed/epl_historical.csv")

mapping_file = Path("data/team_name_mapping.json")

with open(mapping_file, "r", encoding="utf-8") as file:
    team_mapping = json.load(file)

files = sorted(raw_folder.glob("epl_*.csv"))

all_seasons = []

for file in files:
    df = pd.read_csv(file)

    season = file.stem.replace("epl_", "").replace("_", "/")

    df = df[
        ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]
    ].copy()

    df["Season"] = season

    all_seasons.append(df)

combined = pd.concat(all_seasons, ignore_index=True)

teams = set(combined["HomeTeam"]) | set(combined["AwayTeam"])

missing_teams = teams - set(team_mapping.keys())

if missing_teams:
    raise ValueError(f"Missing team mappings: {sorted(missing_teams)}")

combined["HomeTeam"] = combined["HomeTeam"].map(team_mapping)
combined["AwayTeam"] = combined["AwayTeam"].map(team_mapping)

combined["Date"] = pd.to_datetime(
    combined["Date"],
    dayfirst=True
)

combined = combined.sort_values("Date").reset_index(drop=True)

combined.to_csv(output_file, index=False)

print("Historical dataset created successfully!")
print("Total matches:", len(combined))
print("Saved to:", output_file)