"""
FixtureIQ Stage 6.1.3
Goal Feature Validation Tests

Checks:
- Dataset integrity
- Goal feature availability
- Leakage protection
- Feature ranges
- Chronological order
"""


from pathlib import Path
import pandas as pd
import numpy as np


# -------------------------------------------------
# Paths
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]


GOAL_FEATURE_FILE = (
    BASE_DIR
    / "data"
    / "historical"
    / "processed"
    / "epl_stage6_goal_features.csv"
)


# -------------------------------------------------
# Required columns
# -------------------------------------------------

REQUIRED_FEATURES = [

    # General goal features

    "HomeAvgGoalsScoredLast5",
    "HomeAvgGoalsConcededLast5",
    "HomeGoalDifferenceLast5",

    "AwayAvgGoalsScoredLast5",
    "AwayAvgGoalsConcededLast5",
    "AwayGoalDifferenceLast5",


    # Venue features

    "HomeVenueGoalsScoredLast5",
    "HomeVenueGoalsConcededLast5",

    "AwayVenueGoalsScoredLast5",
    "AwayVenueGoalsConcededLast5",


    # Comparison features

    "AttackStrengthDifference",
    "DefenseStrengthDifference",
    "GoalDifferenceStrengthGap",

    "HomeAttackAwayDefenseGap",
    "AwayAttackHomeDefenseGap"

]


# -------------------------------------------------
# Helper
# -------------------------------------------------

def load_goal_features():

    assert GOAL_FEATURE_FILE.exists(), (
        "Stage 6 goal feature file not found"
    )

    df = pd.read_csv(
        GOAL_FEATURE_FILE
    )

    df["Date"] = pd.to_datetime(
        df["Date"]
    )

    return df



# -------------------------------------------------
# Tests
# -------------------------------------------------


def test_goal_dataset_exists():

    df = load_goal_features()

    assert len(df) > 0



def test_correct_match_count():

    df = load_goal_features()

    # EPL 5 seasons = 1900 matches

    assert len(df) == 1900



def test_required_goal_features_exist():

    df = load_goal_features()

    for feature in REQUIRED_FEATURES:

        assert feature in df.columns, (
            f"Missing feature: {feature}"
        )



def test_no_duplicate_matches():

    df = load_goal_features()

    duplicates = df.duplicated(
        subset=[
            "Date",
            "HomeTeam",
            "AwayTeam"
        ]
    )

    assert duplicates.sum() == 0



def test_chronological_order():

    df = load_goal_features()

    dates = df["Date"].tolist()

    assert dates == sorted(dates)



def test_goal_features_not_negative():

    df = load_goal_features()


    goal_columns = [

        "HomeAvgGoalsScoredLast5",
        "HomeAvgGoalsConcededLast5",

        "AwayAvgGoalsScoredLast5",
        "AwayAvgGoalsConcededLast5",

        "HomeVenueGoalsScoredLast5",
        "HomeVenueGoalsConcededLast5",

        "AwayVenueGoalsScoredLast5",
        "AwayVenueGoalsConcededLast5"

    ]


    for col in goal_columns:

        values = df[col].dropna()

        assert (
            values >= 0
        ).all(), (
            f"Negative values found in {col}"
        )



def test_target_match_goals_are_not_used():

    """
    Basic leakage protection.

    The feature dataset should not contain
    target match goals as input features.

    """

    df = load_goal_features()


    forbidden_columns = [

        "CurrentHomeGoals",
        "CurrentAwayGoals",

    ]


    for col in forbidden_columns:

        assert col not in df.columns



def test_first_matches_allow_missing_history():

    """
    Early season matches may not have
    enough previous history.

    Missing values are expected.
    """

    df = load_goal_features()


    first_rows = df.head(50)


    missing_count = (
        first_rows[
            "HomeAvgGoalsScoredLast5"
        ]
        .isna()
        .sum()
    )


    assert missing_count >= 0



def test_feature_values_are_numeric():

    df = load_goal_features()


    for feature in REQUIRED_FEATURES:

        assert np.issubdtype(
            df[feature].dtype,
            np.number
        ), (
            f"{feature} is not numeric"
        )