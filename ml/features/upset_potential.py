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


# Create team-by-team history
team_matches = pd.concat(
    [home, away],
    ignore_index=True
)

team_matches = team_matches.sort_values(
    ["Team", "Season", "Date"]
).reset_index(drop=True)


# Matches played BEFORE current match
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


# Season PPG BEFORE current match
team_matches["SeasonPPG"] = (
    team_matches["LeaguePointsBefore"]
    / team_matches["GamesPlayedBefore"]
)


# Previous 5 matches points
team_matches["Last5Points"] = (
    team_matches
    .groupby(["Team", "Season"])["Points"]
    .transform(
        lambda x: x.shift(1).rolling(5).sum()
    )
)


# Recent PPG
team_matches["RecentPPG"] = (
    team_matches["Last5Points"] / 5
)


# Prepare home-team strength data
home_strength = team_matches[
    [
        "Date",
        "Season",
        "Team",
        "SeasonPPG",
        "RecentPPG"
    ]
].rename(columns={
    "Team": "HomeTeam",
    "SeasonPPG": "HomeSeasonPPG",
    "RecentPPG": "HomeRecentPPG"
})


# Prepare away-team strength data
away_strength = team_matches[
    [
        "Date",
        "Season",
        "Team",
        "SeasonPPG",
        "RecentPPG"
    ]
].rename(columns={
    "Team": "AwayTeam",
    "SeasonPPG": "AwaySeasonPPG",
    "RecentPPG": "AwayRecentPPG"
})


# Merge home data
df = df.merge(
    home_strength,
    on=["Date", "Season", "HomeTeam"],
    how="left"
)


# Merge away data
df = df.merge(
    away_strength,
    on=["Date", "Season", "AwayTeam"],
    how="left"
)


# Whole-season strength difference
df["SeasonStrengthGap"] = (
    df["HomeSeasonPPG"]
    - df["AwaySeasonPPG"]
)


# Recent-form difference
df["RecentFormGap"] = (
    df["HomeRecentPPG"]
    - df["AwayRecentPPG"]
)

# Change from season-level strength to recent form
df["FormSwing"] = (
    df["RecentFormGap"]
    - df["SeasonStrengthGap"]
)

# Detect when season strength and recent form point
# toward opposite teams
df["UpsetPotential"] = 0.0

opposite_form = (
    df["SeasonStrengthGap"]
    * df["RecentFormGap"]
) < 0

df.loc[
    opposite_form,
    "UpsetPotential"
] = df.loc[
    opposite_form,
    "FormSwing"
].abs()

# +1 = possible home-team upset
# -1 = possible away-team upset
#  0 = no clear upset signal
df["UpsetDirection"] = 0

df.loc[
    (df["SeasonStrengthGap"] < 0)
    & (df["RecentFormGap"] > 0),
    "UpsetDirection"
] = 1

df.loc[
    (df["SeasonStrengthGap"] > 0)
    & (df["RecentFormGap"] < 0),
    "UpsetDirection"
] = -1



# Show matches where enough history exists
print(
    df[
        [
            "Date",
            "HomeTeam",
            "AwayTeam",
            "SeasonStrengthGap",
            "RecentFormGap",
            "FormSwing",
            "UpsetPotential",
            "UpsetDirection"
        ]
    ]
    .dropna()
    .head(30)
)