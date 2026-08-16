import pandas as pd


# Load historical EPL data
file_path = "data/historical/processed/epl_historical.csv"

df = pd.read_csv(file_path)

df["Date"] = pd.to_datetime(df["Date"])


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


# Create home-team records
home = df[
    ["Date", "Season", "HomeTeam", "HomePoints"]
].copy()

home.columns = [
    "Date",
    "Season",
    "Team",
    "Points"
]


# Create away-team records
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


# Sort each team's matches chronologically
team_matches = team_matches.sort_values(
    ["Team", "Season", "Date"]
).reset_index(drop=True)


# Games played BEFORE current match
team_matches["GamesPlayedBefore"] = (
    team_matches
    .groupby(["Team", "Season"])
    .cumcount()
)


# League points BEFORE current match
team_matches["LeaguePointsBefore"] = (
    team_matches
    .groupby(["Team", "Season"])["Points"]
    .transform(
        lambda x: x.shift(1).cumsum()
    )
    .fillna(0)
)


# Season points-per-game BEFORE current match
team_matches["SeasonPPGBefore"] = (
    team_matches["LeaguePointsBefore"]
    / team_matches["GamesPlayedBefore"]
)


# Points from previous 5 matches
team_matches["Last5Points"] = (
    team_matches
    .groupby(["Team", "Season"])["Points"]
    .transform(
        lambda x: x.shift(1).rolling(5).sum()
    )
)


# Recent PPG from previous 5 matches
team_matches["RecentPPG"] = (
    team_matches["Last5Points"] / 5
)


# Momentum:
# recent form compared with season-level form
team_matches["Momentum"] = (
    team_matches["RecentPPG"]
    - team_matches["SeasonPPGBefore"]
)


# Prepare home-team momentum
home_momentum = team_matches[
    ["Date", "Season", "Team", "Momentum"]
].rename(columns={
    "Team": "HomeTeam",
    "Momentum": "HomeMomentum"
})


# Prepare away-team momentum
away_momentum = team_matches[
    ["Date", "Season", "Team", "Momentum"]
].rename(columns={
    "Team": "AwayTeam",
    "Momentum": "AwayMomentum"
})


# Merge home momentum into match data
df = df.merge(
    home_momentum,
    on=["Date", "Season", "HomeTeam"],
    how="left"
)


# Merge away momentum into match data
df = df.merge(
    away_momentum,
    on=["Date", "Season", "AwayTeam"],
    how="left"
)


# Compare both teams' momentum
df["MomentumGap"] = (
    df["HomeMomentum"]
    - df["AwayMomentum"]
)


# Show result
print(
    df[
        [
            "Date",
            "HomeTeam",
            "AwayTeam",
            "HomeMomentum",
            "AwayMomentum",
            "MomentumGap"
        ]
    ]
    .dropna(
        subset=[
            "HomeMomentum",
            "AwayMomentum"
        ]
    )
    .head(20)
)