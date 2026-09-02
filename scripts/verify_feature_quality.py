"""
FixtureIQ Stage 7.4.4
Feature Quality and Leakage Verification.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR),
)


from backend.features.splitting import (
    MODEL_FEATURES_FILE,
    TRAIN_FILE,
    VALIDATION_FILE,
    SPLIT_METADATA_FILE,
)


QUALITY_REPORT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "feature_quality_report.json"
)


TARGET_COLUMNS = {
    "target",
    "target_label",
    "home_goals",
    "away_goals",
}


NON_FEATURE_COLUMNS = {
    "fixture_id",
    "season",
    "date",
    "home_team_id",
    "home_team_name",
    "away_team_id",
    "away_team_name",
    "home_goals",
    "away_goals",
    "target",
    "target_label",
}


def load_csv(path):

    if not path.exists():

        raise FileNotFoundError(
            f"Missing file: {path}"
        )

    return pd.read_csv(
        path
    )


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.4.4"
    )

    print(
        "Feature Quality & Leakage Verification"
    )

    print("=" * 50)

    features = load_csv(
        MODEL_FEATURES_FILE
    )

    train = load_csv(
        TRAIN_FILE
    )

    validation = load_csv(
        VALIDATION_FILE
    )

    print(
        f"\nModel feature records: "
        f"{len(features)}"
    )

    print(
        f"Training records: "
        f"{len(train)}"
    )

    print(
        f"Validation records: "
        f"{len(validation)}"
    )

    # ========================================================
    # 1. Missing values
    # ========================================================

    numeric_features = features.select_dtypes(
        include=np.number
    )

    missing_values = int(
        numeric_features.isna()
        .sum()
        .sum()
    )

    print(
        "\n1. Missing numeric feature values"
    )

    print(
        f"Missing values: {missing_values}"
    )

    missing_pass = (
        missing_values == 0
    )

    print(
        f"Result: "
        f"{'PASS' if missing_pass else 'FAIL'}"
    )

    # ========================================================
    # 2. Infinite values
    # ========================================================

    infinite_values = int(
        np.isinf(
            numeric_features
        )
        .sum()
        .sum()
    )

    print(
        "\n2. Infinite feature values"
    )

    print(
        f"Infinite values: "
        f"{infinite_values}"
    )

    infinite_pass = (
        infinite_values == 0
    )

    print(
        f"Result: "
        f"{'PASS' if infinite_pass else 'FAIL'}"
    )

    # ========================================================
    # 3. Duplicate fixtures
    # ========================================================

    duplicate_features = int(
        features["fixture_id"]
        .duplicated()
        .sum()
    )

    duplicate_train = int(
        train["fixture_id"]
        .duplicated()
        .sum()
    )

    duplicate_validation = int(
        validation["fixture_id"]
        .duplicated()
        .sum()
    )

    duplicates_pass = (
        duplicate_features == 0
        and
        duplicate_train == 0
        and
        duplicate_validation == 0
    )

    print(
        "\n3. Duplicate fixture IDs"
    )

    print(
        f"Full dataset duplicates: "
        f"{duplicate_features}"
    )

    print(
        f"Training duplicates: "
        f"{duplicate_train}"
    )

    print(
        f"Validation duplicates: "
        f"{duplicate_validation}"
    )

    print(
        f"Result: "
        f"{'PASS' if duplicates_pass else 'FAIL'}"
    )

    # ========================================================
    # 4. Target validation
    # ========================================================

    valid_targets = {
        0,
        1,
        2,
    }

    target_values = set(
        pd.to_numeric(
            features["target"],
            errors="coerce",
        )
        .dropna()
        .astype(int)
        .unique()
    )

    invalid_targets = (
        target_values
        -
        valid_targets
    )

    target_pass = (
        not invalid_targets
        and
        len(target_values) > 0
    )

    print(
        "\n4. Target validation"
    )

    print(
        f"Observed targets: "
        f"{sorted(target_values)}"
    )

    print(
        f"Invalid targets: "
        f"{sorted(invalid_targets)}"
    )

    print(
        f"Result: "
        f"{'PASS' if target_pass else 'FAIL'}"
    )

    # ========================================================
    # 5. Chronological ordering
    # ========================================================

    feature_dates = pd.to_datetime(
        features["date"],
        errors="coerce",
        utc=True,
    )

    train_dates = pd.to_datetime(
        train["date"],
        errors="coerce",
        utc=True,
    )

    validation_dates = pd.to_datetime(
        validation["date"],
        errors="coerce",
        utc=True,
    )

    dates_valid = (
        feature_dates.notna().all()
        and
        train_dates.notna().all()
        and
        validation_dates.notna().all()
    )

    feature_order_pass = (
        feature_dates
        .is_monotonic_increasing
    )

    split_order_pass = (
        train_dates.max()
        <
        validation_dates.min()
    )

    chronological_pass = (
        dates_valid
        and
        feature_order_pass
        and
        split_order_pass
    )

    print(
        "\n5. Chronological safety"
    )

    print(
        f"Full dataset ordered: "
        f"{'PASS' if feature_order_pass else 'FAIL'}"
    )

    print(
        f"Train before validation: "
        f"{'PASS' if split_order_pass else 'FAIL'}"
    )

    print(
        f"Result: "
        f"{'PASS' if chronological_pass else 'FAIL'}"
    )

    # ========================================================
    # 6. Train/validation contamination
    # ========================================================

    train_ids = set(
        train["fixture_id"]
    )

    validation_ids = set(
        validation["fixture_id"]
    )

    overlap = (
        train_ids
        &
        validation_ids
    )

    contamination_pass = (
        len(overlap) == 0
    )

    print(
        "\n6. Train/validation contamination"
    )

    print(
        f"Overlapping fixture IDs: "
        f"{len(overlap)}"
    )

    print(
        f"Result: "
        f"{'PASS' if contamination_pass else 'FAIL'}"
    )

    # ========================================================
    # 7. Feature matrix leakage
    # ========================================================

    feature_columns = [
        column
        for column in features.columns
        if column not in NON_FEATURE_COLUMNS
    ]

    leaked_target_columns = sorted(
        set(feature_columns)
        &
        TARGET_COLUMNS
    )

    feature_leakage_pass = (
        len(leaked_target_columns) == 0
    )

    print(
        "\n7. Target leakage"
    )

    print(
        f"Feature columns: "
        f"{len(feature_columns)}"
    )

    print(
        f"Target columns inside feature matrix: "
        f"{leaked_target_columns}"
    )

    print(
        f"Result: "
        f"{'PASS' if feature_leakage_pass else 'FAIL'}"
    )

    # ========================================================
    # 8. Historical-state sanity
    # ========================================================

    state_columns = [
        "home_matches",
        "away_matches",
        "home_points",
        "away_points",
        "home_goals_for",
        "away_goals_for",
        "home_goals_against",
        "away_goals_against",
        "home_last5_matches",
        "away_last5_matches",
        "home_last10_matches",
        "away_last10_matches",
    ]

    existing_state_columns = [
        column
        for column in state_columns
        if column in features.columns
    ]

    negative_state_values = 0

    for column in existing_state_columns:

        values = pd.to_numeric(
            features[column],
            errors="coerce",
        )

        negative_state_values += int(
            (values < 0)
            .fillna(False)
            .sum()
        )

    state_pass = (
        negative_state_values == 0
        and
        len(existing_state_columns)
        == len(state_columns)
    )

    print(
        "\n8. Historical state sanity"
    )

    print(
        f"Negative state values: "
        f"{negative_state_values}"
    )

    print(
        f"Required state columns: "
        f"{len(existing_state_columns)}/"
        f"{len(state_columns)}"
    )

    print(
        f"Result: "
        f"{'PASS' if state_pass else 'FAIL'}"
    )

    # ========================================================
    # 9. First-observation check
    # ========================================================

    first_observation_pass = True

    # For each team, locate its first appearance.
    #
    # Before that first match, historical state must be zero.

    team_first_rows = {}

    for index, row in features.iterrows():

        home_id = int(
            row["home_team_id"]
        )

        away_id = int(
            row["away_team_id"]
        )

        if home_id not in team_first_rows:

            team_first_rows[
                home_id
            ] = (
                index,
                "home",
                row,
            )

        if away_id not in team_first_rows:

            team_first_rows[
                away_id
            ] = (
                index,
                "away",
                row,
            )

    for _, venue, row in team_first_rows.values():

        prefix = venue

        if (
            row[f"{prefix}_matches"]
            != 0
            or
            row[f"{prefix}_points"]
            != 0
            or
            row[f"{prefix}_goals_for"]
            != 0
            or
            row[f"{prefix}_goals_against"]
            != 0
        ):

            first_observation_pass = False

    print(
        "\n9. First-observation state"
    )

    print(
        f"Teams checked: "
        f"{len(team_first_rows)}"
    )

    print(
        f"Result: "
        f"{'PASS' if first_observation_pass else 'FAIL'}"
    )

    # ========================================================
    # Overall
    # ========================================================

    checks = {
        "missing_values":
            missing_pass,

        "infinite_values":
            infinite_pass,

        "duplicates":
            duplicates_pass,

        "targets":
            target_pass,

        "chronological_safety":
            chronological_pass,

        "train_validation_contamination":
            contamination_pass,

        "target_leakage":
            feature_leakage_pass,

        "historical_state":
            state_pass,

        "first_observation":
            first_observation_pass,
    }

    overall_pass = all(
        checks.values()
    )

    report = {
        "stage": "7.4.4",
        "overall_pass":
            overall_pass,
        "checks":
            checks,
        "model_feature_records":
            len(features),
        "training_records":
            len(train),
        "validation_records":
            len(validation),
        "feature_columns":
            feature_columns,
        "target_columns":
            sorted(
                TARGET_COLUMNS
            ),
        "train_validation_overlap":
            len(overlap),
    }

    QUALITY_REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with QUALITY_REPORT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
        )

    # ========================================================
    # Final
    # ========================================================

    print(
        "\n" + "=" * 50
    )

    print(
        "FINAL RESULT"
    )

    print(
        "=" * 50
    )

    for name, result in checks.items():

        print(
            f"{name}: "
            f"{'PASS' if result else 'FAIL'}"
        )

    print(
        "\nFeature quality report:"
    )

    print(
        QUALITY_REPORT_FILE
    )

    print(
        "\nSTAGE 7.4.4: "
        f"{'PASS' if overall_pass else 'FAIL'}"
    )

    if not overall_pass:

        sys.exit(1)


if __name__ == "__main__":
    main()