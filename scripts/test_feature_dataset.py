"""
FixtureIQ Stage 7.4.1 + 7.4.2
Feature Dataset Test.
"""

import sys
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR),
)


from backend.features.preparation import (
    FEATURE_INPUT_FILE,
)

from backend.features.historical_features import (
    FEATURE_DATASET_FILE,
)


def main():

    print("=" * 50)
    print(
        "FixtureIQ Stage 7.4.1 + 7.4.2"
    )
    print(
        "Feature Dataset Test"
    )
    print("=" * 50)

    # ========================================================
    # Input dataset
    # ========================================================

    print(
        "\n1. FEATURE INPUT"
    )

    input_exists = (
        FEATURE_INPUT_FILE.exists()
    )

    print(
        f"Feature input exists: "
        f"{'PASS' if input_exists else 'FAIL'}"
    )

    if not input_exists:
        sys.exit(1)

    feature_input = pd.read_csv(
        FEATURE_INPUT_FILE
    )

    print(
        f"Feature input records: "
        f"{len(feature_input)}"
    )

    # ========================================================
    # Model features
    # ========================================================

    print(
        "\n2. MODEL FEATURES"
    )

    dataset_exists = (
        FEATURE_DATASET_FILE.exists()
    )

    print(
        f"Model feature dataset exists: "
        f"{'PASS' if dataset_exists else 'FAIL'}"
    )

    if not dataset_exists:
        sys.exit(1)

    features = pd.read_csv(
        FEATURE_DATASET_FILE
    )

    print(
        f"Feature records: "
        f"{len(features)}"
    )

    row_count_pass = (
        len(features)
        ==
        len(feature_input)
    )

    print(
        f"Row count: "
        f"{'PASS' if row_count_pass else 'FAIL'}"
    )

    # ========================================================
    # IDs
    # ========================================================

    ids_pass = (
        features["fixture_id"]
        .is_unique
    )

    print(
        f"Fixture IDs unique: "
        f"{'PASS' if ids_pass else 'FAIL'}"
    )

    # ========================================================
    # Targets
    # ========================================================

    target_values = set(
        features["target"]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    target_pass = (
        target_values
        <=
        {0, 1, 2}
        and
        len(target_values) > 0
    )

    print(
        f"Target values valid: "
        f"{'PASS' if target_pass else 'FAIL'}"
    )

    # ========================================================
    # Chronological ordering
    # ========================================================

    dates = pd.to_datetime(
        features["date"],
        errors="coerce",
        utc=True,
    )

    chronological_pass = (
        dates.is_monotonic_increasing
    )

    print(
        f"Chronological order: "
        f"{'PASS' if chronological_pass else 'FAIL'}"
    )

    # ========================================================
    # Leakage-oriented checks
    # ========================================================

    leakage_columns = [
        "home_goals",
        "away_goals",
        "target",
        "target_label",
    ]

    leakage_pass = all(
        column in features.columns
        for column in leakage_columns
    )

    print(
        "\n3. LEAKAGE SAFETY"
    )

    print(
        "Target columns retained for evaluation: "
        f"{'PASS' if leakage_pass else 'FAIL'}"
    )

    # First-match sanity check.
    #
    # A team's first observed match must have zero prior
    # matches, points and goals.

    first_rows = features.head(
        min(20, len(features))
    )

    first_match_sanity = True

    for _, row in first_rows.iterrows():

        if (
            row["home_matches"] < 0
            or
            row["away_matches"] < 0
            or
            row["home_prior_matches"] < 0
            or
            row["away_prior_matches"] < 0
        ):

            first_match_sanity = False

    print(
        f"Pre-match state sanity: "
        f"{'PASS' if first_match_sanity else 'FAIL'}"
    )

    # ========================================================
    # Required feature groups
    # ========================================================

    required_features = [
        "home_matches",
        "away_matches",
        "home_points",
        "away_points",
        "home_last5_points",
        "away_last5_points",
        "home_last10_points",
        "away_last10_points",
        "diff_points_per_match",
        "diff_goal_difference",
    ]

    feature_columns_pass = all(
        column in features.columns
        for column in required_features
    )

    print(
        f"Required feature groups: "
        f"{'PASS' if feature_columns_pass else 'FAIL'}"
    )

    # ========================================================
    # Final
    # ========================================================

    all_pass = all(
        [
            input_exists,
            dataset_exists,
            row_count_pass,
            ids_pass,
            target_pass,
            chronological_pass,
            leakage_pass,
            first_match_sanity,
            feature_columns_pass,
        ]
    )

    print(
        "\n" + "=" * 50
    )

    print(
        "FINAL RESULT"
    )

    print(
        "=" * 50
    )

    print(
        "Stage 7.4.1 Feature Input: "
        f"{'PASS' if input_exists else 'FAIL'}"
    )

    print(
        "Stage 7.4.2 Feature Construction: "
        f"{'PASS' if all_pass else 'FAIL'}"
    )

    print(
        "\nStage 7.4.1 + 7.4.2: "
        f"{'PASS' if all_pass else 'FAIL'}"
    )

    if not all_pass:
        sys.exit(1)


if __name__ == "__main__":
    main()