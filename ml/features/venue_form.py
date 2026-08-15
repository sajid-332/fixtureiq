import pandas as pd

file_path = "data/historical/processed/epl_historical.csv"

df = pd.read_csv(file_path)

home_points = {
    "H": 3,
    "D": 1,
    "A": 0
}

df["HomePoints"] = df["FTR"].map(home_points)

home_matches = df[
    ["Date", "Season", "HomeTeam", "HomePoints"]
].copy()

home_matches = home_matches.sort_values(
    ["HomeTeam", "Season", "Date"]
).reset_index(drop=True)

home_matches["Last5HomePoints"] = (
    home_matches
    .groupby(["HomeTeam", "Season"])["HomePoints"]
    .transform(
        lambda x: x.shift(1).rolling(5).sum()
    )
)

print(
    home_matches[
        [
            "Date",
            "Season",
            "HomeTeam",
            "HomePoints",
            "Last5HomePoints"
        ]
    ].head(20)
)

away_points = {
    "H": 0,
    "D": 1,
    "A": 3
}

df["AwayPoints"] = df["FTR"].map(away_points)

away_matches = df[
    ["Date", "Season", "AwayTeam", "AwayPoints"]
].copy()

away_matches = away_matches.sort_values(
    ["AwayTeam", "Season", "Date"]
).reset_index(drop=True)

away_matches["Last5AwayPoints"] = (
    away_matches
    .groupby(["AwayTeam", "Season"])["AwayPoints"]
    .transform(
        lambda x: x.shift(1).rolling(5).sum()
    )
)

print("\nAway venue form:")
print(
    away_matches[
        [
            "Date",
            "Season",
            "AwayTeam",
            "AwayPoints",
            "Last5AwayPoints"
        ]
    ].head(20)
)

home_form = home_matches[
    ["Date", "Season", "HomeTeam", "Last5HomePoints"]
]

away_form = away_matches[
    ["Date", "Season", "AwayTeam", "Last5AwayPoints"]
]

df = df.merge(
    home_form,
    on=["Date", "Season", "HomeTeam"],
    how="left"
)

df = df.merge(
    away_form,
    on=["Date", "Season", "AwayTeam"],
    how="left"
)

print("\nMatches with venue form:")
print(
    df[
        [
            "Date",
            "HomeTeam",
            "AwayTeam",
            "Last5HomePoints",
            "Last5AwayPoints"
        ]
    ].head(30)
)