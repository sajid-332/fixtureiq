import pandas as pd


# Load historical EPL data
file_path = "data/historical/processed/epl_historical.csv"

df = pd.read_csv(file_path)

df["Date"] = pd.to_datetime(df["Date"])


# Create a consistent H2H pair
df["H2HPair"] = df.apply(
    lambda row: " | ".join(
        sorted([
            row["HomeTeam"],
            row["AwayTeam"]
        ])
    ),
    axis=1
)


print(
    df[
        [
            "Date",
            "HomeTeam",
            "AwayTeam",
            "H2HPair"
        ]
    ].head(20)
)

# Sort each H2H rivalry chronologically
df = df.sort_values(
    ["H2HPair", "Date"]
).reset_index(drop=True)


# Count how many previous H2H meetings existed
df["H2HMatchesBefore"] = (
    df
    .groupby("H2HPair")
    .cumcount()
)

df["H2HMatchesUsed"] = (
    df["H2HMatchesBefore"]
    .clip(upper=5)
)

# Store previous-5 H2H points
home_h2h_points = []
away_h2h_points = []


for pair, pair_matches in df.groupby("H2HPair", sort=False):

    history = []

    for index, match in pair_matches.iterrows():

        home_team = match["HomeTeam"]
        away_team = match["AwayTeam"]

        previous_5 = history[-5:]

        home_previous_points = sum(
            game.get(home_team, 0)
            for game in previous_5
        )

        away_previous_points = sum(
            game.get(away_team, 0)
            for game in previous_5
        )

        home_h2h_points.append(
            (index, home_previous_points)
        )

        away_h2h_points.append(
            (index, away_previous_points)
        )


        # Current match points
        if match["FTR"] == "H":

            current_home_points = 3
            current_away_points = 0

        elif match["FTR"] == "A":

            current_home_points = 0
            current_away_points = 3

        else:

            current_home_points = 1
            current_away_points = 1


        # Add current match only AFTER calculating previous H2H
        history.append({
            home_team: current_home_points,
            away_team: current_away_points
        })


for index, points in home_h2h_points:
    df.loc[index, "HomeH2HLast5Points"] = points


for index, points in away_h2h_points:
    df.loc[index, "AwayH2HLast5Points"] = points


print(
    df[
        [
            "Date",
            "HomeTeam",
            "AwayTeam",
            "H2HMatchesBefore",
            "HomeH2HLast5Points",
            "AwayH2HLast5Points",
            "H2HMatchesUsed"
        ]
    ].head(30)
)