"""
FixtureIQ Stage 7.6.3 + 7.6.4

7.6.3 Candidate Model Training
7.6.4 Candidate Model Evaluation

Candidates:
1. Scaled Logistic Regression
2. Regularized Logistic Regression
3. Random Forest

Data protection:
2023 -> training
2024 -> validation
2025/26 -> untouched

Important:
The model matrices contain exactly 86 model features.
fixture_id is metadata and is NOT a model feature.
Fixture IDs are recovered from validation_features.csv
for prediction-artifact alignment.
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    log_loss,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


BASE_DIR = Path(__file__).resolve().parents[2]

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


X_TRAIN_FILE = MODEL_DIR / "X_train.csv"
Y_TRAIN_FILE = MODEL_DIR / "y_train.csv"

X_VALIDATION_FILE = MODEL_DIR / "X_validation.csv"
Y_VALIDATION_FILE = MODEL_DIR / "y_validation.csv"

VALIDATION_FEATURES_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "validation_features.csv"
)


CLASS_IDS = [0, 1, 2]

CLASS_NAMES = {
    0: "draw",
    1: "home_win",
    2: "away_win",
}


CANDIDATE_ORDER = [
    "scaled_logistic",
    "regularized_logistic",
    "random_forest",
]


CANDIDATES = {
    "scaled_logistic": {
        "name": "Scaled Logistic Regression",
        "type": "LogisticRegression",
        "preprocessing": "StandardScaler",
        "parameters": {
            "C": 1.0,
            "solver": "lbfgs",
            "max_iter": 5000,
            "random_state": 42,
        },
    },

    "regularized_logistic": {
        "name": "Regularized Logistic Regression",
        "type": "LogisticRegression",
        "preprocessing": "StandardScaler",
        "parameters": {
            "C": 0.1,
            "solver": "lbfgs",
            "max_iter": 5000,
            "random_state": 42,
        },
    },

    "random_forest": {
        "name": "Random Forest",
        "type": "RandomForestClassifier",
        "preprocessing": "None",
        "parameters": {
            "n_estimators": 500,
            "max_depth": None,
            "min_samples_leaf": 3,
            "random_state": 42,
            "n_jobs": -1,
        },
    },
}


def load_training_data():
    """Load the frozen training partition."""

    X_train = pd.read_csv(
        X_TRAIN_FILE
    )

    y_train = pd.read_csv(
        Y_TRAIN_FILE
    )

    if "target" not in y_train.columns:
        raise ValueError(
            "Training target column 'target' not found."
        )

    return (
        X_train,
        y_train["target"].astype(int),
    )


def load_validation_data():
    """Load the frozen validation partition."""

    X_validation = pd.read_csv(
        X_VALIDATION_FILE
    )

    y_validation = pd.read_csv(
        Y_VALIDATION_FILE
    )

    if "target" not in y_validation.columns:
        raise ValueError(
            "Validation target column 'target' not found."
        )

    return (
        X_validation,
        y_validation["target"].astype(int),
    )


def load_validation_fixture_ids():
    """
    Load fixture IDs from the original validation feature dataset.

    fixture_id is metadata only and must never enter the
    86-feature model matrix.
    """

    if not VALIDATION_FEATURES_FILE.exists():

        raise FileNotFoundError(
            "Validation feature dataset not found: "
            f"{VALIDATION_FEATURES_FILE}"
        )

    validation_features = pd.read_csv(
        VALIDATION_FEATURES_FILE
    )

    if "fixture_id" not in validation_features.columns:

        raise ValueError(
            "validation_features.csv does not contain "
            "'fixture_id'."
        )

    fixture_ids = (
        validation_features[
            "fixture_id"
        ]
        .copy()
    )

    if fixture_ids.isna().any():

        raise ValueError(
            "Validation fixture IDs contain missing values."
        )

    if fixture_ids.duplicated().any():

        raise ValueError(
            "Validation fixture IDs contain duplicates."
        )

    if len(fixture_ids) != 380:

        raise ValueError(
            "Expected 380 validation fixture IDs, "
            f"found {len(fixture_ids)}."
        )

    return fixture_ids.reset_index(
        drop=True
    )


def validate_partitions(
    X_train,
    y_train,
    X_validation,
    y_validation,
    fixture_ids,
):
    """Validate the model input contract."""

    if X_train.shape != (380, 86):

        raise ValueError(
            f"Unexpected training shape: "
            f"{X_train.shape}"
        )

    if X_validation.shape != (380, 86):

        raise ValueError(
            f"Unexpected validation shape: "
            f"{X_validation.shape}"
        )

    if len(y_train) != 380:

        raise ValueError(
            "Training target count is not 380."
        )

    if len(y_validation) != 380:

        raise ValueError(
            "Validation target count is not 380."
        )

    if len(fixture_ids) != 380:

        raise ValueError(
            "Validation fixture ID count is not 380."
        )

    if list(X_train.columns) != list(
        X_validation.columns
    ):

        raise ValueError(
            "Training and validation feature "
            "columns do not match."
        )

    if "fixture_id" in X_train.columns:

        raise ValueError(
            "fixture_id must not be part of "
            "the model feature matrix."
        )

    if "fixture_id" in X_validation.columns:

        raise ValueError(
            "fixture_id must not be part of "
            "the model feature matrix."
        )

    if not set(
        y_train.unique()
    ).issubset(
        set(CLASS_IDS)
    ):

        raise ValueError(
            "Training target contains invalid classes."
        )

    if not set(
        y_validation.unique()
    ).issubset(
        set(CLASS_IDS)
    ):

        raise ValueError(
            "Validation target contains invalid classes."
        )

    if X_train.isna().any().any():

        raise ValueError(
            "Training data contains NaN values."
        )

    if X_validation.isna().any().any():

        raise ValueError(
            "Validation data contains NaN values."
        )

    if not np.isfinite(
        X_train.to_numpy(
            dtype=float
        )
    ).all():

        raise ValueError(
            "Training data contains infinite values."
        )

    if not np.isfinite(
        X_validation.to_numpy(
            dtype=float
        )
    ).all():

        raise ValueError(
            "Validation data contains infinite values."
        )


def build_model(candidate_id):
    """Build one candidate model."""

    config = CANDIDATES[
        candidate_id
    ]

    parameters = config[
        "parameters"
    ]

    if candidate_id == "scaled_logistic":

        return Pipeline(
            steps=[
                (
                    "scaler",
                    StandardScaler(),
                ),
                (
                    "classifier",
                    LogisticRegression(
                        C=parameters["C"],
                        solver=parameters["solver"],
                        max_iter=parameters["max_iter"],
                        random_state=parameters["random_state"],
                    ),
                ),
            ]
        )

    if candidate_id == "regularized_logistic":

        return Pipeline(
            steps=[
                (
                    "scaler",
                    StandardScaler(),
                ),
                (
                    "classifier",
                    LogisticRegression(
                        C=parameters["C"],
                        solver=parameters["solver"],
                        max_iter=parameters["max_iter"],
                        random_state=parameters["random_state"],
                    ),
                ),
            ]
        )

    if candidate_id == "random_forest":

        return RandomForestClassifier(
            n_estimators=parameters[
                "n_estimators"
            ],
            max_depth=parameters[
                "max_depth"
            ],
            min_samples_leaf=parameters[
                "min_samples_leaf"
            ],
            random_state=parameters[
                "random_state"
            ],
            n_jobs=parameters[
                "n_jobs"
            ],
        )

    raise ValueError(
        f"Unknown candidate: {candidate_id}"
    )


def calculate_multiclass_brier(
    y_true,
    probabilities,
):
    """
    Multiclass Brier score.
    """

    y_true = np.asarray(
        y_true,
        dtype=int,
    )

    probabilities = np.asarray(
        probabilities,
        dtype=float,
    )

    one_hot = np.zeros_like(
        probabilities
    )

    for index, target in enumerate(
        y_true
    ):

        one_hot[
            index,
            target,
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


def calculate_class_calibration(
    y_true,
    probabilities,
    class_id,
    bin_count=10,
):
    """Calculate one-vs-rest ECE/MCE."""

    y_true = np.asarray(
        y_true,
        dtype=int,
    )

    class_probabilities = (
        probabilities[:, class_id]
    )

    bin_edges = np.linspace(
        0.0,
        1.0,
        bin_count + 1,
    )

    weighted_error = 0.0
    maximum_error = 0.0

    total_samples = len(
        y_true
    )

    bins = []

    for index in range(
        bin_count
    ):

        lower = bin_edges[index]
        upper = bin_edges[index + 1]

        if index == bin_count - 1:

            mask = (
                (class_probabilities >= lower)
                &
                (class_probabilities <= upper)
            )

        else:

            mask = (
                (class_probabilities >= lower)
                &
                (class_probabilities < upper)
            )

        count = int(
            mask.sum()
        )

        if count == 0:

            bins.append(
                {
                    "bin": index + 1,
                    "lower": float(lower),
                    "upper": float(upper),
                    "count": 0,
                    "mean_predicted": None,
                    "observed_frequency": None,
                    "calibration_error": None,
                }
            )

            continue

        mean_predicted = float(
            class_probabilities[
                mask
            ].mean()
        )

        observed_frequency = float(
            (
                y_true[mask]
                ==
                class_id
            ).mean()
        )

        error = abs(
            mean_predicted
            -
            observed_frequency
        )

        weighted_error += (
            count
            /
            total_samples
        ) * error

        maximum_error = max(
            maximum_error,
            error,
        )

        bins.append(
            {
                "bin": index + 1,
                "lower": float(lower),
                "upper": float(upper),
                "count": count,
                "mean_predicted": mean_predicted,
                "observed_frequency": observed_frequency,
                "calibration_error": float(error),
            }
        )

    return {
        "class_id": int(class_id),
        "class_name": CLASS_NAMES[class_id],
        "bin_count": int(bin_count),
        "bins": bins,
        "ece": float(weighted_error),
        "mce": float(maximum_error),
    }


def calculate_calibration(
    y_true,
    probabilities,
):
    """Calculate macro ECE/MCE."""

    class_results = {}

    eces = []
    mces = []

    for class_id in CLASS_IDS:

        result = calculate_class_calibration(
            y_true,
            probabilities,
            class_id,
            bin_count=10,
        )

        class_results[
            CLASS_NAMES[class_id]
        ] = result

        eces.append(
            result["ece"]
        )

        mces.append(
            result["mce"]
        )

    return {
        "ece": float(
            np.mean(eces)
        ),
        "mce": float(
            np.mean(mces)
        ),
        "bin_count": 10,
        "per_class": class_results,
    }


def validate_probabilities(
    probabilities,
):
    """Validate probability matrix."""

    probabilities = np.asarray(
        probabilities,
        dtype=float,
    )

    if probabilities.ndim != 2:

        raise ValueError(
            "Probability matrix must be two-dimensional."
        )

    if probabilities.shape[1] != 3:

        raise ValueError(
            "Expected probabilities for "
            "exactly three classes."
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
            "Probability values outside [0, 1]."
        )

    if not np.allclose(
        probabilities.sum(
            axis=1
        ),
        1.0,
        atol=1e-8,
    ):

        raise ValueError(
            "Probability rows do not sum to 1."
        )


def save_json(
    data,
    path,
):
    """Save JSON artifact."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def train_candidate(
    candidate_id,
    X_train,
    y_train,
):
    """Train and save one candidate."""

    model = build_model(
        candidate_id
    )

    model.fit(
        X_train,
        y_train,
    )

    CANDIDATE_MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    model_path = (
        CANDIDATE_MODEL_DIR
        / f"{candidate_id}.joblib"
    )

    joblib.dump(
        model,
        model_path,
    )

    config = CANDIDATES[
        candidate_id
    ]

    metadata = {
        "stage": "7.6.3",

        "candidate_id":
            candidate_id,

        "model_name":
            config["name"],

        "model_type":
            config["type"],

        "preprocessing":
            config["preprocessing"],

        "parameters":
            config["parameters"],

        "training_season":
            2023,

        "training_rows":
            int(len(X_train)),

        "feature_count":
            int(X_train.shape[1]),

        "feature_count_excludes_fixture_id":
            True,

        "target_classes":
            CLASS_IDS,

        "target_mapping": {
            "0": "draw",
            "1": "home_win",
            "2": "away_win",
        },

        "validation_season":
            2024,

        "validation_rows":
            380,

        "final_test_season":
            "2025/26",

        "final_test_used":
            False,
    }

    metadata_path = (
        CANDIDATE_MODEL_DIR
        / f"{candidate_id}_metadata.json"
    )

    save_json(
        metadata,
        metadata_path,
    )

    return (
        model,
        model_path,
        metadata_path,
    )


def evaluate_candidate(
    candidate_id,
    model,
    X_validation,
    y_validation,
    fixture_ids,
):
    """Evaluate a trained candidate."""

    probabilities = model.predict_proba(
        X_validation
    )

    validate_probabilities(
        probabilities
    )

    classes = list(
        model.classes_
    )

    if classes != CLASS_IDS:

        raise ValueError(
            f"Unexpected model classes: "
            f"{classes}"
        )

    predictions = (
        np.argmax(
            probabilities,
            axis=1,
        )
    )

    actual = (
        y_validation
        .astype(int)
        .to_numpy()
    )

    if len(fixture_ids) != len(
        actual
    ):

        raise ValueError(
            "Fixture ID count does not match "
            "validation prediction count."
        )

    probability_columns = {
        "prob_draw":
            probabilities[:, 0],

        "prob_home":
            probabilities[:, 1],

        "prob_away":
            probabilities[:, 2],
    }

    prediction_frame = pd.DataFrame(
        {
            "fixture_id":
                fixture_ids.values,

            "actual":
                actual,

            "predicted":
                predictions,

            **probability_columns,
        }
    )

    if prediction_frame[
        "fixture_id"
    ].nunique() != 380:

        raise ValueError(
            "Prediction artifact contains duplicate "
            "fixture IDs."
        )

    accuracy = accuracy_score(
        actual,
        predictions,
    )

    logloss = log_loss(
        actual,
        probabilities,
        labels=CLASS_IDS,
    )

    brier = calculate_multiclass_brier(
        actual,
        probabilities,
    )

    precision = precision_score(
        actual,
        predictions,
        labels=CLASS_IDS,
        average="macro",
        zero_division=0,
    )

    recall = recall_score(
        actual,
        predictions,
        labels=CLASS_IDS,
        average="macro",
        zero_division=0,
    )

    f1 = f1_score(
        actual,
        predictions,
        labels=CLASS_IDS,
        average="macro",
        zero_division=0,
    )

    confusion = confusion_matrix(
        actual,
        predictions,
        labels=CLASS_IDS,
    )

    calibration = calculate_calibration(
        actual,
        probabilities,
    )

    metrics = {
        "stage": "7.6.4",

        "candidate_id":
            candidate_id,

        "model_name":
            CANDIDATES[
                candidate_id
            ]["name"],

        "validation_season":
            2024,

        "sample_count":
            int(len(actual)),

        "accuracy":
            float(accuracy),

        "log_loss":
            float(logloss),

        "brier_score":
            float(brier),

        "precision_macro":
            float(precision),

        "recall_macro":
            float(recall),

        "f1_macro":
            float(f1),

        "ece":
            calibration["ece"],

        "mce":
            calibration["mce"],

        "calibration":
            calibration,

        "classes":
            CLASS_IDS,

        "confusion_matrix":
            confusion.tolist(),

        "training_season":
            2023,

        "final_test_season":
            "2025/26",

        "final_test_used":
            False,
    }

    CANDIDATE_PREDICTION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    prediction_path = (
        CANDIDATE_PREDICTION_DIR
        / f"{candidate_id}_predictions.csv"
    )

    prediction_frame.to_csv(
        prediction_path,
        index=False,
    )

    CANDIDATE_METRIC_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    metrics_path = (
        CANDIDATE_METRIC_DIR
        / f"{candidate_id}_metrics.json"
    )

    save_json(
        metrics,
        metrics_path,
    )

    return (
        prediction_frame,
        metrics,
        prediction_path,
        metrics_path,
    )


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.6.3 + 7.6.4"
    )

    print(
        "Candidate Model Training + Evaluation"
    )

    print("=" * 50)

    (
        X_train,
        y_train,
    ) = load_training_data()

    (
        X_validation,
        y_validation,
    ) = load_validation_data()

    fixture_ids = (
        load_validation_fixture_ids()
    )

    validate_partitions(
        X_train,
        y_train,
        X_validation,
        y_validation,
        fixture_ids,
    )

    print(
        "\nData contract"
    )

    print(
        "Training season: 2023"
    )

    print(
        f"Training rows: {len(X_train)}"
    )

    print(
        "Validation season: 2024"
    )

    print(
        f"Validation rows: {len(X_validation)}"
    )

    print(
        f"Features: {X_train.shape[1]}"
    )

    print(
        "fixture_id in model matrix: NO"
    )

    print(
        "2025/26 final test: PROTECTED"
    )

    results = []

    for candidate_id in CANDIDATE_ORDER:

        config = CANDIDATES[
            candidate_id
        ]

        print(
            "\n" + "-" * 50
        )

        print(
            f"7.6.3 TRAINING: "
            f"{config['name']}"
        )

        (
            model,
            model_path,
            metadata_path,
        ) = train_candidate(
            candidate_id,
            X_train,
            y_train,
        )

        print(
            "Model fitting: PASS"
        )

        print(
            f"Model artifact: "
            f"{model_path}"
        )

        print(
            f"Metadata: "
            f"{metadata_path}"
        )

        print(
            f"\n7.6.4 EVALUATION: "
            f"{config['name']}"
        )

        (
            prediction_frame,
            metrics,
            prediction_path,
            metrics_path,
        ) = evaluate_candidate(
            candidate_id,
            model,
            X_validation,
            y_validation,
            fixture_ids,
        )

        print(
            f"Predictions: "
            f"{len(prediction_frame)}"
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
            f"ECE: "
            f"{metrics['ece']:.6f}"
        )

        print(
            f"MCE: "
            f"{metrics['mce']:.6f}"
        )

        print(
            f"Predictions file: "
            f"{prediction_path}"
        )

        print(
            f"Metrics file: "
            f"{metrics_path}"
        )

        results.append(
            {
                "candidate_id":
                    candidate_id,

                "model_name":
                    config["name"],

                "accuracy":
                    metrics["accuracy"],

                "log_loss":
                    metrics["log_loss"],

                "brier_score":
                    metrics["brier_score"],

                "precision_macro":
                    metrics["precision_macro"],

                "recall_macro":
                    metrics["recall_macro"],

                "f1_macro":
                    metrics["f1_macro"],

                "ece":
                    metrics["ece"],

                "mce":
                    metrics["mce"],
            }
        )

    print(
        "\n" + "=" * 50
    )

    print(
        "STAGE 7.6.3 RESULT"
    )

    print(
        "Candidate models trained: "
        f"{len(results)}"
    )

    print(
        "Training data: 2023 only"
    )

    print(
        "STAGE 7.6.3: PASS"
    )

    print(
        "\nSTAGE 7.6.4 RESULT"
    )

    print(
        "Candidate models evaluated: "
        f"{len(results)}"
    )

    print(
        "Validation data: 2024 only"
    )

    print(
        "STAGE 7.6.4: PASS"
    )

    print(
        "\n7.6.3 + 7.6.4: PASS"
    )


if __name__ == "__main__":
    main()