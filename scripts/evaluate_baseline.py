"""
FixtureIQ Stage 7.5.4
Baseline Evaluation.
"""

import sys
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR),
)


from backend.models.probabilities import (
    PREDICTIONS_FILE,
)

from backend.models.evaluation import (
    evaluate_predictions,
    save_metrics,
)


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.5.4"
    )

    print(
        "Baseline Model Evaluation"
    )

    print("=" * 50)

    if not PREDICTIONS_FILE.exists():

        raise FileNotFoundError(
            "Baseline prediction file not found: "
            f"{PREDICTIONS_FILE}"
        )

    predictions = pd.read_csv(
        PREDICTIONS_FILE
    )

    print(
        f"\nPrediction records: "
        f"{len(predictions)}"
    )

    metrics = evaluate_predictions(
        predictions
    )

    print(
        "\nEvaluation"
    )

    print(
        f"Accuracy: "
        f"{metrics['accuracy']:.6f}"
    )

    print(
        f"Log Loss: "
        f"{metrics['log_loss']:.6f}"
    )

    print(
        f"Brier Score: "
        f"{metrics['brier_score']:.6f}"
    )

    print(
        f"Macro Precision: "
        f"{metrics['precision_macro']:.6f}"
    )

    print(
        f"Macro Recall: "
        f"{metrics['recall_macro']:.6f}"
    )

    print(
        f"Macro F1: "
        f"{metrics['f1_macro']:.6f}"
    )

    print(
        "\nPer-class metrics:"
    )

    for class_name, values in (
        metrics["per_class"].items()
    ):

        print(
            f"{class_name}: "
            f"Precision={values['precision']:.6f}, "
            f"Recall={values['recall']:.6f}, "
            f"F1={values['f1']:.6f}, "
            f"Support={values['support']}"
        )

    print(
        "\nConfusion matrix:"
    )

    for row in (
        metrics["confusion_matrix"]
    ):

        print(
            row
        )

    metrics_path = save_metrics(
        metrics
    )

    print(
        "\nMetrics report:"
    )

    print(
        metrics_path
    )

    print(
        "\nSTAGE 7.5.4: PASS"
    )


if __name__ == "__main__":
    main()