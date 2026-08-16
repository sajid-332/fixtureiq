import pandas as pd


# ================================================================
# LOAD HISTORICAL DATA
# ================================================================

file_path = "data/historical/processed/epl_historical.csv"

df = pd.read_csv(file_path)

df["Date"] = pd.to_datetime(df["Date"])


results = []


# ================================================================
# BUILD PRE-MATCH LEAGUE STATE
# ================================================================

for season, season_df in df.groupby("Season"):

    season_df = season_df.sort_values("Date").copy()

    teams = sorted(
        set(season_df["HomeTeam"])
        | set(season_df["AwayTeam"])
    )


    # Starting league table
    table = {
        team: {
            "Points": 0,
            "Played": 0,
            "GF": 0,
            "GA": 0
        }
        for team in teams
    }


    # ------------------------------------------------------------
    # PROCESS ONE MATCH DATE AT A TIME
    # ------------------------------------------------------------

    for match_date in sorted(season_df["Date"].unique()):

        matches_today = season_df[
            season_df["Date"] == match_date
        ]


        # ========================================================
        # BUILD TABLE BEFORE TODAY'S MATCHES
        # ========================================================

        table_rows = []

        for team in teams:

            points = table[team]["Points"]
            played = table[team]["Played"]
            gf = table[team]["GF"]
            ga = table[team]["GA"]

            table_rows.append({
                "Team": team,
                "Points": points,
                "Played": played,
                "GF": gf,
                "GA": ga,
                "GD": gf - ga
            })


        standings = pd.DataFrame(table_rows)

        standings = standings.sort_values(
            ["Points", "GD", "GF", "Team"],
            ascending=[False, False, False, True]
        ).reset_index(drop=True)


        # ========================================================
        # IMPORTANT TABLE REFERENCE VALUES
        # ========================================================

        # 1st place
        leader_points = standings.iloc[0]["Points"]

        # 4th place
        top4_points = standings.iloc[3]["Points"]

        # 17th = last safe team
        safe_points = standings.iloc[16]["Points"]

        # 18th = first relegation position
        relegation_points = standings.iloc[17]["Points"]


        # ========================================================
        # CREATE TEAM STATE
        # ========================================================

        team_state = {}


        for _, row in standings.iterrows():

            team = row["Team"]

            points = row["Points"]

            played = row["Played"]


            # row.name starts from 0
            # so +1 gives league position
            position = int(row.name) + 1


            # ----------------------------------------------------
            # RELEGATION STATUS
            # ----------------------------------------------------

            in_relegation_zone = position >= 18


            # ----------------------------------------------------
            # DISTANCE FROM RELEGATION / SAFETY BOUNDARY
            # ----------------------------------------------------

            if in_relegation_zone:

                # Example:
                #
                # 17th safe team = 30 points
                # this team      = 27 points
                #
                # distance from safety = 3

                relegation_distance = max(
                    0,
                    safe_points - points
                )

            else:

                # Example:
                #
                # this team = 32 points
                # 18th      = 28 points
                #
                # distance above relegation = 4

                relegation_distance = max(
                    0,
                    points - relegation_points
                )


            # ----------------------------------------------------
            # SAVE TEAM STATE
            # ----------------------------------------------------

            team_state[team] = {

                # 0 = leader
                # positive = points behind leader
                "PointsToLeader": (
                    leader_points - points
                ),


                # Signed Top-4 gap
                #
                # positive = below Top-4 boundary
                # 0        = exactly at boundary
                # negative = above Top-4 boundary
                "PointsToTop4": (
                    top4_points - points
                ),


                # Positive = above 18th-place points
                # Negative = below 18th-place points
                "PointsAboveRelegation": (
                    points - relegation_points
                ),


                # Absolute distance from the
                # relegation/safety battle boundary
                "RelegationDistance":
                    relegation_distance,


                # 1 = currently 18th, 19th or 20th
                # 0 = currently outside relegation zone
                "InRelegationZone":
                    int(in_relegation_zone),


                # EPL season = 38 matches
                "MatchesRemaining": (
                    38 - played
                )
            }


        # ========================================================
        # SAVE PRE-MATCH VALUES
        # ========================================================

        for _, match in matches_today.iterrows():

            home = match["HomeTeam"]

            away = match["AwayTeam"]


            results.append({

                "Date":
                    match["Date"],

                "Season":
                    season,

                "HomeTeam":
                    home,

                "AwayTeam":
                    away,


                # --------------------------------
                # TITLE
                # --------------------------------

                "HomePointsToLeader":
                    team_state[home]["PointsToLeader"],

                "AwayPointsToLeader":
                    team_state[away]["PointsToLeader"],


                # --------------------------------
                # TOP 4
                # --------------------------------

                "HomePointsToTop4":
                    team_state[home]["PointsToTop4"],

                "AwayPointsToTop4":
                    team_state[away]["PointsToTop4"],


                # --------------------------------
                # RELEGATION
                # --------------------------------

                "HomePointsAboveRelegation":
                    team_state[home]["PointsAboveRelegation"],

                "AwayPointsAboveRelegation":
                    team_state[away]["PointsAboveRelegation"],


                "HomeRelegationDistance":
                    team_state[home]["RelegationDistance"],

                "AwayRelegationDistance":
                    team_state[away]["RelegationDistance"],


                "HomeInRelegationZone":
                    team_state[home]["InRelegationZone"],

                "AwayInRelegationZone":
                    team_state[away]["InRelegationZone"],


                # --------------------------------
                # MATCHES REMAINING
                # --------------------------------

                "HomeMatchesRemaining":
                    team_state[home]["MatchesRemaining"],

                "AwayMatchesRemaining":
                    team_state[away]["MatchesRemaining"]
            })


        # ========================================================
        # UPDATE TABLE AFTER TODAY'S MATCHES
        # ========================================================

        for _, match in matches_today.iterrows():

            home = match["HomeTeam"]

            away = match["AwayTeam"]

            home_goals = match["FTHG"]

            away_goals = match["FTAG"]


            # ----------------------------------------------------
            # GAMES PLAYED
            # ----------------------------------------------------

            table[home]["Played"] += 1

            table[away]["Played"] += 1


            # ----------------------------------------------------
            # GOALS
            # ----------------------------------------------------

            table[home]["GF"] += home_goals

            table[home]["GA"] += away_goals


            table[away]["GF"] += away_goals

            table[away]["GA"] += home_goals


            # ----------------------------------------------------
            # POINTS
            # ----------------------------------------------------

            if match["FTR"] == "H":

                table[home]["Points"] += 3


            elif match["FTR"] == "A":

                table[away]["Points"] += 3


            else:

                table[home]["Points"] += 1

                table[away]["Points"] += 1


# ================================================================
# CREATE FINAL DATAFRAME
# ================================================================

pressure_df = pd.DataFrame(results)


# ================================================================
# SEASON PROGRESS
# ================================================================

pressure_df["HomeSeasonProgress"] = (
    38 - pressure_df["HomeMatchesRemaining"]
) / 38


pressure_df["AwaySeasonProgress"] = (
    38 - pressure_df["AwayMatchesRemaining"]
) / 38


# ================================================================
# MAXIMUM POINTS STILL AVAILABLE
# ================================================================

pressure_df["HomeMaxPointsAvailable"] = (
    pressure_df["HomeMatchesRemaining"] * 3
)


pressure_df["AwayMaxPointsAvailable"] = (
    pressure_df["AwayMatchesRemaining"] * 3
)


# ================================================================
# TITLE PRESSURE
# ================================================================

# Can the team still mathematically catch the leader?

home_can_catch = (
    pressure_df["HomePointsToLeader"]
    <= pressure_df["HomeMaxPointsAvailable"]
)


away_can_catch = (
    pressure_df["AwayPointsToLeader"]
    <= pressure_df["AwayMaxPointsAvailable"]
)


pressure_df["HomeTitlePressure"] = 0.0

pressure_df["AwayTitlePressure"] = 0.0


# ------------------------------------------------
# HOME TITLE PRESSURE
# ------------------------------------------------

pressure_df.loc[
    home_can_catch,
    "HomeTitlePressure"
] = (

    pressure_df.loc[
        home_can_catch,
        "HomeSeasonProgress"
    ]

    /

    (
        1
        +
        pressure_df.loc[
            home_can_catch,
            "HomePointsToLeader"
        ]
    )
)


# ------------------------------------------------
# AWAY TITLE PRESSURE
# ------------------------------------------------

pressure_df.loc[
    away_can_catch,
    "AwayTitlePressure"
] = (

    pressure_df.loc[
        away_can_catch,
        "AwaySeasonProgress"
    ]

    /

    (
        1
        +
        pressure_df.loc[
            away_can_catch,
            "AwayPointsToLeader"
        ]
    )
)


# ================================================================
# TOP-4 PRESSURE
# ================================================================

# Absolute distance from Top-4 boundary

pressure_df["HomeTop4Distance"] = (
    pressure_df["HomePointsToTop4"].abs()
)


pressure_df["AwayTop4Distance"] = (
    pressure_df["AwayPointsToTop4"].abs()
)


# ------------------------------------------------
# CAN STILL COMPETE FOR TOP 4?
# ------------------------------------------------

home_can_compete_top4 = (
    pressure_df["HomePointsToTop4"]
    <= pressure_df["HomeMaxPointsAvailable"]
)


away_can_compete_top4 = (
    pressure_df["AwayPointsToTop4"]
    <= pressure_df["AwayMaxPointsAvailable"]
)


pressure_df["HomeTop4Pressure"] = 0.0

pressure_df["AwayTop4Pressure"] = 0.0


# ------------------------------------------------
# HOME TOP-4 PRESSURE
# ------------------------------------------------

pressure_df.loc[
    home_can_compete_top4,
    "HomeTop4Pressure"
] = (

    pressure_df.loc[
        home_can_compete_top4,
        "HomeSeasonProgress"
    ]

    /

    (
        1
        +
        pressure_df.loc[
            home_can_compete_top4,
            "HomeTop4Distance"
        ]
    )
)


# ------------------------------------------------
# AWAY TOP-4 PRESSURE
# ------------------------------------------------

pressure_df.loc[
    away_can_compete_top4,
    "AwayTop4Pressure"
] = (

    pressure_df.loc[
        away_can_compete_top4,
        "AwaySeasonProgress"
    ]

    /

    (
        1
        +
        pressure_df.loc[
            away_can_compete_top4,
            "AwayTop4Distance"
        ]
    )
)


# ================================================================
# RELEGATION PRESSURE
# ================================================================

# High when:
#
# - team is close to relegation/safety boundary
# - season is close to ending


pressure_df["HomeRelegationPressure"] = (

    pressure_df["HomeSeasonProgress"]

    /

    (
        1
        +
        pressure_df["HomeRelegationDistance"]
    )
)


pressure_df["AwayRelegationPressure"] = (

    pressure_df["AwaySeasonProgress"]

    /

    (
        1
        +
        pressure_df["AwayRelegationDistance"]
    )
)


# ================================================================
# DISPLAY RELEGATION TEST OUTPUT
# ================================================================

print(
    pressure_df[
        [
            "Date",
            "HomeTeam",
            "AwayTeam",
            "HomeRelegationDistance",
            "AwayRelegationDistance",
            "HomeInRelegationZone",
            "AwayInRelegationZone",
            "HomeRelegationPressure",
            "AwayRelegationPressure"
        ]
    ]
    .sort_values(
        "HomeRelegationPressure",
        ascending=False
    )
    .head(20)
    .to_string(index=False)
)