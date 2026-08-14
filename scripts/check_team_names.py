import pandas as pd

file_path = "data/historical/processed/epl_historical.csv"

df = pd.read_csv(file_path)

all_teams = sorted(set(df["HomeTeam"]) | set(df["AwayTeam"]))

print("Total unique teams:", len(all_teams))

print("\nStandardized team names:")

for team in all_teams:
    print(team)