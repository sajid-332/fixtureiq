import pandas as pd


# Load historical EPL data
file_path = "data/historical/processed/epl_historical.csv"

df = pd.read_csv(file_path)

df["Date"] = pd.to_datetime(df["Date"])


results = []


# Process each season separately
for season, season_df in df.groupby("Season"):

    season_df = season_df.sort_values("Date").copy()

    teams = sorted(
        set(season_df["HomeTeam"]) |
        set(season_df["AwayTeam"])
    )


    # Starting league table
    table = {
        team: {
            "Points": 0,
            "GF": 0,
            "GA": 0
        }
        for team in teams
    }


    # Process one match date at a time
    for match_date in sorted(season_df["Date"].unique()):

        matches_today = season_df[
            season_df["Date"] == match_date
        ]


        # -----------------------------
        # Build table BEFORE today
        # -----------------------------

        table_rows = []

        for team in teams:

            points = table[team]["Points"]
            gf = table[team]["GF"]
            ga = table[team]["GA"]

            table_rows.append({
                "Team": team,
                "Points": points,
                "GF": gf,
                "GA": ga,
                "GD": gf - ga
            })


        standings = pd.DataFrame(table_rows)


        # Sort league table
        standings = standings.sort_values(
            ["Points", "GD", "GF", "Team"],
            ascending=[False, False, False, True]
        ).reset_index(drop=True)


        # -----------------------------
        # Calculate shared positions
        # -----------------------------

        state_changed = standings[
            ["Points", "GD", "GF"]
        ].ne(
            standings[
                ["Points", "GD", "GF"]
            ].shift()
        ).any(axis=1)


        position_numbers = pd.Series(
            standings.index + 1,
            index=standings.index
        )


        standings["Position"] = (
            position_numbers
            .where(state_changed)
            .ffill()
            .astype(int)
        )


        # Team -> Position lookup
        position_map = dict(
            zip(
                standings["Team"],
                standings["Position"]
            )
        )


        # -----------------------------
        # Save PRE-MATCH positions
        # -----------------------------

        for _, match in matches_today.iterrows():

            results.append({
                "Date": match["Date"],
                "Season": season,
                "HomeTeam": match["HomeTeam"],
                "AwayTeam": match["AwayTeam"],
                "HomePositionBefore": position_map[
                    match["HomeTeam"]
                ],
                "AwayPositionBefore": position_map[
                    match["AwayTeam"]
                ]
            })


        # -----------------------------
        # Update table AFTER today
        # -----------------------------

        for _, match in matches_today.iterrows():

            home = match["HomeTeam"]
            away = match["AwayTeam"]

            home_goals = match["FTHG"]
            away_goals = match["FTAG"]


            # Update goals
            table[home]["GF"] += home_goals
            table[home]["GA"] += away_goals

            table[away]["GF"] += away_goals
            table[away]["GA"] += home_goals


            # Update points
            if match["FTR"] == "H":

                table[home]["Points"] += 3

            elif match["FTR"] == "A":

                table[away]["Points"] += 3

            else:

                table[home]["Points"] += 1
                table[away]["Points"] += 1


# Create final DataFrame
position_df = pd.DataFrame(results)


print("Matches with pre-match league position:")

print(
    position_df.head(30)
)