"""
FixtureIQ Stage 6.1
Goal Feature Engineering

Creates leakage-safe goal prediction features.

Input:
    data/historical/processed/epl_stage5_features.csv

Output:
    data/historical/processed/epl_stage6_goal_features.csv

Rules:
    - Only use information available before each fixture
    - Never use target match goals
    - Maintain chronological order
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
    Calculate average.
    Returns NaN if no history exists.
    """
    if len(values) == 0:
        return np.nan

    return np.mean(values)



def calculate_team_goal_history(team_history):
    """
    Convert team history into goal statistics.
    """

    goals_for = [x["gf"] for x in team_history]
    goals_against = [x["ga"] for x in team_history]

    return {
        "avg_goals_for":
            safe_average(goals_for[-WINDOW:]),

        "avg_goals_against":
            safe_average(goals_against[-WINDOW:]),

        "goal_difference":
            safe_average(
                [
                    x["gf"] - x["ga"]
                    for x in team_history[-WINDOW:]
                ]
            )
    }



# -------------------------------------------------
# Main feature builder
# -------------------------------------------------

def build_goal_features():

    print("Loading Stage 5 dataset...")

    df = pd.read_csv(INPUT_FILE)

    df["Date"] = pd.to_datetime(df["Date"])

    df = (
        df
        .sort_values("Date")
        .reset_index(drop=True)
    )


    # Store previous team information

    team_history = {}


    rows = []


    print("Creating goal features...")


    for _, match in df.iterrows():

        home = match["HomeTeam"]
        away = match["AwayTeam"]


        # -----------------------------------------
        # Before-match features
        # -----------------------------------------

        home_history = team_history.get(home, [])

        away_history = team_history.get(away, [])


        home_stats = calculate_team_goal_history(
            home_history
        )

        away_stats = calculate_team_goal_history(
            away_history
        )


        feature_row = match.to_dict()


        # Home goal features

        feature_row.update({

            "HomeAvgGoalsScoredLast5":
                home_stats["avg_goals_for"],

            "HomeAvgGoalsConcededLast5":
                home_stats["avg_goals_against"],

            "HomeGoalDifferenceLast5":
                home_stats["goal_difference"],

        })


        # Away goal features

        feature_row.update({

            "AwayAvgGoalsScoredLast5":
                away_stats["avg_goals_for"],

            "AwayAvgGoalsConcededLast5":
                away_stats["avg_goals_against"],

            "AwayGoalDifferenceLast5":
                away_stats["goal_difference"],

        })


        # Comparison features

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
                )

        })


        rows.append(feature_row)



        # -----------------------------------------
        # After-match update
        # -----------------------------------------

        # Only now add current match goals

        if pd.notna(match["FTHG"]) and pd.notna(match["FTAG"]):

            team_history.setdefault(home, []).append({

                "gf": match["FTHG"],
                "ga": match["FTAG"]

            })


            team_history.setdefault(away, []).append({

                "gf": match["FTAG"],
                "ga": match["FTHG"]

            })


    result = pd.DataFrame(rows)


    # Save

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    result.to_csv(
        OUTPUT_FILE,
        index=False
    )


    print("\nStage 6.1 completed")
    print("-------------------")
    print(f"Matches: {len(result)}")
    print(f"Columns: {len(result.columns)}")
    print(
        f"Saved: {OUTPUT_FILE}"
    )


    print("\nNew goal features:")

    goal_features = [

        "HomeAvgGoalsScoredLast5",
        "HomeAvgGoalsConcededLast5",
        "HomeGoalDifferenceLast5",

        "AwayAvgGoalsScoredLast5",
        "AwayAvgGoalsConcededLast5",
        "AwayGoalDifferenceLast5",

        "AttackStrengthDifference",
        "DefenseStrengthDifference",
        "GoalDifferenceStrengthGap"

    ]


    for col in goal_features:
        print("-", col)



if __name__ == "__main__":

    build_goal_features()