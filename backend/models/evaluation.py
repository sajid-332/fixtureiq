"""
FixtureIQ Stage 7.5.4
Baseline Model Evaluation.

Evaluates baseline validation predictions using:
- Accuracy
- Precision
- Recall
- F1
- Log Loss
- Multiclass Brier Score
- Confusion Matrix
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    log_loss,
    confusion_matrix,
)


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
)

METRICS_FILE = (
    MODEL_DIR
    / "baseline_metrics.json"
)

CLASS_LABELS = [
    0,
    1,
    2,
]

CLASS_NAMES = {
    0: "draw",
    1: "home_win",
    2: "away_win",
}


def multiclass_brier_score(
    y_true,
    probabilities,
):
    """
    Calculate the multiclass Brier score.

    Formula:
        mean(sum((p_k - o_k)^2))
    """

    y_true = np.asarray(
        y_true,
        dtype=int,
    )

    probabilities = np.asarray(
        probabilities,
        dtype=float,
    )

    if probabilities.shape != (
        len(y_true),
        3,
    ):
        raise ValueError(
            "Invalid probability matrix shape."
        )

    one_hot = np.zeros_like(
        probabilities
    )

    one_hot[
        np.arange(len(y_true)),
        y_true,
    ] = 1.0

    return float(
        np.mean(
            np.sum(
                (
                    probabilities
                    -
                    one_hot
                ) ** 2,
                axis=1,
            )
        )
    )


def evaluate_predictions(
    predictions: pd.DataFrame,
):
    """
    Evaluate a prediction dataframe.
    """

    required_columns = {
        "fixture_id",
        "actual",
        "predicted",
        "prob_home",
        "prob_draw",
        "prob_away",
    }

    missing = (
        required_columns
        -
        set(predictions.columns)
    )

    if missing:
        raise ValueError(
            f"Missing prediction columns: "
            f"{sorted(missing)}"
        )

    if predictions.empty:
        raise ValueError(
            "Prediction dataframe is empty."
        )

    y_true = (
        predictions["actual"]
        .astype(int)
        .to_numpy()
    )

    y_pred = (
        predictions["predicted"]
        .astype(int)
        .to_numpy()
    )

    # Model probability order is:
    # 0 = draw
    # 1 = home
    # 2 = away

    probabilities = predictions[
        [
            "prob_draw",
            "prob_home",
            "prob_away",
        ]
    ].to_numpy(
        dtype=float
    )

    if not np.isfinite(
        probabilities
    ).all():
        raise ValueError(
            "Probabilities contain NaN/Inf."
        )

    if (
        probabilities < 0
    ).any() or (
        probabilities > 1
    ).any():

        raise ValueError(
            "Probabilities outside [0, 1]."
        )

    if not np.allclose(
        probabilities.sum(axis=1),
        1.0,
        atol=1e-8,
    ):
        raise ValueError(
            "Probability rows do not sum to 1."
        )

    accuracy = accuracy_score(
        y_true,
        y_pred,
    )

    precision, recall, f1, support = (
        precision_recall_fscore_support(
            y_true,
            y_pred,
            labels=CLASS_LABELS,
            zero_division=0,
        )
    )

    logloss = log_loss(
        y_true,
        probabilities,
        labels=CLASS_LABELS,
    )

    brier = multiclass_brier_score(
        y_true,
        probabilities,
    )

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=CLASS_LABELS,
    )

    per_class = {}

    for index, class_id in enumerate(
        CLASS_LABELS
    ):

        per_class[
            CLASS_NAMES[class_id]
        ] = {
            "precision":
                float(precision[index]),

            "recall":
                float(recall[index]),

            "f1":
                float(f1[index]),

            "support":
                int(support[index]),
        }

    return {
        "sample_count":
            int(len(predictions)),

        "accuracy":
            float(accuracy),

        "log_loss":
            float(logloss),

        "brier_score":
            float(brier),

        "precision_macro":
            float(np.mean(precision)),

        "recall_macro":
            float(np.mean(recall)),

        "f1_macro":
            float(np.mean(f1)),

        "per_class":
            per_class,

        "confusion_matrix": [
            [
                int(value)
                for value in row
            ]
            for row in matrix
        ],

        "class_order": [
            "draw",
            "home_win",
            "away_win",
        ],
    }


def save_metrics(
    metrics: dict,
):
    """
    Save evaluation metrics.
    """

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with METRICS_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metrics,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return METRICS_FILE