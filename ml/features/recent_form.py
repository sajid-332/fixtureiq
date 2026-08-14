import pandas as pd

file_path = "data/historical/processed/epl_historical.csv"

df = pd.read_csv(file_path)

home_points = {
    "H": 3,
    "D": 1,
    "A": 0
}

away_points = {
    "H": 0,
    "D": 1,
    "A": 3
}

df["HomePoints"] = df["FTR"].map(home_points)
df["AwayPoints"] = df["FTR"].map(away_points)

print(
    df[
        [
            "Date",
            "HomeTeam",
            "AwayTeam",
            "FTR",
            "HomePoints",
            "AwayPoints"
        ]
    ].head(10)
)

home = df[
    ["Date", "HomeTeam", "HomePoints"]
].copy()

home.columns = [
    "Date",
    "Team",
    "Points"
]

away = df[
    ["Date", "AwayTeam", "AwayPoints"]
].copy()

away.columns = [
    "Date",
    "Team",
    "Points"
]

team_matches = pd.concat(
    [home, away],
    ignore_index=True
)

team_matches = team_matches.sort_values(
    ["Team", "Date"]
).reset_index(drop=True)

team_matches["Last5Points"] = (
    team_matches
    .groupby("Team")["Points"]
    .transform(
        lambda x: x.shift(1).rolling(5).sum()
    )
)

print("\nLast 5 matches points:")
print(team_matches.head(10))

home_form = team_matches[
    ["Date", "Team", "Last5Points"]
].rename(columns={
    "Team": "HomeTeam",
    "Last5Points": "HomeLast5Points"
})

away_form = team_matches[
    ["Date", "Team", "Last5Points"]
].rename(columns={
    "Team": "AwayTeam",
    "Last5Points": "AwayLast5Points"
})

df = df.merge(
    home_form,
    on=["Date", "HomeTeam"],
    how="left"
)

df = df.merge(
    away_form,
    on=["Date", "AwayTeam"],
    how="left"
)

print("\nMatches with last 5 points:")
print(
    df[
        [
            "Date",
            "HomeTeam",
            "AwayTeam",
            "HomeLast5Points",
            "AwayLast5Points"
        ]
    ].head(20)
)

