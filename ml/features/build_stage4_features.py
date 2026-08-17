import pandas as pd


# ================================================================
# FILE PATHS
# ================================================================

stage3_file = "data/historical/processed/epl_features.csv"
historical_file = "data/historical/processed/epl_historical.csv"
output_file = "data/historical/processed/epl_stage4_features.csv"


# ================================================================
# LOAD DATA
# ================================================================

df = pd.read_csv(stage3_file)
historical = pd.read_csv(historical_file)

df["Date"] = pd.to_datetime(df["Date"])
historical["Date"] = pd.to_datetime(historical["Date"])


print("Stage 3 dataset loaded successfully!")
print("Matches:", len(df))
print("Columns:", len(df.columns))


# ================================================================
# COMMON MERGE KEYS
# ================================================================

merge_keys = [
    "Date",
    "Season",
    "HomeTeam",
    "AwayTeam"
]


# ================================================================
# TABLE STATE + LEAGUE POSITION
# ================================================================

table_results = []


for season, season_df in historical.groupby("Season"):

    season_df = season_df.sort_values("Date").copy()

    teams = sorted(
        set(season_df["HomeTeam"])
        | set(season_df["AwayTeam"])
    )

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


        # --------------------------------------------------------
        # BUILD TABLE BEFORE TODAY'S MATCHES
        # --------------------------------------------------------

        standings_rows = []

        for team in teams:

            points = table[team]["Points"]
            played = table[team]["Played"]
            gf = table[team]["GF"]
            ga = table[team]["GA"]

            standings_rows.append({
                "Team": team,
                "Points": points,
                "Played": played,
                "GF": gf,
                "GA": ga,
                "GD": gf - ga
            })


        standings = pd.DataFrame(standings_rows)

        standings = standings.sort_values(
            ["Points", "GD", "GF", "Team"],
            ascending=[False, False, False, True]
        ).reset_index(drop=True)


        # --------------------------------------------------------
        # SHARED LEAGUE POSITIONS
        # --------------------------------------------------------

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


        # --------------------------------------------------------
        # TEAM LOOKUP
        # --------------------------------------------------------

        team_state = {}

        for _, row in standings.iterrows():

            team_state[row["Team"]] = {

                "GamesPlayedBefore":
                    int(row["Played"]),

                "LeaguePointsBefore":
                    int(row["Points"]),

                "PositionBefore":
                    int(row["Position"])
            }


        # --------------------------------------------------------
        # SAVE PRE-MATCH STATE
        # --------------------------------------------------------

        for _, match in matches_today.iterrows():

            home = match["HomeTeam"]
            away = match["AwayTeam"]

            home_games = (
                team_state[home]["GamesPlayedBefore"]
            )

            away_games = (
                team_state[away]["GamesPlayedBefore"]
            )

            home_points = (
                team_state[home]["LeaguePointsBefore"]
            )

            away_points = (
                team_state[away]["LeaguePointsBefore"]
            )


            table_results.append({

                "Date":
                    match["Date"],

                "Season":
                    season,

                "HomeTeam":
                    home,

                "AwayTeam":
                    away,


                "HomeGamesPlayedBefore":
                    home_games,

                "AwayGamesPlayedBefore":
                    away_games,


                "HomeLeaguePointsBefore":
                    home_points,

                "AwayLeaguePointsBefore":
                    away_points,


                "LeaguePointsGap":
                    home_points - away_points,

                "GamesPlayedGap":
                    home_games - away_games,


                "HomePositionBefore":
                    team_state[home]["PositionBefore"],

                "AwayPositionBefore":
                    team_state[away]["PositionBefore"]
            })


        # --------------------------------------------------------
        # UPDATE TABLE AFTER TODAY'S MATCHES
        # --------------------------------------------------------

        for _, match in matches_today.iterrows():

            home = match["HomeTeam"]
            away = match["AwayTeam"]

            home_goals = int(match["FTHG"])
            away_goals = int(match["FTAG"])


            table[home]["Played"] += 1
            table[away]["Played"] += 1


            table[home]["GF"] += home_goals
            table[home]["GA"] += away_goals

            table[away]["GF"] += away_goals
            table[away]["GA"] += home_goals


            if match["FTR"] == "H":

                table[home]["Points"] += 3

            elif match["FTR"] == "A":

                table[away]["Points"] += 3

            else:

                table[home]["Points"] += 1
                table[away]["Points"] += 1


# ================================================================
# CREATE TABLE STATE DATAFRAME
# ================================================================

table_df = pd.DataFrame(table_results)


print("\nTable-state rows:", len(table_df))


table_duplicates = table_df.duplicated(
    subset=merge_keys
).sum()


print(
    "Duplicate table-state matches:",
    table_duplicates
)


# ================================================================
# MERGE TABLE STATE
# ================================================================

original_rows = len(df)


df = df.merge(
    table_df,
    on=merge_keys,
    how="left",
    validate="one_to_one"
)


if len(df) != original_rows:

    raise ValueError(
        "ERROR: Match count changed after table-state merge!"
    )


print("\nAfter table-state merge:")
print("Matches:", len(df))
print("Columns:", len(df.columns))


table_feature_columns = [

    "HomeGamesPlayedBefore",
    "AwayGamesPlayedBefore",

    "HomeLeaguePointsBefore",
    "AwayLeaguePointsBefore",

    "LeaguePointsGap",
    "GamesPlayedGap",

    "HomePositionBefore",
    "AwayPositionBefore"
]


print("\nMissing table-state values:")

print(
    df[
        table_feature_columns
    ]
    .isnull()
    .sum()
)


# ================================================================
# H2H FEATURES
# ================================================================

h2h_source = historical.copy()


h2h_source["H2HPair"] = h2h_source.apply(
    lambda row: " | ".join(
        sorted([
            row["HomeTeam"],
            row["AwayTeam"]
        ])
    ),
    axis=1
)


h2h_source = h2h_source.sort_values(
    ["H2HPair", "Date"]
).copy()


h2h_results = []

pair_history = {}


for _, match in h2h_source.iterrows():

    pair = match["H2HPair"]

    home = match["HomeTeam"]
    away = match["AwayTeam"]

    history = pair_history.get(
        pair,
        []
    )


    # Only latest 5 previous meetings
    previous_five = history[-5:]


    home_h2h_points = 0
    away_h2h_points = 0


    for previous in previous_five:

        if previous["HomeTeam"] == home:

            home_h2h_points += (
                previous["HomePoints"]
            )

            away_h2h_points += (
                previous["AwayPoints"]
            )

        else:

            home_h2h_points += (
                previous["AwayPoints"]
            )

            away_h2h_points += (
                previous["HomePoints"]
            )


    # ------------------------------------------------------------
    # SAVE FEATURES BEFORE ADDING CURRENT MATCH
    # ------------------------------------------------------------

    h2h_results.append({

        "Date":
            match["Date"],

        "Season":
            match["Season"],

        "HomeTeam":
            home,

        "AwayTeam":
            away,

        "HomeH2HLast5Points":
            home_h2h_points,

        "AwayH2HLast5Points":
            away_h2h_points,

        "H2HMatchesBefore":
            len(history),

        "H2HMatchesUsed":
            min(
                len(history),
                5
            )
    })


    # ------------------------------------------------------------
    # CURRENT MATCH POINTS
    # ------------------------------------------------------------

    if match["FTR"] == "H":

        home_points = 3
        away_points = 0

    elif match["FTR"] == "A":

        home_points = 0
        away_points = 3

    else:

        home_points = 1
        away_points = 1


    # Add current match only AFTER feature calculation
    history.append({

        "HomeTeam":
            home,

        "AwayTeam":
            away,

        "HomePoints":
            home_points,

        "AwayPoints":
            away_points
    })


    pair_history[pair] = history


# ================================================================
# CREATE H2H DATAFRAME
# ================================================================

h2h_df = pd.DataFrame(h2h_results)


print("\nH2H rows:", len(h2h_df))


h2h_duplicates = h2h_df.duplicated(
    subset=merge_keys
).sum()


print(
    "Duplicate H2H matches:",
    h2h_duplicates
)


# ================================================================
# MERGE H2H
# ================================================================

rows_before_h2h = len(df)


df = df.merge(
    h2h_df,
    on=merge_keys,
    how="left",
    validate="one_to_one"
)


if len(df) != rows_before_h2h:

    raise ValueError(
        "ERROR: Match count changed after H2H merge!"
    )


print("\nAfter H2H merge:")
print("Matches:", len(df))
print("Columns:", len(df.columns))


h2h_columns = [

    "HomeH2HLast5Points",
    "AwayH2HLast5Points",

    "H2HMatchesBefore",
    "H2HMatchesUsed"
]


print("\nMissing H2H values:")

print(
    df[
        h2h_columns
    ]
    .isnull()
    .sum()
)


# ================================================================
# MOMENTUM + UPSET POTENTIAL
# ================================================================

# ------------------------------------------------
# HOME TEAM HISTORY
# ------------------------------------------------

home_history = historical[
    [
        "Date",
        "Season",
        "HomeTeam",
        "FTR"
    ]
].copy()


home_history = home_history.rename(
    columns={
        "HomeTeam": "Team"
    }
)


home_history["Points"] = (
    home_history["FTR"].map({
        "H": 3,
        "D": 1,
        "A": 0
    })
)


# ------------------------------------------------
# AWAY TEAM HISTORY
# ------------------------------------------------

away_history = historical[
    [
        "Date",
        "Season",
        "AwayTeam",
        "FTR"
    ]
].copy()


away_history = away_history.rename(
    columns={
        "AwayTeam": "Team"
    }
)


away_history["Points"] = (
    away_history["FTR"].map({
        "H": 0,
        "D": 1,
        "A": 3
    })
)


# ------------------------------------------------
# COMBINE TEAM HISTORY
# ------------------------------------------------

team_history = pd.concat(
    [
        home_history[
            ["Date", "Season", "Team", "Points"]
        ],

        away_history[
            ["Date", "Season", "Team", "Points"]
        ]
    ],
    ignore_index=True
)


team_history = team_history.sort_values(
    [
        "Team",
        "Season",
        "Date"
    ]
).reset_index(drop=True)


# ================================================================
# GAMES PLAYED BEFORE MATCH
# ================================================================

team_history["GamesPlayedBefore"] = (
    team_history
    .groupby(
        ["Team", "Season"]
    )
    .cumcount()
)


# ================================================================
# LEAGUE POINTS BEFORE MATCH
# ================================================================

team_history["LeaguePointsBefore"] = (
    team_history
    .groupby(
        ["Team", "Season"]
    )["Points"]
    .transform(
        lambda x:
            x.shift(1)
            .cumsum()
    )
)


team_history["LeaguePointsBefore"] = (
    team_history["LeaguePointsBefore"]
    .fillna(0)
)


# ================================================================
# SEASON PPG
# ================================================================

team_history["SeasonPPG"] = (
    team_history["LeaguePointsBefore"]
    /
    team_history["GamesPlayedBefore"]
)


# ================================================================
# LAST-5 POINTS
# ================================================================

team_history["Last5Points"] = (
    team_history
    .groupby(
        ["Team", "Season"]
    )["Points"]
    .transform(
        lambda x:
            x.shift(1)
            .rolling(5)
            .sum()
    )
)


# ================================================================
# RECENT PPG
# ================================================================

team_history["RecentPPG"] = (
    team_history["Last5Points"]
    / 5
)


# ================================================================
# MOMENTUM
# ================================================================

team_history["Momentum"] = (
    team_history["RecentPPG"]
    -
    team_history["SeasonPPG"]
)


# ================================================================
# HOME LOOKUP
# ================================================================

home_context = team_history[
    [
        "Date",
        "Season",
        "Team",
        "SeasonPPG",
        "RecentPPG",
        "Momentum"
    ]
].copy()


home_context = home_context.rename(
    columns={

        "Team":
            "HomeTeam",

        "SeasonPPG":
            "HomeSeasonPPG",

        "RecentPPG":
            "HomeRecentPPG",

        "Momentum":
            "HomeMomentum"
    }
)


# ================================================================
# AWAY LOOKUP
# ================================================================

away_context = team_history[
    [
        "Date",
        "Season",
        "Team",
        "SeasonPPG",
        "RecentPPG",
        "Momentum"
    ]
].copy()


away_context = away_context.rename(
    columns={

        "Team":
            "AwayTeam",

        "SeasonPPG":
            "AwaySeasonPPG",

        "RecentPPG":
            "AwayRecentPPG",

        "Momentum":
            "AwayMomentum"
    }
)


# ================================================================
# CREATE MATCH-LEVEL MOMENTUM DATA
# ================================================================

momentum_upset_df = historical[
    merge_keys
].copy()


momentum_upset_df = momentum_upset_df.merge(
    home_context,
    on=[
        "Date",
        "Season",
        "HomeTeam"
    ],
    how="left",
    validate="one_to_one"
)


momentum_upset_df = momentum_upset_df.merge(
    away_context,
    on=[
        "Date",
        "Season",
        "AwayTeam"
    ],
    how="left",
    validate="one_to_one"
)


# ================================================================
# MOMENTUM GAP
# ================================================================

momentum_upset_df["MomentumGap"] = (

    momentum_upset_df["HomeMomentum"]
    -
    momentum_upset_df["AwayMomentum"]
)


# ================================================================
# UPSET FEATURES
# ================================================================

momentum_upset_df["SeasonStrengthGap"] = (

    momentum_upset_df["HomeSeasonPPG"]
    -
    momentum_upset_df["AwaySeasonPPG"]
)


momentum_upset_df["RecentFormGap"] = (

    momentum_upset_df["HomeRecentPPG"]
    -
    momentum_upset_df["AwayRecentPPG"]
)


momentum_upset_df["FormSwing"] = (

    momentum_upset_df["RecentFormGap"]
    -
    momentum_upset_df["SeasonStrengthGap"]
)


# ------------------------------------------------
# VALID UPSET DATA
# ------------------------------------------------

valid_upset_data = (

    momentum_upset_df[
        "SeasonStrengthGap"
    ].notna()

    &

    momentum_upset_df[
        "RecentFormGap"
    ].notna()
)


# NaN = not enough historical data yet

momentum_upset_df[
    "UpsetPotential"
] = float("nan")


momentum_upset_df[
    "UpsetDirection"
] = float("nan")


# Enough data, but currently no upset signal

momentum_upset_df.loc[
    valid_upset_data,
    "UpsetPotential"
] = 0.0


momentum_upset_df.loc[
    valid_upset_data,
    "UpsetDirection"
] = 0


# ------------------------------------------------
# SEASON AND RECENT FORM POINT TO OPPOSITE TEAMS
# ------------------------------------------------

opposite_form = (

    valid_upset_data

    &

    (
        momentum_upset_df[
            "SeasonStrengthGap"
        ]

        *

        momentum_upset_df[
            "RecentFormGap"
        ]

        < 0
    )
)


momentum_upset_df.loc[
    opposite_form,
    "UpsetPotential"
] = (

    momentum_upset_df.loc[
        opposite_form,
        "FormSwing"
    ].abs()
)


# ------------------------------------------------
# POSSIBLE HOME UPSET
# ------------------------------------------------

home_upset = (

    valid_upset_data

    &

    (
        momentum_upset_df[
            "SeasonStrengthGap"
        ] < 0
    )

    &

    (
        momentum_upset_df[
            "RecentFormGap"
        ] > 0
    )
)


momentum_upset_df.loc[
    home_upset,
    "UpsetDirection"
] = 1


# ------------------------------------------------
# POSSIBLE AWAY UPSET
# ------------------------------------------------

away_upset = (

    valid_upset_data

    &

    (
        momentum_upset_df[
            "SeasonStrengthGap"
        ] > 0
    )

    &

    (
        momentum_upset_df[
            "RecentFormGap"
        ] < 0
    )
)


momentum_upset_df.loc[
    away_upset,
    "UpsetDirection"
] = -1


# ================================================================
# VALIDATE MOMENTUM / UPSET MATCH KEYS
# ================================================================

print(
    "\nMomentum/Upset rows:",
    len(momentum_upset_df)
)


momentum_duplicates = (
    momentum_upset_df
    .duplicated(
        subset=merge_keys
    )
    .sum()
)


print(
    "Duplicate Momentum/Upset matches:",
    momentum_duplicates
)


# ================================================================
# MERGE MOMENTUM + UPSET
# ================================================================

rows_before_momentum = len(df)


df = df.merge(
    momentum_upset_df,
    on=merge_keys,
    how="left",
    validate="one_to_one"
)


if len(df) != rows_before_momentum:

    raise ValueError(
        "ERROR: Match count changed after Momentum/Upset merge!"
    )


print("\nAfter Momentum/Upset merge:")
print("Matches:", len(df))
print("Columns:", len(df.columns))


momentum_upset_columns = [

    "HomeSeasonPPG",
    "AwaySeasonPPG",

    "HomeRecentPPG",
    "AwayRecentPPG",

    "HomeMomentum",
    "AwayMomentum",

    "MomentumGap",

    "SeasonStrengthGap",
    "RecentFormGap",

    "FormSwing",

    "UpsetPotential",
    "UpsetDirection"
]


print("\nMissing Momentum/Upset values:")

print(
    df[
        momentum_upset_columns
    ]
    .isnull()
    .sum()
)


# ================================================================
# LEAGUE PRESSURE FEATURES
# ================================================================

pressure_results = []


for season, season_df in historical.groupby("Season"):

    season_df = season_df.sort_values("Date").copy()

    teams = sorted(
        set(season_df["HomeTeam"])
        | set(season_df["AwayTeam"])
    )


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
    # PROCESS EACH DATE
    # ------------------------------------------------------------

    for match_date in sorted(season_df["Date"].unique()):

        matches_today = season_df[
            season_df["Date"] == match_date
        ]


        standings_rows = []


        # --------------------------------------------------------
        # PRE-MATCH TABLE
        # --------------------------------------------------------

        for team in teams:

            points = table[team]["Points"]
            played = table[team]["Played"]
            gf = table[team]["GF"]
            ga = table[team]["GA"]


            standings_rows.append({

                "Team":
                    team,

                "Points":
                    points,

                "Played":
                    played,

                "GF":
                    gf,

                "GA":
                    ga,

                "GD":
                    gf - ga
            })


        standings = pd.DataFrame(
            standings_rows
        )


        standings = standings.sort_values(
            [
                "Points",
                "GD",
                "GF",
                "Team"
            ],
            ascending=[
                False,
                False,
                False,
                True
            ]
        ).reset_index(drop=True)


        # ========================================================
        # TABLE BOUNDARIES
        # ========================================================

        leader_points = (
            standings.iloc[0]["Points"]
        )


        top4_points = (
            standings.iloc[3]["Points"]
        )


        # 17th = last safe position
        safe_points = (
            standings.iloc[16]["Points"]
        )


        # 18th = first relegation position
        relegation_points = (
            standings.iloc[17]["Points"]
        )


        # ========================================================
        # TEAM PRESSURE STATE
        # ========================================================

        team_pressure = {}


        for _, row in standings.iterrows():

            team = row["Team"]

            points = row["Points"]

            played = row["Played"]

            position = (
                int(row.name) + 1
            )


            in_relegation_zone = (
                position >= 18
            )


            if in_relegation_zone:

                relegation_distance = max(
                    0,
                    safe_points - points
                )

            else:

                relegation_distance = max(
                    0,
                    points - relegation_points
                )


            team_pressure[team] = {

                "PointsToLeader":
                    leader_points - points,


                # Positive = below Top 4
                # Negative = above Top 4
                "PointsToTop4":
                    top4_points - points,


                "PointsAboveRelegation":
                    points - relegation_points,


                "RelegationDistance":
                    relegation_distance,


                "InRelegationZone":
                    int(
                        in_relegation_zone
                    ),


                "MatchesRemaining":
                    38 - played
            }


        # ========================================================
        # SAVE PRE-MATCH VALUES
        # ========================================================

        for _, match in matches_today.iterrows():

            home = match["HomeTeam"]
            away = match["AwayTeam"]


            pressure_results.append({

                "Date":
                    match["Date"],

                "Season":
                    season,

                "HomeTeam":
                    home,

                "AwayTeam":
                    away,


                "HomePointsToLeader":
                    team_pressure[home][
                        "PointsToLeader"
                    ],

                "AwayPointsToLeader":
                    team_pressure[away][
                        "PointsToLeader"
                    ],


                "HomePointsToTop4":
                    team_pressure[home][
                        "PointsToTop4"
                    ],

                "AwayPointsToTop4":
                    team_pressure[away][
                        "PointsToTop4"
                    ],


                "HomePointsAboveRelegation":
                    team_pressure[home][
                        "PointsAboveRelegation"
                    ],

                "AwayPointsAboveRelegation":
                    team_pressure[away][
                        "PointsAboveRelegation"
                    ],


                "HomeRelegationDistance":
                    team_pressure[home][
                        "RelegationDistance"
                    ],

                "AwayRelegationDistance":
                    team_pressure[away][
                        "RelegationDistance"
                    ],


                "HomeInRelegationZone":
                    team_pressure[home][
                        "InRelegationZone"
                    ],

                "AwayInRelegationZone":
                    team_pressure[away][
                        "InRelegationZone"
                    ],


                "HomeMatchesRemaining":
                    team_pressure[home][
                        "MatchesRemaining"
                    ],

                "AwayMatchesRemaining":
                    team_pressure[away][
                        "MatchesRemaining"
                    ]
            })


        # ========================================================
        # UPDATE TABLE AFTER MATCH DATE
        # ========================================================

        for _, match in matches_today.iterrows():

            home = match["HomeTeam"]
            away = match["AwayTeam"]

            home_goals = int(
                match["FTHG"]
            )

            away_goals = int(
                match["FTAG"]
            )


            table[home]["Played"] += 1
            table[away]["Played"] += 1


            table[home]["GF"] += home_goals
            table[home]["GA"] += away_goals


            table[away]["GF"] += away_goals
            table[away]["GA"] += home_goals


            if match["FTR"] == "H":

                table[home]["Points"] += 3


            elif match["FTR"] == "A":

                table[away]["Points"] += 3


            else:

                table[home]["Points"] += 1
                table[away]["Points"] += 1


# ================================================================
# CREATE PRESSURE DATAFRAME
# ================================================================

pressure_df = pd.DataFrame(
    pressure_results
)


# ================================================================
# SEASON PROGRESS
# ================================================================

pressure_df["HomeSeasonProgress"] = (

    38
    -
    pressure_df["HomeMatchesRemaining"]

) / 38


pressure_df["AwaySeasonProgress"] = (

    38
    -
    pressure_df["AwayMatchesRemaining"]

) / 38


# ================================================================
# MAXIMUM POINTS AVAILABLE
# ================================================================

home_max_points = (

    pressure_df[
        "HomeMatchesRemaining"
    ]

    * 3
)


away_max_points = (

    pressure_df[
        "AwayMatchesRemaining"
    ]

    * 3
)


# ================================================================
# TITLE PRESSURE
# ================================================================

pressure_df[
    "HomeTitlePressure"
] = 0.0


pressure_df[
    "AwayTitlePressure"
] = 0.0


home_can_catch = (

    pressure_df[
        "HomePointsToLeader"
    ]

    <=

    home_max_points
)


away_can_catch = (

    pressure_df[
        "AwayPointsToLeader"
    ]

    <=

    away_max_points
)


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

pressure_df[
    "HomeTop4Distance"
] = (

    pressure_df[
        "HomePointsToTop4"
    ].abs()
)


pressure_df[
    "AwayTop4Distance"
] = (

    pressure_df[
        "AwayPointsToTop4"
    ].abs()
)


home_can_compete_top4 = (

    pressure_df[
        "HomePointsToTop4"
    ]

    <=

    home_max_points
)


away_can_compete_top4 = (

    pressure_df[
        "AwayPointsToTop4"
    ]

    <=

    away_max_points
)


pressure_df[
    "HomeTop4Pressure"
] = 0.0


pressure_df[
    "AwayTop4Pressure"
] = 0.0


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

pressure_df[
    "HomeRelegationPressure"
] = (

    pressure_df[
        "HomeSeasonProgress"
    ]

    /

    (
        1
        +
        pressure_df[
            "HomeRelegationDistance"
        ]
    )
)


pressure_df[
    "AwayRelegationPressure"
] = (

    pressure_df[
        "AwaySeasonProgress"
    ]

    /

    (
        1
        +
        pressure_df[
            "AwayRelegationDistance"
        ]
    )
)


# ================================================================
# VALIDATE PRESSURE DATA
# ================================================================

print(
    "\nLeague Pressure rows:",
    len(pressure_df)
)


pressure_duplicates = (
    pressure_df
    .duplicated(
        subset=merge_keys
    )
    .sum()
)


print(
    "Duplicate League Pressure matches:",
    pressure_duplicates
)


# ================================================================
# PRESSURE COLUMNS
# ================================================================

pressure_columns = [

    "HomePointsToLeader",
    "AwayPointsToLeader",

    "HomePointsToTop4",
    "AwayPointsToTop4",

    "HomePointsAboveRelegation",
    "AwayPointsAboveRelegation",

    "HomeRelegationDistance",
    "AwayRelegationDistance",

    "HomeInRelegationZone",
    "AwayInRelegationZone",

    "HomeMatchesRemaining",
    "AwayMatchesRemaining",

    "HomeSeasonProgress",
    "AwaySeasonProgress",

    "HomeTitlePressure",
    "AwayTitlePressure",

    "HomeTop4Distance",
    "AwayTop4Distance",

    "HomeTop4Pressure",
    "AwayTop4Pressure",

    "HomeRelegationPressure",
    "AwayRelegationPressure"
]


pressure_merge_df = pressure_df[
    merge_keys
    +
    pressure_columns
].copy()


# ================================================================
# MERGE LEAGUE PRESSURE
# ================================================================

rows_before_pressure = len(df)


df = df.merge(
    pressure_merge_df,
    on=merge_keys,
    how="left",
    validate="one_to_one"
)


if len(df) != rows_before_pressure:

    raise ValueError(
        "ERROR: Match count changed after League Pressure merge!"
    )


print(
    "\nAfter League Pressure merge:"
)

print(
    "Matches:",
    len(df)
)

print(
    "Columns:",
    len(df.columns)
)


print(
    "\nMissing League Pressure values:"
)


print(
    df[
        pressure_columns
    ]
    .isnull()
    .sum()
)


# ================================================================
# FINAL STAGE 4 VALIDATION
# ================================================================

print("\n" + "=" * 60)

print(
    "FINAL STAGE 4 VALIDATION"
)

print(
    "=" * 60
)


# ================================================================
# 1. MATCH COUNT
# ================================================================

if len(df) != 1900:

    raise ValueError(
        f"Expected 1900 matches, found {len(df)}"
    )


print(
    "✅ Match count:",
    len(df)
)


# ================================================================
# 2. COLUMN COUNT
# ================================================================

if len(df.columns) != 57:

    raise ValueError(
        f"Expected 57 columns, found {len(df.columns)}"
    )


print(
    "✅ Column count:",
    len(df.columns)
)


# ================================================================
# 3. DUPLICATE MATCHES
# ================================================================

final_duplicates = df.duplicated(
    subset=merge_keys
).sum()


if final_duplicates != 0:

    raise ValueError(
        f"Found {final_duplicates} duplicate matches"
    )


print(
    "✅ Duplicate matches:",
    final_duplicates
)


# ================================================================
# 4. MATCH RESULTS
# ================================================================

valid_results = {
    "H",
    "D",
    "A"
}


actual_results = set(
    df["FTR"]
    .dropna()
    .unique()
)


if not actual_results.issubset(
    valid_results
):

    raise ValueError(
        f"Invalid FTR values: {actual_results}"
    )


print(
    "✅ Match results valid"
)


# ================================================================
# 5. GAMES PLAYED RANGE
# ================================================================

for column in [

    "HomeGamesPlayedBefore",
    "AwayGamesPlayedBefore"

]:

    if not df[column].between(
        0,
        37
    ).all():

        raise ValueError(
            f"{column} contains invalid values"
        )


print(
    "✅ Games played range: 0–37"
)


# ================================================================
# 6. LEAGUE POSITION RANGE
# ================================================================

for column in [

    "HomePositionBefore",
    "AwayPositionBefore"

]:

    if not df[column].between(
        1,
        20
    ).all():

        raise ValueError(
            f"{column} contains invalid values"
        )


print(
    "✅ League positions range: 1–20"
)


# ================================================================
# 7. LEAGUE POINTS RANGE
# ================================================================

for column in [

    "HomeLeaguePointsBefore",
    "AwayLeaguePointsBefore"

]:

    if not df[column].between(
        0,
        114
    ).all():

        raise ValueError(
            f"{column} contains invalid values"
        )


print(
    "✅ League points range valid"
)


# ================================================================
# 8. TABLE GAP CALCULATIONS
# ================================================================

expected_points_gap = (

    df[
        "HomeLeaguePointsBefore"
    ]

    -

    df[
        "AwayLeaguePointsBefore"
    ]
)


if not expected_points_gap.equals(
    df["LeaguePointsGap"]
):

    raise ValueError(
        "LeaguePointsGap calculation is incorrect"
    )


expected_games_gap = (

    df[
        "HomeGamesPlayedBefore"
    ]

    -

    df[
        "AwayGamesPlayedBefore"
    ]
)


if not expected_games_gap.equals(
    df["GamesPlayedGap"]
):

    raise ValueError(
        "GamesPlayedGap calculation is incorrect"
    )


print(
    "✅ Table gaps calculated correctly"
)


# ================================================================
# 9. H2H VALIDATION
# ================================================================

if not df[
    "H2HMatchesUsed"
].between(
    0,
    5
).all():

    raise ValueError(
        "H2HMatchesUsed must be between 0 and 5"
    )


if not (

    df["H2HMatchesUsed"]

    <=

    df["H2HMatchesBefore"]

).all():

    raise ValueError(
        "H2HMatchesUsed exceeds H2HMatchesBefore"
    )


for column in [

    "HomeH2HLast5Points",
    "AwayH2HLast5Points"

]:

    if not df[column].between(
        0,
        15
    ).all():

        raise ValueError(
            f"{column} contains invalid values"
        )


print(
    "✅ H2H feature ranges valid"
)


# ================================================================
# 10. PPG VALIDATION
# ================================================================

for column in [

    "HomeSeasonPPG",
    "AwaySeasonPPG",

    "HomeRecentPPG",
    "AwayRecentPPG"

]:

    valid_values = (
        df[column]
        .dropna()
    )


    if not valid_values.between(
        0,
        3
    ).all():

        raise ValueError(
            f"{column} must be between 0 and 3"
        )


print(
    "✅ PPG ranges valid"
)


# ================================================================
# 11. MOMENTUM FORMULA
# ================================================================

valid_momentum = df[
    [
        "HomeMomentum",
        "AwayMomentum",
        "MomentumGap"
    ]
].dropna()


momentum_difference = (

    valid_momentum[
        "HomeMomentum"
    ]

    -

    valid_momentum[
        "AwayMomentum"
    ]
)


momentum_error = (

    momentum_difference

    -

    valid_momentum[
        "MomentumGap"
    ]

).abs()


if not (
    momentum_error < 1e-9
).all():

    raise ValueError(
        "MomentumGap calculation is incorrect"
    )


print(
    "✅ Momentum calculations valid"
)


# ================================================================
# 12. FORM SWING FORMULA
# ================================================================

valid_form = df[
    [
        "SeasonStrengthGap",
        "RecentFormGap",
        "FormSwing"
    ]
].dropna()


expected_form_swing = (

    valid_form[
        "RecentFormGap"
    ]

    -

    valid_form[
        "SeasonStrengthGap"
    ]
)


form_swing_error = (

    expected_form_swing

    -

    valid_form[
        "FormSwing"
    ]

).abs()


if not (
    form_swing_error < 1e-9
).all():

    raise ValueError(
        "FormSwing calculation is incorrect"
    )


print(
    "✅ Form swing calculations valid"
)


# ================================================================
# 13. UPSET DIRECTION
# ================================================================

valid_directions = set(

    df[
        "UpsetDirection"
    ]
    .dropna()
    .unique()
)


if not valid_directions.issubset(
    {
        -1.0,
        0.0,
        1.0
    }
):

    raise ValueError(
        "UpsetDirection contains invalid values"
    )


if (

    df[
        "UpsetPotential"
    ]
    .dropna()

    < 0

).any():

    raise ValueError(
        "UpsetPotential cannot be negative"
    )


print(
    "✅ Upset Potential values valid"
)


# ================================================================
# 14. MATCHES REMAINING
# ================================================================

for column in [

    "HomeMatchesRemaining",
    "AwayMatchesRemaining"

]:

    if not df[column].between(
        1,
        38
    ).all():

        raise ValueError(
            f"{column} contains invalid values"
        )


print(
    "✅ Matches remaining range: 1–38"
)


# ================================================================
# 15. SEASON PROGRESS
# ================================================================

for column in [

    "HomeSeasonProgress",
    "AwaySeasonProgress"

]:

    if not df[column].between(
        0,
        1
    ).all():

        raise ValueError(
            f"{column} contains invalid values"
        )


print(
    "✅ Season progress range valid"
)


# ================================================================
# 16. PRESSURE FEATURE RANGE
# ================================================================

pressure_score_columns = [

    "HomeTitlePressure",
    "AwayTitlePressure",

    "HomeTop4Pressure",
    "AwayTop4Pressure",

    "HomeRelegationPressure",
    "AwayRelegationPressure"
]


for column in pressure_score_columns:

    if not df[column].between(
        0,
        1
    ).all():

        raise ValueError(
            f"{column} must be between 0 and 1"
        )


print(
    "✅ League pressure ranges valid"
)


# ================================================================
# 17. TOP-4 DISTANCE
# ================================================================

if (

    df[
        "HomeTop4Distance"
    ] < 0

).any():

    raise ValueError(
        "HomeTop4Distance cannot be negative"
    )


if (

    df[
        "AwayTop4Distance"
    ] < 0

).any():

    raise ValueError(
        "AwayTop4Distance cannot be negative"
    )


print(
    "✅ Top-4 distance values valid"
)


# ================================================================
# 18. RELEGATION DISTANCE
# ================================================================

if (

    df[
        "HomeRelegationDistance"
    ] < 0

).any():

    raise ValueError(
        "HomeRelegationDistance cannot be negative"
    )


if (

    df[
        "AwayRelegationDistance"
    ] < 0

).any():

    raise ValueError(
        "AwayRelegationDistance cannot be negative"
    )


print(
    "✅ Relegation distance values valid"
)


# ================================================================
# 19. RELEGATION STATUS
# ================================================================

for column in [

    "HomeInRelegationZone",
    "AwayInRelegationZone"

]:

    valid_values = set(
        df[column].unique()
    )


    if not valid_values.issubset(
        {
            0,
            1
        }
    ):

        raise ValueError(
            f"{column} must contain only 0 or 1"
        )


print(
    "✅ Relegation status valid"
)


# ================================================================
# 20. EXPECTED EARLY-SEASON MISSING VALUES
# ================================================================

print(
    "\nExpected early-season missing values:"
)


important_missing_columns = [

    "HomeLast5Points",
    "AwayLast5Points",

    "Last5HomePoints",
    "Last5AwayPoints",

    "HomeSeasonPPG",
    "AwaySeasonPPG",

    "HomeRecentPPG",
    "AwayRecentPPG",

    "HomeMomentum",
    "AwayMomentum",

    "MomentumGap",

    "SeasonStrengthGap",
    "RecentFormGap",

    "FormSwing",

    "UpsetPotential",
    "UpsetDirection"
]


print(
    df[
        important_missing_columns
    ]
    .isnull()
    .sum()
)


# ================================================================
# SORT FINAL DATASET
# ================================================================

df = df.sort_values(
    "Date"
).reset_index(drop=True)


# ================================================================
# SAVE FINAL STAGE 4 DATASET
# ================================================================

df.to_csv(
    output_file,
    index=False
)


# ================================================================
# FINAL SUCCESS MESSAGE
# ================================================================

print(
    "\n" + "=" * 60
)

print(
    "✅ STAGE 4 DATASET CREATED SUCCESSFULLY"
)

print(
    "=" * 60
)


print(
    "Total matches:",
    len(df)
)


print(
    "Total columns:",
    len(df.columns)
)


print(
    "Saved to:",
    output_file
)