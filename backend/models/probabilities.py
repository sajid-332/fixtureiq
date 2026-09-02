"""
FixtureIQ Stage 7.5.3
Baseline Probability Generation.

Loads the frozen Stage 7.5.2 baseline model and generates
validation-set outcome probabilities.

No model retraining occurs here.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
)

PREDICTIONS_FILE = (
    MODEL_DIR
    / "baseline_predictions.csv"
)

PREDICTION_METADATA_FILE = (
    MODEL_DIR
    / "baseline_prediction_metadata.json"
)

TARGET_MAPPING = {
    0: "draw",
    1: "home_win",
    2: "away_win",
}


def generate_baseline_predictions(
    model,
    X_validation,
    y_validation,
    fixture_ids,
):
    """
    Generate validated baseline predictions.
    """

    if len(X_validation) != len(y_validation):
        raise ValueError(
            "Validation feature and target counts "
            "do not match."
        )

    if len(X_validation) != len(fixture_ids):
        raise ValueError(
            "Validation features and fixture IDs "
            "do not match."
        )

    expected_classes = np.array(
        [0, 1, 2]
    )

    model_classes = np.asarray(
        model.classes_
    )

    if not np.array_equal(
        model_classes,
        expected_classes,
    ):
        raise ValueError(
            "Model class mapping does not match "
            "FixtureIQ target mapping."
        )

    probabilities = model.predict_proba(
        X_validation
    )

    probabilities = np.asarray(
        probabilities,
        dtype=float,
    )

    if probabilities.shape != (
        len(X_validation),
        3,
    ):
        raise ValueError(
            "Unexpected probability matrix shape."
        )

    if not np.isfinite(
        probabilities
    ).all():
        raise ValueError(
            "Probability matrix contains NaN/Inf."
        )

    if (
        probabilities < 0
    ).any() or (
        probabilities > 1
    ).any():

        raise ValueError(
            "Probability values are outside [0, 1]."
        )

    row_sums = probabilities.sum(
        axis=1
    )

    if not np.allclose(
        row_sums,
        1.0,
        atol=1e-8,
    ):
        raise ValueError(
            "Probability rows do not sum to 1."
        )

    predicted = np.argmax(
        probabilities,
        axis=1,
    )

    predictions = pd.DataFrame(
        {
            "fixture_id":
                fixture_ids.astype(int),

            "actual":
                y_validation.astype(int),

            "predicted":
                predicted.astype(int),

            "prob_home":
                probabilities[:, 1],

            "prob_draw":
                probabilities[:, 0],

            "prob_away":
                probabilities[:, 2],
        }
    )

    return predictions


def save_predictions(
    predictions: pd.DataFrame,
    feature_count: int,
):
    """
    Save prediction data and metadata.
    """

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    predictions.to_csv(
        PREDICTIONS_FILE,
        index=False,
    )

    metadata = {
        "stage": "7.5.3",
        "model_type":
            "LogisticRegression",
        "validation_rows":
            int(len(predictions)),
        "feature_count":
            int(feature_count),
        "target_mapping": {
            "0": "draw",
            "1": "home_win",
            "2": "away_win",
        },
        "prediction_columns": [
            "fixture_id",
            "actual",
            "predicted",
            "prob_home",
            "prob_draw",
            "prob_away",
        ],
        "probability_sum_tolerance":
            1e-8,
    }

    with PREDICTION_METADATA_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return (
        PREDICTIONS_FILE,
        PREDICTION_METADATA_FILE,
    )