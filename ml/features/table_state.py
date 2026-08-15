import pandas as pd


# Load historical EPL data
file_path = "data/historical/processed/epl_historical.csv"

df = pd.read_csv(file_path)

df["Date"] = pd.to_datetime(df["Date"])


# Convert results into league points
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


# Home-team records
home = df[
    ["Date", "Season", "HomeTeam", "HomePoints"]
].copy()

home.columns = [
    "Date",
    "Season",
    "Team",
    "Points"
]


# Away-team records
away = df[
    ["Date", "Season", "AwayTeam", "AwayPoints"]
].copy()

away.columns = [
    "Date",
    "Season",
    "Team",
    "Points"
]


# Combine into team match history
team_matches = pd.concat(
    [home, away],
    ignore_index=True
)

team_matches = team_matches.sort_values(
    ["Team", "Season", "Date"]
).reset_index(drop=True)


# Number of matches played BEFORE the current match
team_matches["GamesPlayedBefore"] = (
    team_matches
    .groupby(["Team", "Season"])
    .cumcount()
)


# League points earned BEFORE the current match
team_matches["LeaguePointsBefore"] = (
    team_matches
    .groupby(["Team", "Season"])["Points"]
    .transform(
        lambda x: x.shift(1).cumsum()
    )
    .fillna(0)
)

# Prepare home pre-match table state
home_state = team_matches[
    [
        "Date",
        "Season",
        "Team",
        "GamesPlayedBefore",
        "LeaguePointsBefore"
    ]
].rename(columns={
    "Team": "HomeTeam",
    "GamesPlayedBefore": "HomeGamesPlayedBefore",
    "LeaguePointsBefore": "HomeLeaguePointsBefore"
})


# Prepare away pre-match table state
away_state = team_matches[
    [
        "Date",
        "Season",
        "Team",
        "GamesPlayedBefore",
        "LeaguePointsBefore"
    ]
].rename(columns={
    "Team": "AwayTeam",
    "GamesPlayedBefore": "AwayGamesPlayedBefore",
    "LeaguePointsBefore": "AwayLeaguePointsBefore"
})


# Merge home state into matches
df = df.merge(
    home_state,
    on=["Date", "Season", "HomeTeam"],
    how="left"
)


# Merge away state into matches
df = df.merge(
    away_state,
    on=["Date", "Season", "AwayTeam"],
    how="left"
)

df["LeaguePointsGap"] = (
    df["HomeLeaguePointsBefore"]
    - df["AwayLeaguePointsBefore"]
)

df["GamesPlayedGap"] = (
    df["HomeGamesPlayedBefore"]
    - df["AwayGamesPlayedBefore"]
)

print("\nMatches with pre-match table state:")

print(
    df[
        [
            "Date",
            "HomeTeam",
            "AwayTeam",
            "HomeGamesPlayedBefore",
            "AwayGamesPlayedBefore",
            "HomeLeaguePointsBefore",
            "AwayLeaguePointsBefore",
            "LeaguePointsGap",
            "GamesPlayedGap"
        ]
    ].head(30)
)

