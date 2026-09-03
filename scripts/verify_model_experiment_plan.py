"""
FixtureIQ Stage 7.6.1 + 7.6.2
Diagnosis and Candidate Plan Verification.
"""

import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
)

DIAGNOSIS_FILE = (
    MODEL_DIR
    / "baseline_diagnosis.json"
)

EXPERIMENT_FILE = (
    MODEL_DIR
    / "candidate_model_plan.json"
)


def load_json(path):

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.6.1 + 7.6.2"
    )

    print(
        "Final Verification"
    )

    print("=" * 50)

    # ========================================================
    # 1. Diagnosis
    # ========================================================

    print(
        "\n1. BASELINE DIAGNOSIS"
    )

    diagnosis_exists = (
        DIAGNOSIS_FILE.exists()
    )

    print(
        f"Diagnosis report: "
        f"{'PASS' if diagnosis_exists else 'FAIL'}"
    )

    if not diagnosis_exists:
        sys.exit(1)

    diagnosis = load_json(
        DIAGNOSIS_FILE
    )

    diagnosis_schema = {
        "stage",
        "purpose",
        "data_protection",
        "dataset",
        "class_distribution",
        "feature_scale",
        "baseline_convergence",
        "baseline_metrics",
        "baseline_calibration",
        "prediction_diagnostics",
        "diagnostic_conclusions",
    }

    diagnosis_schema_pass = (
        diagnosis_schema
        <=
        set(diagnosis.keys())
    )

    print(
        f"Diagnosis schema: "
        f"{'PASS' if diagnosis_schema_pass else 'FAIL'}"
    )

    dataset = diagnosis[
        "dataset"
    ]

    dataset_pass = (
        dataset["training_rows"] == 380
        and
        dataset["validation_rows"] == 380
        and
        dataset["feature_count"] == 86
    )

    print(
        f"Dataset dimensions: "
        f"{'PASS' if dataset_pass else 'FAIL'}"
    )

    # ========================================================
    # 2. Data protection
    # ========================================================

    print(
        "\n2. DATA PROTECTION"
    )

    protection = diagnosis[
        "data_protection"
    ]

    protection_pass = (
        protection["training_season"]
        == 2023
        and
        protection["validation_season"]
        == 2024
        and
        protection["final_test_season"]
        == "2025/26"
        and
        protection["final_test_used"]
        is False
    )

    print(
        f"2023 training: "
        f"{'PASS' if protection['training_season'] == 2023 else 'FAIL'}"
    )

    print(
        f"2024 validation: "
        f"{'PASS' if protection['validation_season'] == 2024 else 'FAIL'}"
    )

    print(
        f"2025/26 final test protected: "
        f"{'PASS' if protection['final_test_used'] is False else 'FAIL'}"
    )

    # ========================================================
    # 3. Feature diagnostics
    # ========================================================

    print(
        "\n3. FEATURE DIAGNOSTICS"
    )

    feature_scale = diagnosis[
        "feature_scale"
    ]

    scale_pass = (
        feature_scale[
            "numeric_feature_count"
        ]
        ==
        86
    )

    print(
        f"Numeric features: "
        f"{feature_scale['numeric_feature_count']}"
    )

    print(
        f"Feature scale analysis: "
        f"{'PASS' if scale_pass else 'FAIL'}"
    )

    # ========================================================
    # 4. Candidate plan
    # ========================================================

    print(
        "\n4. CANDIDATE MODEL PLAN"
    )

    plan_exists = (
        EXPERIMENT_FILE.exists()
    )

    print(
        f"Candidate plan: "
        f"{'PASS' if plan_exists else 'FAIL'}"
    )

    if not plan_exists:
        sys.exit(1)

    plan = load_json(
        EXPERIMENT_FILE
    )

    plan_schema = {
        "stage",
        "purpose",
        "selection_principles",
        "target_mapping",
        "training_data",
        "validation_data",
        "candidates",
        "comparison_metrics",
        "selection_priority",
        "selection_rule",
        "next_stage",
    }

    plan_schema_pass = (
        plan_schema
        <=
        set(plan.keys())
    )

    print(
        f"Plan schema: "
        f"{'PASS' if plan_schema_pass else 'FAIL'}"
    )

    candidates = plan[
        "candidates"
    ]

    candidate_count_pass = (
        len(candidates) == 3
    )

    print(
        f"Candidate count: "
        f"{len(candidates)}"
    )

    print(
        f"Candidate count: "
        f"{'PASS' if candidate_count_pass else 'FAIL'}"
    )

    candidate_ids = [
        candidate["id"]
        for candidate in candidates
    ]

    expected_ids = {
        "scaled_logistic",
        "regularized_logistic",
        "random_forest",
    }

    candidate_ids_pass = (
        set(candidate_ids)
        ==
        expected_ids
    )

    print(
        f"Candidate definitions: "
        f"{'PASS' if candidate_ids_pass else 'FAIL'}"
    )

    # ========================================================
    # 5. Target mapping
    # ========================================================

    print(
        "\n5. TARGET MAPPING"
    )

    mapping_pass = (
        plan["target_mapping"]
        ==
        {
            "0": "draw",
            "1": "home_win",
            "2": "away_win",
        }
    )

    print(
        f"Target mapping: "
        f"{'PASS' if mapping_pass else 'FAIL'}"
    )

    # ========================================================
    # 6. Comparison contract
    # ========================================================

    print(
        "\n6. COMPARISON CONTRACT"
    )

    expected_metrics = {
        "accuracy",
        "log_loss",
        "brier_score",
        "precision_macro",
        "recall_macro",
        "f1_macro",
        "ece",
        "mce",
    }

    comparison_metrics_pass = (
        set(
            plan["comparison_metrics"]
        )
        ==
        expected_metrics
    )

    print(
        f"Evaluation metrics: "
        f"{'PASS' if comparison_metrics_pass else 'FAIL'}"
    )

    priority_pass = (
        plan["selection_priority"]
        ==
        [
            "log_loss",
            "brier_score",
            "ece",
            "mce",
            "accuracy",
        ]
    )

    print(
        f"Selection priority: "
        f"{'PASS' if priority_pass else 'FAIL'}"
    )

    # ========================================================
    # Final
    # ========================================================

    overall = all(
        [
            diagnosis_exists,
            diagnosis_schema_pass,
            dataset_pass,
            protection_pass,
            scale_pass,
            plan_exists,
            plan_schema_pass,
            candidate_count_pass,
            candidate_ids_pass,
            mapping_pass,
            comparison_metrics_pass,
            priority_pass,
        ]
    )

    print(
        "\n" + "=" * 50
    )

    print(
        "FINAL RESULT"
    )

    print(
        f"Stage 7.6.1: "
        f"{'PASS' if overall else 'FAIL'}"
    )

    print(
        f"Stage 7.6.2: "
        f"{'PASS' if overall else 'FAIL'}"
    )

    print(
        f"\n7.6.1 + 7.6.2: "
        f"{'PASS' if overall else 'FAIL'}"
    )

    if not overall:
        sys.exit(1)


if __name__ == "__main__":
    main()