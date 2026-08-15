import pandas as pd


# Load historical EPL data
file_path = "data/historical/processed/epl_historical.csv"

df = pd.read_csv(file_path)


# Convert match results into league points
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


# Create home-team history
home = df[
    ["Date", "Season", "HomeTeam", "HomePoints"]
].copy()

home.columns = [
    "Date",
    "Season",
    "Team",
    "Points"
]


# Create away-team history
away = df[
    ["Date", "Season", "AwayTeam", "AwayPoints"]
].copy()

away.columns = [
    "Date",
    "Season",
    "Team",
    "Points"
]


# Combine home and away records
team_matches = pd.concat(
    [home, away],
    ignore_index=True
)


# Sort matches chronologically
team_matches = team_matches.sort_values(
    ["Team", "Season", "Date"]
).reset_index(drop=True)


# Calculate points from previous 5 matches
team_matches["Last5Points"] = (
    team_matches
    .groupby(["Team", "Season"])["Points"]
    .transform(
        lambda x: x.shift(1).rolling(5).sum()
    )
)


# Prepare home recent-form data
home_form = team_matches[
    ["Date", "Season", "Team", "Last5Points"]
].rename(columns={
    "Team": "HomeTeam",
    "Last5Points": "HomeLast5Points"
})


# Prepare away recent-form data
away_form = team_matches[
    ["Date", "Season", "Team", "Last5Points"]
].rename(columns={
    "Team": "AwayTeam",
    "Last5Points": "AwayLast5Points"
})


# Merge home recent form into matches
df = df.merge(
    home_form,
    on=["Date", "Season", "HomeTeam"],
    how="left"
)


# Merge away recent form into matches
df = df.merge(
    away_form,
    on=["Date", "Season", "AwayTeam"],
    how="left"
)

# Calculate previous 5 HOME matches points
home_venue = df[
    ["Date", "Season", "HomeTeam", "HomePoints"]
].copy()

home_venue = home_venue.sort_values(
    ["HomeTeam", "Season", "Date"]
).reset_index(drop=True)

home_venue["Last5HomePoints"] = (
    home_venue
    .groupby(["HomeTeam", "Season"])["HomePoints"]
    .transform(
        lambda x: x.shift(1).rolling(5).sum()
    )
)


# Calculate previous 5 AWAY matches points
away_venue = df[
    ["Date", "Season", "AwayTeam", "AwayPoints"]
].copy()

away_venue = away_venue.sort_values(
    ["AwayTeam", "Season", "Date"]
).reset_index(drop=True)

away_venue["Last5AwayPoints"] = (
    away_venue
    .groupby(["AwayTeam", "Season"])["AwayPoints"]
    .transform(
        lambda x: x.shift(1).rolling(5).sum()
    )
)


# Merge home venue form
df = df.merge(
    home_venue[
        ["Date", "Season", "HomeTeam", "Last5HomePoints"]
    ],
    on=["Date", "Season", "HomeTeam"],
    how="left"
)


# Merge away venue form
df = df.merge(
    away_venue[
        ["Date", "Season", "AwayTeam", "Last5AwayPoints"]
    ],
    on=["Date", "Season", "AwayTeam"],
    how="left"
)


# Keep ML feature columns
feature_df = df[
    [
        "Date",
        "Season",
        "HomeTeam",
        "AwayTeam",
        "FTHG",
        "FTAG",
        "FTR",
        "HomeLast5Points",
        "AwayLast5Points",
        "Last5HomePoints",
        "Last5AwayPoints"
    ]
].copy()


# Save feature dataset
output_file = "data/historical/processed/epl_features.csv"

feature_df.to_csv(
    output_file,
    index=False
)

print("Feature dataset created successfully!")
print("Total matches:", len(feature_df))
print("Saved to:", output_file)