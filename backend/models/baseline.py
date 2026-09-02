"""
FixtureIQ Stage 7.5.2
Baseline Multiclass Model.

The baseline uses Logistic Regression because it is:
- simple
- reproducible
- probability-producing
- interpretable
- suitable as a benchmark

This is NOT the final FixtureIQ model.
"""

import json
from pathlib import Path

import joblib
import numpy as np

from sklearn.linear_model import LogisticRegression


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
)

BASELINE_MODEL_FILE = (
    MODEL_DIR
    / "baseline_model.joblib"
)

BASELINE_METADATA_FILE = (
    MODEL_DIR
    / "baseline_model_metadata.json"
)


def train_baseline(
    X_train,
    y_train,
):
    """
    Train the baseline Logistic Regression model.
    """

    if len(X_train) != len(y_train):
        raise ValueError(
            "Training feature and target counts "
            "do not match."
        )

    model = LogisticRegression(
        max_iter=2000,
        solver="lbfgs",
        random_state=42,
    )

    model.fit(
        X_train,
        y_train,
    )

    return model


def validate_probability_output(
    probabilities,
):
    """
    Validate multiclass probability output.

    Expected:
        shape = (n_samples, 3)

    Each row must:
        - contain finite values
        - contain values between 0 and 1
        - sum to 1
    """

    probabilities = np.asarray(
        probabilities,
        dtype=float,
    )

    if probabilities.ndim != 2:
        raise ValueError(
            "Probability output must be 2-dimensional."
        )

    if probabilities.shape[1] != 3:
        raise ValueError(
            "Expected exactly 3 probability classes."
        )

    if not np.isfinite(
        probabilities
    ).all():
        raise ValueError(
            "Probability output contains NaN/Inf."
        )

    if (
        probabilities < 0
    ).any() or (
        probabilities > 1
    ).any():

        raise ValueError(
            "Probability values must be between "
            "0 and 1."
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

    return True


def save_baseline_model(
    model,
    feature_columns,
    training_rows,
):
    """
    Save the trained baseline model and metadata.
    """

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        model,
        BASELINE_MODEL_FILE,
    )

    metadata = {
        "stage": "7.5.2",

        "model_type":
            "LogisticRegression",

        "solver":
            "lbfgs",

        "max_iter":
            2000,

        "random_state":
            42,

        "training_rows":
            int(training_rows),

        "feature_count":
            len(feature_columns),

        "feature_columns":
            list(feature_columns),

        "classes":
            [
                int(value)
                for value
                in model.classes_
            ],

        "target_mapping": {
            "0": "draw",
            "1": "home_win",
            "2": "away_win",
        },
    }

    with BASELINE_METADATA_FILE.open(
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
        BASELINE_MODEL_FILE,
        BASELINE_METADATA_FILE,
    )


def load_baseline_model():
    """
    Load the saved baseline model.
    """

    if not BASELINE_MODEL_FILE.exists():
        raise FileNotFoundError(
            "Baseline model not found: "
            f"{BASELINE_MODEL_FILE}"
        )

    return joblib.load(
        BASELINE_MODEL_FILE
    )