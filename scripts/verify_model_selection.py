"""
FixtureIQ Stage 7.6.5
Model Selection Verification.
"""

import json
import sys
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
)

REPORT_FILE = (
    MODEL_DIR
    / "candidate_comparison.json"
)

SUMMARY_FILE = (
    MODEL_DIR
    / "candidate_comparison.csv"
)


EXPECTED_CANDIDATES = [
    "scaled_logistic",
    "regularized_logistic",
    "random_forest",
]


def load_json(path):

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.6.5"
    )

    print(
        "Model Selection Verification"
    )

    print("=" * 50)

    overall = True

    # ========================================================
    # 1. Report
    # ========================================================

    print(
        "\n1. COMPARISON REPORT"
    )

    report_exists = (
        REPORT_FILE.exists()
    )

    print(
        f"Report exists: "
        f"{'PASS' if report_exists else 'FAIL'}"
    )

    if not report_exists:
        sys.exit(1)

    report = load_json(
        REPORT_FILE
    )

    required_report_fields = {
        "stage",
        "purpose",
        "validation_season",
        "training_season",
        "final_test_season",
        "final_test_used",
        "selection_priority",
        "direction",
        "models",
        "baseline_improvements",
        "ranking",
        "selected_candidate",
        "selected_model",
        "selection_reason",
        "final_test_protection",
    }

    schema_pass = (
        required_report_fields
        <=
        set(report.keys())
    )

    print(
        f"Report schema: "
        f"{'PASS' if schema_pass else 'FAIL'}"
    )

    if not schema_pass:
        overall = False

    # ========================================================
    # 2. Data protection
    # ========================================================

    print(
        "\n2. DATA PROTECTION"
    )

    training_pass = (
        report["training_season"]
        ==
        2023
    )

    validation_pass = (
        report["validation_season"]
        ==
        2024
    )

    final_test_pass = (
        report["final_test_season"]
        ==
        "2025/26"
        and
        report["final_test_used"]
        is False
        and
        report["final_test_protection"]
        is True
    )

    print(
        f"2023 training: "
        f"{'PASS' if training_pass else 'FAIL'}"
    )

    print(
        f"2024 validation: "
        f"{'PASS' if validation_pass else 'FAIL'}"
    )

    print(
        f"2025/26 protected: "
        f"{'PASS' if final_test_pass else 'FAIL'}"
    )

    if not (
        training_pass
        and
        validation_pass
        and
        final_test_pass
    ):

        overall = False

    # ========================================================
    # 3. Candidate coverage
    # ========================================================

    print(
        "\n3. CANDIDATE COVERAGE"
    )

    candidate_ids = [
        model[
            "candidate_id"
        ]
        for model in report[
            "models"
        ]
    ]

    expected_all = [
        "baseline",
        "scaled_logistic",
        "regularized_logistic",
        "random_forest",
    ]

    coverage_pass = (
        set(candidate_ids)
        ==
        set(expected_all)
    )

    print(
        f"All baseline + candidates present: "
        f"{'PASS' if coverage_pass else 'FAIL'}"
    )

    if not coverage_pass:
        overall = False

    # ========================================================
    # 4. Validation sample counts
    # ========================================================

    print(
        "\n4. VALIDATION SAMPLE COUNTS"
    )

    count_pass = all(
        model[
            "sample_count"
        ]
        ==
        380
        for model in report[
            "models"
        ]
    )

    print(
        f"All models evaluated on 380 records: "
        f"{'PASS' if count_pass else 'FAIL'}"
    )

    if not count_pass:
        overall = False

    # ========================================================
    # 5. Ranking
    # ========================================================

    print(
        "\n5. CANDIDATE RANKING"
    )

    ranking = report[
        "ranking"
    ]

    ranking_pass = (
        len(ranking)
        ==
        3
        and
        set(ranking)
        ==
        set(EXPECTED_CANDIDATES)
    )

    print(
        f"Three candidates ranked: "
        f"{'PASS' if ranking_pass else 'FAIL'}"
    )

    if not ranking_pass:
        overall = False

    for index, candidate in enumerate(
        ranking,
        start=1,
    ):

        print(
            f"{index}. {candidate}"
        )

    # ========================================================
    # 6. Selection
    # ========================================================

    print(
        "\n6. MODEL SELECTION"
    )

    selected_candidate = report[
        "selected_candidate"
    ]

    selected_model = report[
        "selected_model"
    ]

    selection_pass = (
        selected_candidate
        in
        EXPECTED_CANDIDATES
        and
        selected_candidate
        ==
        ranking[0]
        and
        isinstance(
            selected_model,
            str,
        )
        and
        len(selected_model) > 0
    )

    print(
        f"Selected candidate: "
        f"{selected_candidate}"
    )

    print(
        f"Selected model: "
        f"{selected_model}"
    )

    print(
        f"Selection validity: "
        f"{'PASS' if selection_pass else 'FAIL'}"
    )

    if not selection_pass:
        overall = False

    # ========================================================
    # 7. Selection criteria
    # ========================================================

    print(
        "\n7. SELECTION CRITERIA"
    )

    expected_priority = [
        "log_loss",
        "brier_score",
        "ece",
        "mce",
        "accuracy",
    ]

    priority_pass = (
        report[
            "selection_priority"
        ]
        ==
        expected_priority
    )

    print(
        f"Predefined metric priority: "
        f"{'PASS' if priority_pass else 'FAIL'}"
    )

    if not priority_pass:
        overall = False

    # ========================================================
    # 8. Summary CSV
    # ========================================================

    print(
        "\n8. SUMMARY ARTIFACT"
    )

    csv_exists = (
        SUMMARY_FILE.exists()
    )

    print(
        f"Comparison CSV exists: "
        f"{'PASS' if csv_exists else 'FAIL'}"
    )

    if not csv_exists:

        overall = False

    else:

        summary = pd.read_csv(
            SUMMARY_FILE
        )

        csv_pass = (
            len(summary) == 3
            and
            set(
                summary[
                    "candidate_id"
                ]
            )
            ==
            set(EXPECTED_CANDIDATES)
        )

        print(
            f"Summary CSV integrity: "
            f"{'PASS' if csv_pass else 'FAIL'}"
        )

        if not csv_pass:
            overall = False

    # ========================================================
    # Final
    # ========================================================

    print(
        "\n" + "=" * 50
    )

    print(
        "FINAL RESULT"
    )

    print("=" * 50)

    print(
        f"7.6.5 Model Comparison: "
        f"{'PASS' if overall else 'FAIL'}"
    )

    print(
        f"7.6.5 Model Selection: "
        f"{'PASS' if overall else 'FAIL'}"
    )

    print(
        f"\nSTAGE 7.6.5: "
        f"{'PASS' if overall else 'FAIL'}"
    )

    if not overall:
        sys.exit(1)


if __name__ == "__main__":
    main()