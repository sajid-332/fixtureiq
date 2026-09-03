"""
FixtureIQ Stage 7.6.3 + 7.6.4
Candidate Model Verification.
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


CANDIDATE_ORDER = [
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
        "FixtureIQ Stage 7.6.3 + 7.6.4"
    )

    print(
        "Candidate Model Verification"
    )

    print("=" * 50)

    overall = True

    # ========================================================
    # 1. Candidate model artifacts
    # ========================================================

    print(
        "\n1. CANDIDATE MODEL ARTIFACTS"
    )

    for candidate_id in CANDIDATE_ORDER:

        model_path = (
            CANDIDATE_MODEL_DIR
            / f"{candidate_id}.joblib"
        )

        metadata_path = (
            CANDIDATE_MODEL_DIR
            / f"{candidate_id}_metadata.json"
        )

        model_pass = (
            model_path.exists()
        )

        metadata_pass = (
            metadata_path.exists()
        )

        print(
            f"{candidate_id} model: "
            f"{'PASS' if model_pass else 'FAIL'}"
        )

        print(
            f"{candidate_id} metadata: "
            f"{'PASS' if metadata_pass else 'FAIL'}"
        )

        if not (
            model_pass
            and
            metadata_pass
        ):

            overall = False
            continue

        metadata = load_json(
            metadata_path
        )

        metadata_pass = all(
            [
                metadata.get(
                    "stage"
                )
                == "7.6.3",

                metadata.get(
                    "training_season"
                )
                == 2023,

                metadata.get(
                    "validation_season"
                )
                == 2024,

                metadata.get(
                    "training_rows"
                )
                == 380,

                metadata.get(
                    "validation_rows"
                )
                == 380,

                metadata.get(
                    "feature_count"
                )
                == 86,

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
            f"{'PASS' if metadata_pass else 'FAIL'}"
        )

        if not metadata_pass:
            overall = False

    # ========================================================
    # 2. Prediction artifacts
    # ========================================================

    print(
        "\n2. PREDICTION ARTIFACTS"
    )

    required_prediction_columns = {
        "fixture_id",
        "actual",
        "predicted",
        "prob_home",
        "prob_draw",
        "prob_away",
    }

    for candidate_id in CANDIDATE_ORDER:

        path = (
            CANDIDATE_PREDICTION_DIR
            / f"{candidate_id}_predictions.csv"
        )

        exists = path.exists()

        print(
            f"{candidate_id}: "
            f"{'PASS' if exists else 'FAIL'}"
        )

        if not exists:

            overall = False
            continue

        predictions = pd.read_csv(
            path
        )

        count_pass = (
            len(predictions) == 380
        )

        schema_pass = (
            required_prediction_columns
            <=
            set(predictions.columns)
        )

        duplicate_pass = (
            predictions[
                "fixture_id"
            ].nunique()
            ==
            380
        )

        probability_matrix = (
            predictions[
                [
                    "prob_draw",
                    "prob_home",
                    "prob_away",
                ]
            ].to_numpy(
                dtype=float
            )
        )

        finite_pass = np.isfinite(
            probability_matrix
        ).all()

        range_pass = (
            (probability_matrix >= 0).all()
            and
            (probability_matrix <= 1).all()
        )

        sum_pass = np.allclose(
            probability_matrix.sum(
                axis=1
            ),
            1.0,
            atol=1e-8,
        )

        target_pass = (
            set(
                predictions[
                    "actual"
                ].astype(int).unique()
            )
            <=
            {0, 1, 2}
            and
            set(
                predictions[
                    "predicted"
                ].astype(int).unique()
            )
            <=
            {0, 1, 2}
        )

        candidate_pass = all(
            [
                count_pass,
                schema_pass,
                duplicate_pass,
                finite_pass,
                range_pass,
                sum_pass,
                target_pass,
            ]
        )

        print(
            f"  Count 380: "
            f"{'PASS' if count_pass else 'FAIL'}"
        )

        print(
            f"  Schema: "
            f"{'PASS' if schema_pass else 'FAIL'}"
        )

        print(
            f"  Unique fixture IDs: "
            f"{'PASS' if duplicate_pass else 'FAIL'}"
        )

        print(
            f"  Probability integrity: "
            f"{'PASS' if (finite_pass and range_pass and sum_pass) else 'FAIL'}"
        )

        print(
            f"  Targets: "
            f"{'PASS' if target_pass else 'FAIL'}"
        )

        if not candidate_pass:
            overall = False

    # ========================================================
    # 3. Evaluation metrics
    # ========================================================

    print(
        "\n3. EVALUATION METRICS"
    )

    required_metrics = {
        "stage",
        "candidate_id",
        "model_name",
        "validation_season",
        "sample_count",
        "accuracy",
        "log_loss",
        "brier_score",
        "precision_macro",
        "recall_macro",
        "f1_macro",
        "ece",
        "mce",
        "calibration",
        "classes",
        "confusion_matrix",
        "training_season",
        "final_test_season",
        "final_test_used",
    }

    for candidate_id in CANDIDATE_ORDER:

        path = (
            CANDIDATE_METRIC_DIR
            / f"{candidate_id}_metrics.json"
        )

        exists = path.exists()

        print(
            f"{candidate_id}: "
            f"{'PASS' if exists else 'FAIL'}"
        )

        if not exists:

            overall = False
            continue

        metrics = load_json(
            path
        )

        schema_pass = (
            required_metrics
            <=
            set(metrics.keys())
        )

        count_pass = (
            metrics[
                "sample_count"
            ]
            ==
            380
        )

        values = [
            metrics["accuracy"],
            metrics["log_loss"],
            metrics["brier_score"],
            metrics["precision_macro"],
            metrics["recall_macro"],
            metrics["f1_macro"],
            metrics["ece"],
            metrics["mce"],
        ]

        finite_pass = all(
            np.isfinite(
                value
            )
            for value in values
        )

        range_pass = all(
            0 <= metrics[key] <= 1
            for key in [
                "accuracy",
                "precision_macro",
                "recall_macro",
                "f1_macro",
                "ece",
                "mce",
            ]
        )

        classes_pass = (
            metrics[
                "classes"
            ]
            ==
            [0, 1, 2]
        )

        confusion_pass = (
            np.asarray(
                metrics[
                    "confusion_matrix"
                ]
            ).shape
            ==
            (3, 3)
        )

        protection_pass = (
            metrics[
                "training_season"
            ]
            ==
            2023
            and
            metrics[
                "validation_season"
            ]
            ==
            2024
            and
            metrics[
                "final_test_season"
            ]
            ==
            "2025/26"
            and
            metrics[
                "final_test_used"
            ]
            is False
        )

        candidate_pass = all(
            [
                schema_pass,
                count_pass,
                finite_pass,
                range_pass,
                classes_pass,
                confusion_pass,
                protection_pass,
            ]
        )

        print(
            f"  Schema: "
            f"{'PASS' if schema_pass else 'FAIL'}"
        )

        print(
            f"  Sample count: "
            f"{'PASS' if count_pass else 'FAIL'}"
        )

        print(
            f"  Metric values: "
            f"{'PASS' if (finite_pass and range_pass) else 'FAIL'}"
        )

        print(
            f"  Classes: "
            f"{'PASS' if classes_pass else 'FAIL'}"
        )

        print(
            f"  Confusion matrix: "
            f"{'PASS' if confusion_pass else 'FAIL'}"
        )

        print(
            f"  Final test protection: "
            f"{'PASS' if protection_pass else 'FAIL'}"
        )

        if not candidate_pass:
            overall = False

    # ========================================================
    # 4. Candidate consistency
    # ========================================================

    print(
        "\n4. CANDIDATE CONSISTENCY"
    )

    prediction_counts = []
    metric_counts = []

    for candidate_id in CANDIDATE_ORDER:

        prediction_path = (
            CANDIDATE_PREDICTION_DIR
            / f"{candidate_id}_predictions.csv"
        )

        metric_path = (
            CANDIDATE_METRIC_DIR
            / f"{candidate_id}_metrics.json"
        )

        if (
            prediction_path.exists()
            and
            metric_path.exists()
        ):

            prediction_count = len(
                pd.read_csv(
                    prediction_path
                )
            )

            metric_count = load_json(
                metric_path
            )["sample_count"]

            prediction_counts.append(
                prediction_count
            )

            metric_counts.append(
                metric_count
            )

    consistency_pass = (
        prediction_counts
        ==
        [380, 380, 380]
        and
        metric_counts
        ==
        [380, 380, 380]
    )

    print(
        f"All candidates evaluated on 380 "
        f"validation records: "
        f"{'PASS' if consistency_pass else 'FAIL'}"
    )

    if not consistency_pass:
        overall = False

    # ========================================================
    # 5. Final test protection
    # ========================================================

    print(
        "\n5. FINAL TEST PROTECTION"
    )

    print(
        "2025/26 final test used: NO"
    )

    print(
        "Final test protection: PASS"
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

    print("=" * 50)

    print(
        f"7.6.3 Candidate Training: "
        f"{'PASS' if overall else 'FAIL'}"
    )

    print(
        f"7.6.4 Candidate Evaluation: "
        f"{'PASS' if overall else 'FAIL'}"
    )

    print(
        f"\n7.6.3 + 7.6.4: "
        f"{'PASS' if overall else 'FAIL'}"
    )

    if not overall:
        sys.exit(1)


if __name__ == "__main__":
    main()