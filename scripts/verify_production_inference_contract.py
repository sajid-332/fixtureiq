"""
FixtureIQ Stage 7.8.1
Production Inference Contract Verification.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

CONTRACT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
    / "production_inference_contract.json"
)

X_TRAIN_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
    / "X_train.csv"
)

SELECTED_MODEL = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
    / "selected"
    / "selected_model.joblib"
)

LOCK_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
    / "selected_model.json"
)


def check(
    label,
    condition,
):

    result = (
        "PASS"
        if condition
        else "FAIL"
    )

    print(
        f"{label}: {result}"
    )

    return bool(
        condition
    )


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.8.1"
    )

    print(
        "Production Inference Contract Verification"
    )

    print("=" * 50)

    failures = 0

    # ========================================================
    # 1. CONTRACT
    # ========================================================

    print(
        "\n1. CONTRACT"
    )

    if not CONTRACT_FILE.exists():

        print(
            "Contract file: FAIL"
        )

        sys.exit(1)

    with CONTRACT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        contract = json.load(
            file
        )

    failures += not check(
        "Contract file",
        True,
    )

    failures += not check(
        "Stage 7.8.1",
        contract.get(
            "stage"
        )
        ==
        "7.8.1",
    )

    failures += not check(
        "Locked contract",
        contract.get(
            "status"
        )
        ==
        "LOCKED_CONTRACT",
    )

    # ========================================================
    # 2. MODEL
    # ========================================================

    print(
        "\n2. MODEL"
    )

    failures += not check(
        "Selected model exists",
        SELECTED_MODEL.exists(),
    )

    failures += not check(
        "Random Forest selected",
        contract.get(
            "model",
            {}
        ).get(
            "candidate_id"
        )
        ==
        "random_forest",
    )

    failures += not check(
        "Model status LOCKED",
        contract.get(
            "model",
            {}
        ).get(
            "status"
        )
        ==
        "LOCKED",
    )

    # ========================================================
    # 3. MODEL PROTECTION
    # ========================================================

    print(
        "\n3. MODEL PROTECTION"
    )

    failures += not check(
        "Selection stage 7.6.5",
        contract[
            "model"
        ][
            "selection_stage"
        ]
        ==
        "7.6.5",
    )

    failures += not check(
        "Lock stage 7.7.1",
        contract[
            "model"
        ][
            "lock_stage"
        ]
        ==
        "7.7.1",
    )

    failures += not check(
        "Package stage 7.7.2",
        contract[
            "model"
        ][
            "package_stage"
        ]
        ==
        "7.7.2",
    )

    # ========================================================
    # 4. CANONICAL SCHEMA
    # ========================================================

    print(
        "\n4. FEATURE SCHEMA"
    )

    failures += not check(
        "X_train exists",
        X_TRAIN_FILE.exists(),
    )

    if X_TRAIN_FILE.exists():

        canonical = pd.read_csv(
            X_TRAIN_FILE,
            nrows=0,
        )

        columns = list(
            canonical.columns
        )

        failures += not check(
            "86 canonical features",
            len(columns)
            ==
            86,
        )

        failures += not check(
            "fixture_id excluded",
            "fixture_id"
            not in columns,
        )

        contract_columns = contract.get(
            "feature_columns",
            [],
        )

        failures += not check(
            "Contract contains 86 features",
            len(contract_columns)
            ==
            86,
        )

        failures += not check(
            "Contract schema matches X_train",
            columns
            ==
            contract_columns,
        )

    # ========================================================
    # 5. TARGET CONTRACT
    # ========================================================

    print(
        "\n5. TARGET CONTRACT"
    )

    failures += not check(
        "Target mapping",
        contract.get(
            "target_mapping"
        )
        ==
        {
            "0": "draw",
            "1": "home_win",
            "2": "away_win",
        },
    )

    # ========================================================
    # 6. FINAL TEST PROTECTION
    # ========================================================

    print(
        "\n6. FINAL TEST PROTECTION"
    )

    final_test = contract.get(
        "final_test",
        {},
    )

    failures += not check(
        "Final test marked consumed",
        final_test.get(
            "status"
        )
        ==
        "CONSUMED",
    )

    failures += not check(
        "No final-test training",
        final_test.get(
            "must_not_be_used_for_training"
        )
        is True,
    )

    failures += not check(
        "No final-test selection",
        final_test.get(
            "must_not_be_used_for_selection"
        )
        is True,
    )

    # ========================================================
    # 7. INPUT RULES
    # ========================================================

    print(
        "\n7. INPUT RULES"
    )

    rules = set(
        contract.get(
            "input_rules",
            [],
        )
    )

    required_rules = {
        "fixture_id is metadata only and must not enter the model matrix.",
        "Only completed matches before kickoff may update team state.",
        "Upcoming fixtures never update historical state.",
        "Target/result fields are prohibited from production features.",
        "NaN and infinite model features are prohibited.",
        "Feature order must exactly match the canonical training schema.",
    }

    failures += not check(
        "Required input rules",
        required_rules.issubset(
            rules
        ),
    )

    # ========================================================
    # 8. PROHIBITED OPERATIONS
    # ========================================================

    print(
        "\n8. PROHIBITED OPERATIONS"
    )

    prohibited = set(
        contract.get(
            "prohibited_operations",
            [],
        )
    )

    required_prohibited = {
        "retraining",
        "model_selection",
        "hyperparameter_tuning",
        "use_of_2025_26_final_test_for_training",
        "use_of_2025_26_final_test_for_selection",
    }

    failures += not check(
        "Production restrictions",
        required_prohibited.issubset(
            prohibited
        ),
    )

    # ========================================================
    # FINAL
    # ========================================================

    print(
        "\n" + "=" * 50
    )

    if failures == 0:

        print(
            "STAGE 7.8.1: PASS"
        )

        print(
            "Production inference contract is valid."
        )

    else:

        print(
            "STAGE 7.8.1: FAIL"
        )

        print(
            f"Failures: {failures}"
        )

    print(
        "=" * 50
    )

    sys.exit(
        0
        if failures == 0
        else 1
    )


if __name__ == "__main__":
    main()