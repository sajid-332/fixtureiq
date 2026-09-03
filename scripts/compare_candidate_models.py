"""
FixtureIQ Stage 7.6.5
Candidate Model Comparison & Selection

Compares:
- Stage 7.5 baseline
- Scaled Logistic Regression
- Regularized Logistic Regression
- Random Forest

Selection priority:
1. Log Loss       lower is better
2. Brier Score    lower is better
3. ECE            lower is better
4. MCE            lower is better
5. Accuracy       higher is better

2025/26 final test remains protected.
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

BASELINE_METRICS_FILE = (
    MODEL_DIR
    / "baseline_metrics.json"
)

CANDIDATE_METRIC_DIR = (
    MODEL_DIR
    / "candidate_metrics"
)

OUTPUT_FILE = (
    MODEL_DIR
    / "candidate_comparison.json"
)

SUMMARY_FILE = (
    MODEL_DIR
    / "candidate_comparison.csv"
)


CANDIDATE_ORDER = [
    "baseline",
    "scaled_logistic",
    "regularized_logistic",
    "random_forest",
]


CANDIDATE_NAMES = {
    "baseline":
        "Stage 7.5 Baseline Logistic Regression",

    "scaled_logistic":
        "Scaled Logistic Regression",

    "regularized_logistic":
        "Regularized Logistic Regression",

    "random_forest":
        "Random Forest",
}


def load_json(path):

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def load_baseline():

    if not BASELINE_METRICS_FILE.exists():

        raise FileNotFoundError(
            "Baseline metrics not found: "
            f"{BASELINE_METRICS_FILE}"
        )

    data = load_json(
        BASELINE_METRICS_FILE
    )

    return {
        "candidate_id":
            "baseline",

        "model_name":
            CANDIDATE_NAMES[
                "baseline"
            ],

        "validation_season":
            2024,

        "sample_count":
            data.get(
                "sample_count",
                380,
            ),

        "accuracy":
            float(
                data["accuracy"]
            ),

        "log_loss":
            float(
                data["log_loss"]
            ),

        "brier_score":
            float(
                data["brier_score"]
            ),

        "precision_macro":
            float(
                data.get(
                    "precision_macro",
                    0.0,
                )
            ),

        "recall_macro":
            float(
                data.get(
                    "recall_macro",
                    0.0,
                )
            ),

        "f1_macro":
            float(
                data.get(
                    "f1_macro",
                    0.0,
                )
            ),

        "ece":
            float(
                data.get(
                    "ece",
                    0.0,
                )
            ),

        "mce":
            float(
                data.get(
                    "mce",
                    0.0,
                )
            ),

        "training_season":
            2023,

        "final_test_season":
            "2025/26",

        "final_test_used":
            False,
    }


def load_candidate(candidate_id):

    path = (
        CANDIDATE_METRIC_DIR
        / f"{candidate_id}_metrics.json"
    )

    if not path.exists():

        raise FileNotFoundError(
            f"Candidate metrics not found: {path}"
        )

    data = load_json(
        path
    )

    return {
        "candidate_id":
            candidate_id,

        "model_name":
            data["model_name"],

        "validation_season":
            data["validation_season"],

        "sample_count":
            data["sample_count"],

        "accuracy":
            float(
                data["accuracy"]
            ),

        "log_loss":
            float(
                data["log_loss"]
            ),

        "brier_score":
            float(
                data["brier_score"]
            ),

        "precision_macro":
            float(
                data["precision_macro"]
            ),

        "recall_macro":
            float(
                data["recall_macro"]
            ),

        "f1_macro":
            float(
                data["f1_macro"]
            ),

        "ece":
            float(
                data["ece"]
            ),

        "mce":
            float(
                data["mce"]
            ),

        "training_season":
            data["training_season"],

        "final_test_season":
            data["final_test_season"],

        "final_test_used":
            data["final_test_used"],
    }


def validate_result(result):

    required = [
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
        "training_season",
        "final_test_season",
        "final_test_used",
    ]

    for key in required:

        if key not in result:

            raise ValueError(
                f"Missing metric field: {key}"
            )

    if result[
        "validation_season"
    ] != 2024:

        raise ValueError(
            "Candidate evaluation must use "
            "2024 validation data."
        )

    if result[
        "sample_count"
    ] != 380:

        raise ValueError(
            "Expected exactly 380 validation records."
        )

    if result[
        "training_season"
    ] != 2023:

        raise ValueError(
            "Candidate training season must be 2023."
        )

    if result[
        "final_test_season"
    ] != "2025/26":

        raise ValueError(
            "Final test season metadata mismatch."
        )

    if result[
        "final_test_used"
    ] is not False:

        raise ValueError(
            "A candidate indicates that the "
            "2025/26 final test was used."
        )


def calculate_improvements(
    candidate,
    baseline,
):
    """
    Positive improvement means better performance.

    For error metrics:
        baseline - candidate

    For accuracy:
        candidate - baseline
    """

    return {
        "accuracy_delta":
            candidate["accuracy"]
            -
            baseline["accuracy"],

        "log_loss_improvement":
            baseline["log_loss"]
            -
            candidate["log_loss"],

        "brier_score_improvement":
            baseline["brier_score"]
            -
            candidate["brier_score"],

        "ece_improvement":
            baseline["ece"]
            -
            candidate["ece"],

        "mce_improvement":
            baseline["mce"]
            -
            candidate["mce"],
    }


def selection_key(result):
    """
    Lower is better for the first four metrics.
    Accuracy is the final tie-breaker.
    """

    return (
        result["log_loss"],
        result["brier_score"],
        result["ece"],
        result["mce"],
        -result["accuracy"],
    )


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.6.5"
    )

    print(
        "Candidate Model Comparison & Selection"
    )

    print("=" * 50)

    baseline = load_baseline()

    candidates = [
        baseline
    ]

    for candidate_id in [
        "scaled_logistic",
        "regularized_logistic",
        "random_forest",
    ]:

        candidates.append(
            load_candidate(
                candidate_id
            )
        )

    # --------------------------------------------------------
    # Validate all results
    # --------------------------------------------------------

    for result in candidates:
        validate_result(
            result
        )

    # --------------------------------------------------------
    # Print comparison
    # --------------------------------------------------------

    print(
        "\nVALIDATION COMPARISON"
    )

    print(
        "-" * 90
    )

    print(
        f"{'Model':<32}"
        f"{'Accuracy':>12}"
        f"{'LogLoss':>12}"
        f"{'Brier':>12}"
        f"{'ECE':>12}"
        f"{'MCE':>12}"
    )

    print(
        "-" * 90
    )

    for result in candidates:

        print(
            f"{result['model_name']:<32}"
            f"{result['accuracy']:>12.6f}"
            f"{result['log_loss']:>12.6f}"
            f"{result['brier_score']:>12.6f}"
            f"{result['ece']:>12.6f}"
            f"{result['mce']:>12.6f}"
        )

    # --------------------------------------------------------
    # Select candidate
    # --------------------------------------------------------

    candidate_only = [
        result
        for result in candidates
        if result["candidate_id"]
        != "baseline"
    ]

    ranked = sorted(
        candidate_only,
        key=selection_key,
    )

    selected = ranked[0]

    # --------------------------------------------------------
    # Baseline comparison
    # --------------------------------------------------------

    print(
        "\nBASELINE IMPROVEMENT"
    )

    print(
        "-" * 70
    )

    improvement_records = []

    for result in candidate_only:

        improvement = (
            calculate_improvements(
                result,
                baseline,
            )
        )

        improvement_records.append(
            {
                "candidate_id":
                    result["candidate_id"],

                "model_name":
                    result["model_name"],

                **improvement,
            }
        )

        print(
            f"\n{result['model_name']}"
        )

        print(
            f"Accuracy delta: "
            f"{improvement['accuracy_delta']:+.6f}"
        )

        print(
            f"Log Loss improvement: "
            f"{improvement['log_loss_improvement']:+.6f}"
        )

        print(
            f"Brier improvement: "
            f"{improvement['brier_score_improvement']:+.6f}"
        )

        print(
            f"ECE improvement: "
            f"{improvement['ece_improvement']:+.6f}"
        )

        print(
            f"MCE improvement: "
            f"{improvement['mce_improvement']:+.6f}"
        )

    # --------------------------------------------------------
    # Ranking
    # --------------------------------------------------------

    print(
        "\nCANDIDATE RANKING"
    )

    for index, result in enumerate(
        ranked,
        start=1,
    ):

        print(
            f"{index}. "
            f"{result['model_name']}"
        )

    # --------------------------------------------------------
    # Protection
    # --------------------------------------------------------

    final_test_protection = all(
        result[
            "final_test_used"
        ] is False
        for result in candidates
    )

    # --------------------------------------------------------
    # Build report
    # --------------------------------------------------------

    report = {
        "stage": "7.6.5",

        "purpose":
            "Compare candidate models against "
            "the frozen Stage 7.5 baseline.",

        "validation_season":
            2024,

        "training_season":
            2023,

        "final_test_season":
            "2025/26",

        "final_test_used":
            False,

        "selection_priority": [
            "log_loss",
            "brier_score",
            "ece",
            "mce",
            "accuracy",
        ],

        "direction": {
            "log_loss": "lower_is_better",
            "brier_score": "lower_is_better",
            "ece": "lower_is_better",
            "mce": "lower_is_better",
            "accuracy": "higher_is_better",
        },

        "models": candidates,

        "baseline_improvements":
            improvement_records,

        "ranking": [
            result[
                "candidate_id"
            ]
            for result in ranked
        ],

        "selected_candidate":
            selected[
                "candidate_id"
            ],

        "selected_model":
            selected[
                "model_name"
            ],

        "selection_reason":
            "Best validation result under the "
            "predefined metric priority.",

        "final_test_protection":
            final_test_protection,
    }

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # --------------------------------------------------------
    # CSV summary
    # --------------------------------------------------------

    rows = []

    for rank, result in enumerate(
        ranked,
        start=1,
    ):

        rows.append(
            {
                "rank":
                    rank,

                "candidate_id":
                    result["candidate_id"],

                "model_name":
                    result["model_name"],

                "accuracy":
                    result["accuracy"],

                "log_loss":
                    result["log_loss"],

                "brier_score":
                    result["brier_score"],

                "ece":
                    result["ece"],

                "mce":
                    result["mce"],
            }
        )

    pd.DataFrame(
        rows
    ).to_csv(
        SUMMARY_FILE,
        index=False,
    )

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    print(
        "\n" + "=" * 50
    )

    print(
        "SELECTION RESULT"
    )

    print(
        f"Selected candidate: "
        f"{selected['model_name']}"
    )

    print(
        f"Log Loss: "
        f"{selected['log_loss']:.6f}"
    )

    print(
        f"Brier Score: "
        f"{selected['brier_score']:.6f}"
    )

    print(
        f"ECE: "
        f"{selected['ece']:.6f}"
    )

    print(
        f"MCE: "
        f"{selected['mce']:.6f}"
    )

    print(
        f"Accuracy: "
        f"{selected['accuracy']:.6f}"
    )

    print(
        "\nComparison report:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nComparison CSV:"
    )

    print(
        SUMMARY_FILE
    )

    print(
        "\n2025/26 final test protection: "
        f"{'PASS' if final_test_protection else 'FAIL'}"
    )

    print(
        "\nSTAGE 7.6.5: PASS"
    )


if __name__ == "__main__":
    main()