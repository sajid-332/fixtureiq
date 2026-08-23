"""
FixtureIQ Stage 6.1
Goal Feature Engineering

Creates leakage-safe features for goal prediction.

Input:
    data/historical/processed/epl_stage5_features.csv

Output:
    data/historical/processed/epl_stage6_goal_features.csv

Rules:
    - Only use information available before each fixture
    - Never use target match goals
    - Update history only after feature creation
"""

from pathlib import Path
import pandas as pd
import numpy as np


# -------------------------------------------------
# Paths
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]


INPUT_FILE = (
    BASE_DIR
    / "data"
    / "historical"
    / "processed"
    / "epl_stage5_features.csv"
)


OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "historical"
    / "processed"
    / "epl_stage6_goal_features.csv"
)


# -------------------------------------------------
# Configuration
# -------------------------------------------------

WINDOW = 5


# -------------------------------------------------
# Helper functions
# -------------------------------------------------

def safe_average(values):
    """
    Return average.
    If no previous history exists, return NaN.
    """

    if len(values) == 0:
        return np.nan

    return np.mean(values)



def calculate_team_goal_history(history):
    """
    Calculate overall team goal statistics.

    Includes:
    - goals scored
    - goals conceded
    - goal difference
    """

    goals_for = [
        x["gf"]
        for x in history
    ]

    goals_against = [
        x["ga"]
        for x in history
    ]


    return {

        "avg_goals_for":
            safe_average(
                goals_for[-WINDOW:]
            ),


        "avg_goals_against":
            safe_average(
                goals_against[-WINDOW:]
            ),


        "goal_difference":
            safe_average(
                [
                    x["gf"] - x["ga"]
                    for x in history[-WINDOW:]
                ]
            )
    }



def calculate_venue_goal_history(history):
    """
    Calculate venue-specific goal statistics.

    Example:

    Home team:
        previous home matches only

    Away team:
        previous away matches only
    """

    goals_for = [
        x["gf"]
        for x in history
    ]

    goals_against = [
        x["ga"]
        for x in history
    ]


    return {

        "avg_goals_for":
            safe_average(
                goals_for[-WINDOW:]
            ),


        "avg_goals_against":
            safe_average(
                goals_against[-WINDOW:]
            )
    }



# -------------------------------------------------
# Main Builder
# -------------------------------------------------

def build_goal_features():


    print("Loading Stage 5 dataset...")


    df = pd.read_csv(INPUT_FILE)


    df["Date"] = pd.to_datetime(
        df["Date"]
    )


    df = (
        df
        .sort_values("Date")
        .reset_index(drop=True)
    )


    # ---------------------------------------------
    # History containers
    # ---------------------------------------------

    # All matches
    team_history = {}


    # Home matches only
    home_venue_history = {}


    # Away matches only
    away_venue_history = {}


    rows = []


    print("Creating Stage 6 goal features...")


    for _, match in df.iterrows():


        home = match["HomeTeam"]

        away = match["AwayTeam"]



        # -----------------------------------------
        # BEFORE MATCH FEATURE CREATION
        # -----------------------------------------

        home_history = (
            team_history
            .get(home, [])
        )


        away_history = (
            team_history
            .get(away, [])
        )


        home_home_history = (
            home_venue_history
            .get(home, [])
        )


        away_away_history = (
            away_venue_history
            .get(away, [])
        )



        home_stats = calculate_team_goal_history(
            home_history
        )


        away_stats = calculate_team_goal_history(
            away_history
        )


        home_venue_stats = calculate_venue_goal_history(
            home_home_history
        )


        away_venue_stats = calculate_venue_goal_history(
            away_away_history
        )



        feature_row = match.to_dict()



        # -----------------------------------------
        # General Goal Features
        # -----------------------------------------

        feature_row.update({

            "HomeAvgGoalsScoredLast5":
                home_stats["avg_goals_for"],


            "HomeAvgGoalsConcededLast5":
                home_stats["avg_goals_against"],


            "HomeGoalDifferenceLast5":
                home_stats["goal_difference"],



            "AwayAvgGoalsScoredLast5":
                away_stats["avg_goals_for"],


            "AwayAvgGoalsConcededLast5":
                away_stats["avg_goals_against"],


            "AwayGoalDifferenceLast5":
                away_stats["goal_difference"]

        })



        # -----------------------------------------
        # Venue Goal Features
        # -----------------------------------------

        feature_row.update({

            "HomeVenueGoalsScoredLast5":
                home_venue_stats["avg_goals_for"],


            "HomeVenueGoalsConcededLast5":
                home_venue_stats["avg_goals_against"],



            "AwayVenueGoalsScoredLast5":
                away_venue_stats["avg_goals_for"],


            "AwayVenueGoalsConcededLast5":
                away_venue_stats["avg_goals_against"]

        })



        # -----------------------------------------
        # Match Comparison Features
        # -----------------------------------------

        feature_row.update({


            "AttackStrengthDifference":

                (
                    home_stats["avg_goals_for"]
                    -
                    away_stats["avg_goals_for"]
                ),



            "DefenseStrengthDifference":

                (
                    away_stats["avg_goals_against"]
                    -
                    home_stats["avg_goals_against"]
                ),



            "GoalDifferenceStrengthGap":

                (
                    home_stats["goal_difference"]
                    -
                    away_stats["goal_difference"]
                ),



            "HomeAttackAwayDefenseGap":

                (
                    home_venue_stats["avg_goals_for"]
                    -
                    away_venue_stats["avg_goals_against"]
                ),



            "AwayAttackHomeDefenseGap":

                (
                    away_venue_stats["avg_goals_for"]
                    -
                    home_venue_stats["avg_goals_against"]
                )

        })



        rows.append(feature_row)



        # -----------------------------------------
        # AFTER MATCH UPDATE
        # -----------------------------------------

        # Current match goals become available
        # only after prediction point


        if (
            pd.notna(match["FTHG"])
            and
            pd.notna(match["FTAG"])
        ):


            # Overall history

            team_history.setdefault(
                home,
                []
            ).append({

                "gf": match["FTHG"],
                "ga": match["FTAG"]

            })


            team_history.setdefault(
                away,
                []
            ).append({

                "gf": match["FTAG"],
                "ga": match["FTHG"]

            })



            # Home venue history

            home_venue_history.setdefault(
                home,
                []
            ).append({

                "gf": match["FTHG"],
                "ga": match["FTAG"]

            })



            # Away venue history

            away_venue_history.setdefault(
                away,
                []
            ).append({

                "gf": match["FTAG"],
                "ga": match["FTHG"]

            })



    result = pd.DataFrame(rows)



    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    result.to_csv(
        OUTPUT_FILE,
        index=False
    )



    print("\nStage 6.1 Goal Feature Engineering Complete")
    print("-----------------------------------------")
    print(f"Matches: {len(result)}")
    print(f"Columns: {len(result.columns)}")
    print(f"Saved: {OUTPUT_FILE}")



    print("\nAdded Goal Features:")


    new_features = [

        "HomeAvgGoalsScoredLast5",
        "HomeAvgGoalsConcededLast5",
        "HomeGoalDifferenceLast5",

        "AwayAvgGoalsScoredLast5",
        "AwayAvgGoalsConcededLast5",
        "AwayGoalDifferenceLast5",

        "HomeVenueGoalsScoredLast5",
        "HomeVenueGoalsConcededLast5",

        "AwayVenueGoalsScoredLast5",
        "AwayVenueGoalsConcededLast5",

        "AttackStrengthDifference",
        "DefenseStrengthDifference",
        "GoalDifferenceStrengthGap",

        "HomeAttackAwayDefenseGap",
        "AwayAttackHomeDefenseGap"

    ]


    for feature in new_features:
        print("-", feature)



if __name__ == "__main__":

    build_goal_features()