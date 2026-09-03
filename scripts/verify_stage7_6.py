"""
FixtureIQ Stage 7.6
Final Candidate Model Pipeline Verification

Verifies:
7.6.1 Baseline Diagnosis
7.6.2 Candidate Model Design
7.6.3 Candidate Model Training
7.6.4 Candidate Model Evaluation
7.6.5 Candidate Comparison & Selection

2025/26 final test must remain untouched.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
)

CANDIDATE_MODEL_DIR = (
    MODEL_DIR
    / "candidates"
)

CANDIDATE_PREDICTION_DIR = (
    MODEL_DIR
    / "candidate_predictions"
)

CANDIDATE_METRIC_DIR = (
    MODEL_DIR
    / "candidate_metrics"
)

DIAGNOSIS_FILE = (
    MODEL_DIR
    / "baseline_diagnosis.json"
)

CANDIDATE_PLAN_FILE = (
    MODEL_DIR
    / "candidate_model_plan.json"
)

COMPARISON_FILE = (
    MODEL_DIR
    / "candidate_comparison.json"
)

COMPARISON_CSV = (
    MODEL_DIR
    / "candidate_comparison.csv"
)


CANDIDATES = [
    "scaled_logistic",
    "regularized_logistic",
    "random_forest",
]


def load_json(path):
    """Load a JSON file."""

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def check(condition):
    """Return PASS/FAIL text."""

    return (
        "PASS"
        if condition
        else "FAIL"
    )


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.6"
    )

    print(
        "Final Candidate Model Pipeline Verification"
    )

    print("=" * 50)

    overall = True

    # ========================================================
    # 1. BASELINE DIAGNOSIS
    # ========================================================

    print(
        "\n1. BASELINE DIAGNOSIS"
    )

    diagnosis_exists = (
        DIAGNOSIS_FILE.exists()
    )

    print(
        f"Diagnosis report: "
        f"{check(diagnosis_exists)}"
    )

    diagnosis_pass = False

    if diagnosis_exists:

        diagnosis = load_json(
            DIAGNOSIS_FILE
        )

        diagnosis_pass = (
            diagnosis.get(
                "stage"
            )
            ==
            "7.6.1"
        )

        print(
            f"Diagnosis schema: "
            f"{check(diagnosis_pass)}"
        )

    if not diagnosis_pass:
        overall = False

    # ========================================================
    # 2. CANDIDATE MODEL DESIGN
    # ========================================================

    print(
        "\n2. CANDIDATE MODEL DESIGN"
    )

    plan_exists = (
        CANDIDATE_PLAN_FILE.exists()
    )

    print(
        f"Candidate plan: "
        f"{check(plan_exists)}"
    )

    plan_pass = False

    if plan_exists:

        plan = load_json(
            CANDIDATE_PLAN_FILE
        )

        candidate_entries = (
            plan.get(
                "candidates",
                []
            )
        )

        planned_ids = set()

        if isinstance(
            candidate_entries,
            dict,
        ):

            planned_ids = set(
                candidate_entries.keys()
            )

        elif isinstance(
            candidate_entries,
            list,
        ):

            for item in candidate_entries:

                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                # IMPORTANT:
                # Stage 7.6.2 uses "id"
                # as the candidate identifier.
                candidate_id = (
                    item.get(
                        "id"
                    )
                )

                if candidate_id:

                    planned_ids.add(
                        candidate_id
                    )

        plan_pass = (
            set(CANDIDATES)
            <=
            planned_ids
        )

        print(
            f"Candidate definitions: "
            f"{check(plan_pass)}"
        )

    if not plan_pass:
        overall = False

    # ========================================================
    # 3. CANDIDATE MODEL ARTIFACTS
    # ========================================================

    print(
        "\n3. CANDIDATE MODEL ARTIFACTS"
    )

    models_pass = True

    for candidate_id in CANDIDATES:

        model_file = (
            CANDIDATE_MODEL_DIR
            / f"{candidate_id}.joblib"
        )

        metadata_file = (
            CANDIDATE_MODEL_DIR
            / f"{candidate_id}_metadata.json"
        )

        model_ok = (
            model_file.exists()
        )

        metadata_ok = (
            metadata_file.exists()
        )

        print(
            f"{candidate_id} model: "
            f"{check(model_ok)}"
        )

        print(
            f"{candidate_id} metadata: "
            f"{check(metadata_ok)}"
        )

        if not (
            model_ok
            and
            metadata_ok
        ):

            models_pass = False
            continue

        metadata = load_json(
            metadata_file
        )

        metadata_ok = all(
            [
                metadata.get(
                    "stage"
                )
                ==
                "7.6.3",

                metadata.get(
                    "training_season"
                )
                ==
                2023,

                metadata.get(
                    "validation_season"
                )
                ==
                2024,

                metadata.get(
                    "training_rows"
                )
                ==
                380,

                metadata.get(
                    "validation_rows"
                )
                ==
                380,

                metadata.get(
                    "feature_count"
                )
                ==
                86,

                metadata.get(
                    "feature_count_excludes_fixture_id"
                )
                is True,

                metadata.get(
                    "final_test_used"
                )
                is False,
            ]
        )

        print(
            f"{candidate_id} metadata integrity: "
            f"{check(metadata_ok)}"
        )

        if not metadata_ok:
            models_pass = False

    if not models_pass:
        overall = False

    # ========================================================
    # 4. CANDIDATE PREDICTIONS
    # ========================================================

    print(
        "\n4. CANDIDATE PREDICTIONS"
    )

    predictions_pass = True

    required_columns = {
        "fixture_id",
        "actual",
        "predicted",
        "prob_draw",
        "prob_home",
        "prob_away",
    }

    prediction_frames = {}

    for candidate_id in CANDIDATES:

        path = (
            CANDIDATE_PREDICTION_DIR
            / f"{candidate_id}_predictions.csv"
        )

        exists = path.exists()

        print(
            f"{candidate_id}: "
            f"{check(exists)}"
        )

        if not exists:

            predictions_pass = False
            continue

        frame = pd.read_csv(
            path
        )

        prediction_frames[
            candidate_id
        ] = frame

        count_ok = (
            len(frame)
            ==
            380
        )

        schema_ok = (
            required_columns
            <=
            set(frame.columns)
        )

        unique_ok = (
            frame[
                "fixture_id"
            ].nunique()
            ==
            380
        )

        probabilities = (
            frame[
                [
                    "prob_draw",
                    "prob_home",
                    "prob_away",
                ]
            ]
            .to_numpy(
                dtype=float
            )
        )

        finite_ok = np.isfinite(
            probabilities
        ).all()

        range_ok = (
            (
                probabilities
                >=
                0
            ).all()
            and
            (
                probabilities
                <=
                1
            ).all()
        )

        sums_ok = np.allclose(
            probabilities.sum(
                axis=1
            ),
            1.0,
            atol=1e-8,
        )

        targets_ok = (
            set(
                frame[
                    "actual"
                ].astype(int)
            )
            <=
            {
                0,
                1,
                2,
            }
            and
            set(
                frame[
                    "predicted"
                ].astype(int)
            )
            <=
            {
                0,
                1,
                2,
            }
        )

        candidate_ok = all(
            [
                count_ok,
                schema_ok,
                unique_ok,
                finite_ok,
                range_ok,
                sums_ok,
                targets_ok,
            ]
        )

        print(
            f"  380 records: "
            f"{check(count_ok)}"
        )

        print(
            f"  Schema: "
            f"{check(schema_ok)}"
        )

        print(
            f"  Unique fixture IDs: "
            f"{check(unique_ok)}"
        )

        print(
            f"  Probability integrity: "
            f"{check(
                finite_ok
                and
                range_ok
                and
                sums_ok
            )}"
        )

        print(
            f"  Target integrity: "
            f"{check(targets_ok)}"
        )

        if not candidate_ok:
            predictions_pass = False

    if not predictions_pass:
        overall = False

    # ========================================================
    # 5. CANDIDATE EVALUATION
    # ========================================================

    print(
        "\n5. CANDIDATE EVALUATION"
    )

    metrics_pass = True

    metric_data = {}

    for candidate_id in CANDIDATES:

        path = (
            CANDIDATE_METRIC_DIR
            / f"{candidate_id}_metrics.json"
        )

        exists = path.exists()

        print(
            f"{candidate_id}: "
            f"{check(exists)}"
        )

        if not exists:

            metrics_pass = False
            continue

        metrics = load_json(
            path
        )

        metric_data[
            candidate_id
        ] = metrics

        required = [
            "stage",
            "candidate_id",
            "model_name",
            "validation_season",
            "sample_count",
            "accuracy",
            "log_loss",
            "brier_score",
            "ece",
            "mce",
            "training_season",
            "final_test_season",
            "final_test_used",
        ]

        schema_ok = all(
            key in metrics
            for key in required
        )

        data_ok = (
            metrics.get(
                "stage"
            )
            ==
            "7.6.4"
            and
            metrics.get(
                "candidate_id"
            )
            ==
            candidate_id
            and
            metrics.get(
                "validation_season"
            )
            ==
            2024
            and
            metrics.get(
                "training_season"
            )
            ==
            2023
            and
            metrics.get(
                "sample_count"
            )
            ==
            380
            and
            metrics.get(
                "final_test_season"
            )
            ==
            "2025/26"
            and
            metrics.get(
                "final_test_used"
            )
            is False
        )

        metric_values = [
            metrics.get(
                "accuracy"
            ),
            metrics.get(
                "log_loss"
            ),
            metrics.get(
                "brier_score"
            ),
            metrics.get(
                "ece"
            ),
            metrics.get(
                "mce"
            ),
        ]

        finite_ok = all(
            isinstance(
                value,
                (int, float)
            )
            and
            np.isfinite(
                value
            )
            for value in metric_values
        )

        candidate_ok = all(
            [
                schema_ok,
                data_ok,
                finite_ok,
            ]
        )

        print(
            f"  Schema: "
            f"{check(schema_ok)}"
        )

        print(
            f"  Validation data: "
            f"{check(data_ok)}"
        )

        print(
            f"  Metric validity: "
            f"{check(finite_ok)}"
        )

        if not candidate_ok:
            metrics_pass = False

    if not metrics_pass:
        overall = False

    # ========================================================
    # 6. CROSS-CANDIDATE CONSISTENCY
    # ========================================================

    print(
        "\n6. CROSS-CANDIDATE CONSISTENCY"
    )

    consistency_pass = True

    if len(
        prediction_frames
    ) == 3:

        reference_ids = (
            prediction_frames[
                CANDIDATES[0]
            ][
                "fixture_id"
            ].tolist()
        )

        reference_actual = (
            prediction_frames[
                CANDIDATES[0]
            ][
                "actual"
            ].tolist()
        )

        for candidate_id in CANDIDATES[1:]:

            current_ids = (
                prediction_frames[
                    candidate_id
                ][
                    "fixture_id"
                ].tolist()
            )

            current_actual = (
                prediction_frames[
                    candidate_id
                ][
                    "actual"
                ].tolist()
            )

            same_ids = (
                current_ids
                ==
                reference_ids
            )

            same_actual = (
                current_actual
                ==
                reference_actual
            )

            print(
                f"{candidate_id} fixture alignment: "
                f"{check(same_ids)}"
            )

            print(
                f"{candidate_id} target alignment: "
                f"{check(same_actual)}"
            )

            if not (
                same_ids
                and
                same_actual
            ):

                consistency_pass = False

    else:

        consistency_pass = False

    print(
        f"Cross-candidate fixture alignment: "
        f"{check(consistency_pass)}"
    )

    if not consistency_pass:
        overall = False

    # ========================================================
    # 7. MODEL COMPARISON
    # ========================================================

    print(
        "\n7. MODEL COMPARISON"
    )

    comparison_exists = (
        COMPARISON_FILE.exists()
    )

    print(
        f"Comparison report: "
        f"{check(comparison_exists)}"
    )

    comparison_pass = False

    comparison = None

    if comparison_exists:

        comparison = load_json(
            COMPARISON_FILE
        )

        comparison_pass = (
            comparison.get(
                "stage"
            )
            ==
            "7.6.5"
            and
            comparison.get(
                "validation_season"
            )
            ==
            2024
            and
            comparison.get(
                "training_season"
            )
            ==
            2023
            and
            comparison.get(
                "final_test_season"
            )
            ==
            "2025/26"
            and
            comparison.get(
                "final_test_used"
            )
            is False
        )

        print(
            f"Comparison integrity: "
            f"{check(comparison_pass)}"
        )

    if not comparison_pass:
        overall = False

    # ========================================================
    # 8. MODEL SELECTION
    # ========================================================

    print(
        "\n8. MODEL SELECTION"
    )

    selection_pass = False

    if comparison is not None:

        selected_candidate = (
            comparison.get(
                "selected_candidate"
            )
        )

        selected_model = (
            comparison.get(
                "selected_model"
            )
        )

        ranking = comparison.get(
            "ranking",
            []
        )

        selection_pass = (
            selected_candidate
            ==
            "random_forest"
            and
            selected_model
            ==
            "Random Forest"
            and
            len(ranking)
            ==
            3
            and
            ranking[0]
            ==
            "random_forest"
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
            f"Random Forest ranked #1: "
            f"{check(selection_pass)}"
        )

    else:

        print(
            "Selection data unavailable: FAIL"
        )

    if not selection_pass:
        overall = False

    # ========================================================
    # 9. SELECTED MODEL CONSISTENCY
    # ========================================================

    print(
        "\n9. SELECTED MODEL CONSISTENCY"
    )

    selected_consistency = False

    if (
        comparison is not None
        and
        "random_forest"
        in metric_data
    ):

        rf_metrics = metric_data[
            "random_forest"
        ]

        comparison_models = (
            comparison.get(
                "models",
                []
            )
        )

        comparison_rf = None

        for model in comparison_models:

            if (
                isinstance(
                    model,
                    dict,
                )
                and
                model.get(
                    "candidate_id"
                )
                ==
                "random_forest"
            ):

                comparison_rf = model
                break

        if comparison_rf is not None:

            selected_consistency = (
                comparison[
                    "selected_candidate"
                ]
                ==
                "random_forest"
                and
                comparison_rf[
                    "log_loss"
                ]
                ==
                rf_metrics[
                    "log_loss"
                ]
                and
                comparison_rf[
                    "brier_score"
                ]
                ==
                rf_metrics[
                    "brier_score"
                ]
                and
                comparison_rf[
                    "accuracy"
                ]
                ==
                rf_metrics[
                    "accuracy"
                ]
            )

    print(
        f"Selected Random Forest metrics consistent: "
        f"{check(selected_consistency)}"
    )

    if not selected_consistency:
        overall = False

    # ========================================================
    # 10. FINAL TEST PROTECTION
    # ========================================================

    print(
        "\n10. FINAL TEST PROTECTION"
    )

    protection_pass = True

    if comparison is not None:

        protection_pass = (
            comparison.get(
                "final_test_used"
            )
            is False
            and
            comparison.get(
                "final_test_protection"
            )
            is True
        )

    for candidate_id in CANDIDATES:

        metrics = metric_data.get(
            candidate_id
        )

        if metrics is None:

            protection_pass = False
            continue

        if metrics.get(
            "final_test_used"
        ) is not False:

            protection_pass = False

    print(
        f"2025/26 final test used: "
        f"{'NO' if protection_pass else 'YES'}"
    )

    print(
        f"Final test protection: "
        f"{check(protection_pass)}"
    )

    if not protection_pass:
        overall = False

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print(
        "\n" + "=" * 50
    )

    print(
        "STAGE 7.6 FINAL RESULT"
    )

    print("=" * 50)

    print(
        f"7.6.1 Baseline Diagnosis        "
        f"{check(diagnosis_pass)}"
    )

    print(
        f"7.6.2 Candidate Model Design    "
        f"{check(plan_pass)}"
    )

    print(
        f"7.6.3 Candidate Model Training  "
        f"{check(models_pass)}"
    )

    print(
        f"7.6.4 Candidate Evaluation      "
        f"{check(metrics_pass)}"
    )

    print(
        f"7.6.5 Model Comparison          "
        f"{check(comparison_pass)}"
    )

    print(
        f"7.6.5 Model Selection           "
        f"{check(selection_pass)}"
    )

    print(
        f"Cross-stage consistency          "
        f"{check(selected_consistency)}"
    )

    print(
        f"Final test protection            "
        f"{check(protection_pass)}"
    )

    print(
        "\n" + "=" * 50
    )

    if overall:

        print(
            "STAGE 7.6: COMPLETE"
        )

        print(
            "Selected model: Random Forest"
        )

        print(
            "Training season: 2023"
        )

        print(
            "Validation season: 2024"
        )

        print(
            "Final test season: 2025/26"
        )

        print(
            "2025/26 final test: PROTECTED"
        )

    else:

        print(
            "STAGE 7.6: FAIL"
        )

        sys.exit(1)


if __name__ == "__main__":
    main()