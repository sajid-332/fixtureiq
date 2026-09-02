"""
FixtureIQ Stage 7.4.6
Full Feature Pipeline Verification.
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


from backend.features.model_ready import (
    MODEL_DIR,
    X_TRAIN_FILE,
    Y_TRAIN_FILE,
    X_VALIDATION_FILE,
    Y_VALIDATION_FILE,
    FEATURE_SCHEMA_FILE,
    DATASET_METADATA_FILE,
)

from backend.features.splitting import (
    MODEL_FEATURES_FILE,
    TRAIN_FILE,
    VALIDATION_FILE,
)


QUALITY_REPORT = (
    BASE_DIR
    / "data"
    / "processed"
    / "feature_quality_report.json"
)


FINAL_REPORT = (
    BASE_DIR
    / "data"
    / "processed"
    / "stage7_4_final_report.json"
)


PROHIBITED_FEATURES = {
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

    return pd.read_csv(path)


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.4.6"
    )

    print(
        "Full Feature Pipeline Verification"
    )

    print("=" * 50)

    checks = {}

    # ========================================================
    # 1. Source files
    # ========================================================

    print(
        "\n1. SOURCE DATA"
    )

    checks[
        "model_features"
    ] = MODEL_FEATURES_FILE.exists()

    checks[
        "train_features"
    ] = TRAIN_FILE.exists()

    checks[
        "validation_features"
    ] = VALIDATION_FILE.exists()

    print(
        f"Model features: "
        f"{'PASS' if checks['model_features'] else 'FAIL'}"
    )

    print(
        f"Training features: "
        f"{'PASS' if checks['train_features'] else 'FAIL'}"
    )

    print(
        f"Validation features: "
        f"{'PASS' if checks['validation_features'] else 'FAIL'}"
    )

    # ========================================================
    # 2. Model-ready files
    # ========================================================

    print(
        "\n2. MODEL-READY FILES"
    )

    model_files = {
        "X_train": X_TRAIN_FILE,
        "y_train": Y_TRAIN_FILE,
        "X_validation": X_VALIDATION_FILE,
        "y_validation": Y_VALIDATION_FILE,
        "feature_schema": FEATURE_SCHEMA_FILE,
        "dataset_metadata":
            DATASET_METADATA_FILE,
    }

    for name, path in model_files.items():

        result = path.exists()

        checks[
            f"file_{name}"
        ] = result

        print(
            f"{name}: "
            f"{'PASS' if result else 'FAIL'}"
        )

    # Stop if fundamental files are missing.

    if not all(
        checks.values()
    ):

        print(
            "\nSTAGE 7.4.6: FAIL"
        )

        sys.exit(1)

    # ========================================================
    # Load
    # ========================================================

    X_train = load_csv(
        X_TRAIN_FILE
    )

    y_train = load_csv(
        Y_TRAIN_FILE
    )

    X_validation = load_csv(
        X_VALIDATION_FILE
    )

    y_validation = load_csv(
        Y_VALIDATION_FILE
    )

    train_full = load_csv(
        TRAIN_FILE
    )

    validation_full = load_csv(
        VALIDATION_FILE
    )

    # ========================================================
    # 3. Row counts
    # ========================================================

    print(
        "\n3. ROW COUNTS"
    )

    train_count_pass = (
        len(X_train)
        ==
        len(y_train)
        ==
        len(train_full)
    )

    validation_count_pass = (
        len(X_validation)
        ==
        len(y_validation)
        ==
        len(validation_full)
    )

    checks[
        "training_row_count"
    ] = train_count_pass

    checks[
        "validation_row_count"
    ] = validation_count_pass

    print(
        f"Training: "
        f"{len(X_train)} "
        f"{'PASS' if train_count_pass else 'FAIL'}"
    )

    print(
        f"Validation: "
        f"{len(X_validation)} "
        f"{'PASS' if validation_count_pass else 'FAIL'}"
    )

    # ========================================================
    # 4. Fixture ID alignment
    # ========================================================

    print(
        "\n4. TARGET ALIGNMENT"
    )

    train_id_alignment = (
        X_train.index.equals(
            y_train.index
        )
    )

    validation_id_alignment = (
        X_validation.index.equals(
            y_validation.index
        )
    )

    checks[
        "training_target_alignment"
    ] = train_id_alignment

    checks[
        "validation_target_alignment"
    ] = validation_id_alignment

    print(
        f"Training target alignment: "
        f"{'PASS' if train_id_alignment else 'FAIL'}"
    )

    print(
        f"Validation target alignment: "
        f"{'PASS' if validation_id_alignment else 'FAIL'}"
    )

    # ========================================================
    # 5. Feature schema
    # ========================================================

    print(
        "\n5. FEATURE SCHEMA"
    )

    with FEATURE_SCHEMA_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        schema = json.load(file)

    schema_features = schema[
        "feature_columns"
    ]

    train_schema_pass = (
        list(X_train.columns)
        ==
        schema_features
    )

    validation_schema_pass = (
        list(X_validation.columns)
        ==
        schema_features
    )

    same_columns_pass = (
        list(X_train.columns)
        ==
        list(X_validation.columns)
    )

    checks[
        "training_schema"
    ] = train_schema_pass

    checks[
        "validation_schema"
    ] = validation_schema_pass

    checks[
        "same_feature_columns"
    ] = same_columns_pass

    print(
        f"Training schema: "
        f"{'PASS' if train_schema_pass else 'FAIL'}"
    )

    print(
        f"Validation schema: "
        f"{'PASS' if validation_schema_pass else 'FAIL'}"
    )

    print(
        f"Train/validation columns identical: "
        f"{'PASS' if same_columns_pass else 'FAIL'}"
    )

    # ========================================================
    # 6. Leakage check
    # ========================================================

    print(
        "\n6. TARGET / METADATA LEAKAGE"
    )

    prohibited_in_train = sorted(
        set(X_train.columns)
        &
        PROHIBITED_FEATURES
    )

    prohibited_in_validation = sorted(
        set(X_validation.columns)
        &
        PROHIBITED_FEATURES
    )

    leakage_pass = (
        not prohibited_in_train
        and
        not prohibited_in_validation
    )

    checks[
        "feature_leakage"
    ] = leakage_pass

    print(
        f"Prohibited columns in X_train: "
        f"{prohibited_in_train}"
    )

    print(
        f"Prohibited columns in X_validation: "
        f"{prohibited_in_validation}"
    )

    print(
        f"Result: "
        f"{'PASS' if leakage_pass else 'FAIL'}"
    )

    # ========================================================
    # 7. Numeric integrity
    # ========================================================

    print(
        "\n7. NUMERIC INTEGRITY"
    )

    train_numeric = X_train.select_dtypes(
        include=np.number
    )

    validation_numeric = (
        X_validation.select_dtypes(
            include=np.number
        )
    )

    train_nan = int(
        train_numeric.isna()
        .sum()
        .sum()
    )

    validation_nan = int(
        validation_numeric.isna()
        .sum()
        .sum()
    )

    train_inf = int(
        np.isinf(
            train_numeric.to_numpy()
        ).sum()
    )

    validation_inf = int(
        np.isinf(
            validation_numeric.to_numpy()
        ).sum()
    )

    numeric_pass = (
        train_nan == 0
        and
        validation_nan == 0
        and
        train_inf == 0
        and
        validation_inf == 0
    )

    checks[
        "numeric_integrity"
    ] = numeric_pass

    print(
        f"Training NaN: {train_nan}"
    )

    print(
        f"Validation NaN: {validation_nan}"
    )

    print(
        f"Training infinite: {train_inf}"
    )

    print(
        f"Validation infinite: {validation_inf}"
    )

    print(
        f"Result: "
        f"{'PASS' if numeric_pass else 'FAIL'}"
    )

    # ========================================================
    # 8. Target integrity
    # ========================================================

    print(
        "\n8. TARGET INTEGRITY"
    )

    valid_targets = {
        0,
        1,
        2,
    }

    train_targets = set(
        y_train["target"]
        .astype(int)
        .unique()
    )

    validation_targets = set(
        y_validation["target"]
        .astype(int)
        .unique()
    )

    target_pass = (
        train_targets <= valid_targets
        and
        validation_targets <= valid_targets
        and
        not y_train["target"].isna().any()
        and
        not y_validation["target"].isna().any()
    )

    checks[
        "target_integrity"
    ] = target_pass

    print(
        f"Training targets: "
        f"{sorted(train_targets)}"
    )

    print(
        f"Validation targets: "
        f"{sorted(validation_targets)}"
    )

    print(
        f"Result: "
        f"{'PASS' if target_pass else 'FAIL'}"
    )

    # ========================================================
    # 9. Train/validation separation
    # ========================================================

    print(
        "\n9. TRAIN / VALIDATION SEPARATION"
    )

    train_ids = set(
        train_full["fixture_id"]
    )

    validation_ids = set(
        validation_full["fixture_id"]
    )

    overlap = (
        train_ids
        &
        validation_ids
    )

    train_dates = pd.to_datetime(
        train_full["date"],
        utc=True,
        errors="coerce",
    )

    validation_dates = pd.to_datetime(
        validation_full["date"],
        utc=True,
        errors="coerce",
    )

    chronological = (
        train_dates.max()
        <
        validation_dates.min()
    )

    separation_pass = (
        len(overlap) == 0
        and
        chronological
    )

    checks[
        "train_validation_separation"
    ] = separation_pass

    print(
        f"Fixture overlap: "
        f"{len(overlap)}"
    )

    print(
        f"Chronological separation: "
        f"{'PASS' if chronological else 'FAIL'}"
    )

    print(
        f"Result: "
        f"{'PASS' if separation_pass else 'FAIL'}"
    )

    # ========================================================
    # 10. Existing quality report
    # ========================================================

    print(
        "\n10. PREVIOUS QUALITY GATE"
    )

    quality_pass = False

    if QUALITY_REPORT.exists():

        with QUALITY_REPORT.open(
            "r",
            encoding="utf-8",
        ) as file:

            quality = json.load(file)

        quality_pass = bool(
            quality.get(
                "overall_pass",
                False,
            )
        )

    checks[
        "previous_quality_gate"
    ] = quality_pass

    print(
        f"7.4.4 quality gate: "
        f"{'PASS' if quality_pass else 'FAIL'}"
    )

    # ========================================================
    # 11. Final test protection
    # ========================================================

    print(
        "\n11. FINAL TEST PROTECTION"
    )

    final_test_protected = True

    for dataframe in [
        train_full,
        validation_full,
    ]:

        if "season" in dataframe.columns:

            if (
                dataframe["season"]
                .astype(int)
                >=
                2025
            ).any():

                final_test_protected = False

    checks[
        "final_test_protected"
    ] = final_test_protected

    print(
        f"2025/26 final test untouched: "
        f"{'PASS' if final_test_protected else 'FAIL'}"
    )

    # ========================================================
    # Final result
    # ========================================================

    overall_pass = all(
        checks.values()
    )

    report = {
        "stage": "7.4.6",
        "overall_pass":
            overall_pass,
        "checks":
            checks,
        "training_records":
            len(X_train),
        "validation_records":
            len(X_validation),
        "feature_count":
            len(X_train.columns),
        "train_validation_overlap":
            len(overlap),
        "final_test_protected":
            final_test_protected,
    }

    with FINAL_REPORT.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
        )

    print(
        "\n" + "=" * 50
    )

    print(
        "STAGE 7.4 FINAL RESULT"
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
        f"\nFinal report:"
    )

    print(
        FINAL_REPORT
    )

    print(
        "\nSTAGE 7.4: "
        f"{'COMPLETE' if overall_pass else 'FAIL'}"
    )

    if not overall_pass:

        sys.exit(1)


if __name__ == "__main__":
    main()