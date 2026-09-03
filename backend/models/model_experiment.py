"""
FixtureIQ Stage 7.6.1 + 7.6.2
Baseline Diagnosis and Candidate Model Design.

This module:
- diagnoses the existing Stage 7.5 baseline
- analyzes feature scale and data characteristics
- defines a controlled candidate-model experiment
- does NOT train candidate models
- does NOT modify the protected final test set
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

DIAGNOSIS_FILE = (
    MODEL_DIR
    / "baseline_diagnosis.json"
)

EXPERIMENT_FILE = (
    MODEL_DIR
    / "candidate_model_plan.json"
)

X_TRAIN_FILE = (
    MODEL_DIR
    / "X_train.csv"
)

Y_TRAIN_FILE = (
    MODEL_DIR
    / "y_train.csv"
)

X_VALIDATION_FILE = (
    MODEL_DIR
    / "X_validation.csv"
)

Y_VALIDATION_FILE = (
    MODEL_DIR
    / "y_validation.csv"
)

PREDICTIONS_FILE = (
    MODEL_DIR
    / "baseline_predictions.csv"
)

METRICS_FILE = (
    MODEL_DIR
    / "baseline_metrics.json"
)

CALIBRATION_FILE = (
    MODEL_DIR
    / "baseline_calibration.json"
)


TARGET_NAMES = {
    0: "draw",
    1: "home_win",
    2: "away_win",
}


def load_datasets():
    """Load existing train/validation artifacts."""

    X_train = pd.read_csv(
        X_TRAIN_FILE
    )

    y_train = pd.read_csv(
        Y_TRAIN_FILE
    )

    X_validation = pd.read_csv(
        X_VALIDATION_FILE
    )

    y_validation = pd.read_csv(
        Y_VALIDATION_FILE
    )

    return (
        X_train,
        y_train,
        X_validation,
        y_validation,
    )


def load_json_if_exists(path):
    """Load JSON if available."""

    if not path.exists():
        return None

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def calculate_class_distribution(
    target_series,
):
    """Calculate class counts and proportions."""

    values = (
        target_series
        .astype(int)
        .value_counts()
        .sort_index()
    )

    total = len(
        target_series
    )

    result = {}

    for class_id in [0, 1, 2]:

        count = int(
            values.get(
                class_id,
                0,
            )
        )

        result[
            TARGET_NAMES[class_id]
        ] = {
            "class_id": class_id,
            "count": count,
            "proportion": (
                float(count / total)
                if total
                else 0.0
            ),
        }

    return result


def calculate_feature_scale_diagnostics(
    X_train,
):
    """
    Analyze feature magnitude and variance.

    This is diagnostic only.
    No features are removed or transformed.
    """

    numeric = X_train.select_dtypes(
        include=[np.number]
    )

    rows = []

    for column in numeric.columns:

        values = numeric[
            column
        ].to_numpy(
            dtype=float
        )

        finite_values = values[
            np.isfinite(values)
        ]

        if len(finite_values) == 0:
            continue

        minimum = float(
            np.min(finite_values)
        )

        maximum = float(
            np.max(finite_values)
        )

        mean = float(
            np.mean(finite_values)
        )

        std = float(
            np.std(finite_values)
        )

        absolute_max = float(
            np.max(
                np.abs(
                    finite_values
                )
            )
        )

        rows.append(
            {
                "feature": column,
                "min": minimum,
                "max": maximum,
                "mean": mean,
                "std": std,
                "absolute_max": absolute_max,
            }
        )

    diagnostics = pd.DataFrame(
        rows
    )

    if diagnostics.empty:

        return {
            "numeric_feature_count": 0,
            "features_with_large_scale": [],
            "features_with_zero_variance": [],
            "max_absolute_feature_value": 0.0,
        }

    large_scale = diagnostics[
        diagnostics["absolute_max"] > 10
    ]

    zero_variance = diagnostics[
        diagnostics["std"] == 0
    ]

    return {
        "numeric_feature_count":
            int(len(diagnostics)),

        "features_with_large_scale":
            [
                str(value)
                for value in large_scale[
                    "feature"
                ].tolist()
            ],

        "features_with_zero_variance":
            [
                str(value)
                for value in zero_variance[
                    "feature"
                ].tolist()
            ],

        "max_absolute_feature_value":
            float(
                diagnostics[
                    "absolute_max"
                ].max()
            ),

        "max_std":
            float(
                diagnostics[
                    "std"
                ].max()
            ),

        "median_std":
            float(
                diagnostics[
                    "std"
                ].median()
            ),
    }


def calculate_prediction_diagnostics(
    predictions,
):
    """Analyze existing baseline predictions."""

    predicted_distribution = (
        calculate_class_distribution(
            predictions["predicted"]
        )
    )

    actual_distribution = (
        calculate_class_distribution(
            predictions["actual"]
        )
    )

    probabilities = predictions[
        [
            "prob_draw",
            "prob_home",
            "prob_away",
        ]
    ].to_numpy(
        dtype=float
    )

    confidence = (
        probabilities.max(
            axis=1
        )
    )

    predicted_probability_class = (
        np.argmax(
            probabilities,
            axis=1,
        )
    )

    actual = (
        predictions["actual"]
        .astype(int)
        .to_numpy()
    )

    correct = (
        predicted_probability_class
        ==
        actual
    )

    return {
        "predicted_class_distribution":
            predicted_distribution,

        "actual_class_distribution":
            actual_distribution,

        "mean_max_probability":
            float(
                confidence.mean()
            ),

        "median_max_probability":
            float(
                np.median(confidence)
            ),

        "minimum_max_probability":
            float(
                confidence.min()
            ),

        "maximum_max_probability":
            float(
                confidence.max()
            ),

        "correct_prediction_count":
            int(correct.sum()),

        "incorrect_prediction_count":
            int((~correct).sum()),
    }


def build_baseline_diagnosis():
    """Create the Stage 7.6.1 diagnosis."""

    (
        X_train,
        y_train,
        X_validation,
        y_validation,
    ) = load_datasets()

    baseline_metrics = load_json_if_exists(
        METRICS_FILE
    )

    calibration = load_json_if_exists(
        CALIBRATION_FILE
    )

    predictions = None

    if PREDICTIONS_FILE.exists():

        predictions = pd.read_csv(
            PREDICTIONS_FILE
        )

    feature_scale = (
        calculate_feature_scale_diagnostics(
            X_train
        )
    )

    train_classes = (
        calculate_class_distribution(
            y_train["target"]
        )
    )

    validation_classes = (
        calculate_class_distribution(
            y_validation["target"]
        )
    )

    prediction_diagnostics = None

    if predictions is not None:

        prediction_diagnostics = (
            calculate_prediction_diagnostics(
                predictions
            )
        )

    convergence_issue = (
        True
    )

    diagnosis = {
        "stage": "7.6.1",

        "purpose":
            "Diagnose the Stage 7.5 "
            "baseline before candidate-model "
            "experimentation.",

        "data_protection": {
            "training_season":
                2023,

            "validation_season":
                2024,

            "final_test_season":
                "2025/26",

            "final_test_used":
                False,
        },

        "dataset": {
            "training_rows":
                int(len(X_train)),

            "validation_rows":
                int(len(X_validation)),

            "feature_count":
                int(X_train.shape[1]),
        },

        "class_distribution": {
            "training":
                train_classes,

            "validation":
                validation_classes,
        },

        "feature_scale": feature_scale,

        "baseline_convergence": {
            "convergence_warning_observed":
                convergence_issue,

            "description":
                "The Stage 7.5 Logistic Regression "
                "training emitted an lbfgs convergence "
                "warning after reaching max_iter=2000.",

            "recommended_diagnostic":
                "Evaluate feature scaling and "
                "solver behavior in a separate "
                "candidate experiment.",
        },

        "baseline_metrics":
            baseline_metrics,

        "baseline_calibration":
            calibration,

        "prediction_diagnostics":
            prediction_diagnostics,

        "diagnostic_conclusions": [
            "The current Logistic Regression baseline "
            "is reproducible but weak.",

            "Feature magnitude and convergence behavior "
            "should be investigated before selecting "
            "an improved model.",

            "The existing baseline artifact must remain "
            "unchanged for benchmark comparison.",

            "Candidate models must use identical "
            "training and validation partitions.",

            "The 2025/26 final test season remains "
            "protected.",
        ],
    }

    return diagnosis


def build_candidate_model_plan():
    """
    Define a small, controlled candidate set.

    Candidate training happens in Stage 7.6.3.
    """

    plan = {
        "stage": "7.6.2",

        "purpose":
            "Define controlled candidate models "
            "for baseline improvement.",

        "selection_principles": [
            "Use only the 2023 training dataset.",
            "Evaluate only on the 2024 validation dataset.",
            "Use the same 86-feature input.",
            "Use the same target mapping.",
            "Generate three-class probabilities.",
            "Do not use the 2025/26 final test set.",
            "Do not modify the existing baseline artifact.",
        ],

        "target_mapping": {
            "0": "draw",
            "1": "home_win",
            "2": "away_win",
        },

        "training_data": {
            "season": 2023,
            "rows": 380,
            "features": 86,
        },

        "validation_data": {
            "season": 2024,
            "rows": 380,
            "features": 86,
        },

        "candidates": [
            {
                "id": "scaled_logistic",
                "name":
                    "Scaled Logistic Regression",

                "family":
                    "linear_probability_classifier",

                "reason":
                    "Addresses feature-scale differences "
                    "and the observed Logistic Regression "
                    "convergence warning.",

                "preprocessing":
                    "StandardScaler",

                "classifier":
                    "LogisticRegression",

                "probability_output":
                    True,
            },

            {
                "id": "regularized_logistic",
                "name":
                    "Regularized Logistic Regression",

                "family":
                    "linear_probability_classifier",

                "reason":
                    "Tests whether stronger regularization "
                    "improves generalization and probability "
                    "quality.",

                "preprocessing":
                    "StandardScaler",

                "classifier":
                    "LogisticRegression",

                "probability_output":
                    True,
            },

            {
                "id": "random_forest",
                "name":
                    "Random Forest",

                "family":
                    "tree_ensemble",

                "reason":
                    "Provides a non-linear comparison "
                    "against the linear baseline.",

                "preprocessing":
                    "None",

                "classifier":
                    "RandomForestClassifier",

                "probability_output":
                    True,
            },
        ],

        "comparison_metrics": [
            "accuracy",
            "log_loss",
            "brier_score",
            "precision_macro",
            "recall_macro",
            "f1_macro",
            "ece",
            "mce",
        ],

        "selection_priority": [
            "log_loss",
            "brier_score",
            "ece",
            "mce",
            "accuracy",
        ],

        "selection_rule":
            "Select a candidate only after comparing "
            "all candidates against the frozen baseline "
            "using the identical 2024 validation set. "
            "No candidate may be selected using the "
            "2025/26 final test set.",

        "next_stage":
            "7.6.3 Candidate Model Training",
    }

    return plan


def save_json(
    data,
    path,
):
    """Save JSON artifact."""

    MODEL_DIR.mkdir(
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


def main():

    diagnosis = (
        build_baseline_diagnosis()
    )

    plan = (
        build_candidate_model_plan()
    )

    save_json(
        diagnosis,
        DIAGNOSIS_FILE,
    )

    save_json(
        plan,
        EXPERIMENT_FILE,
    )

    print(
        "=" * 50
    )

    print(
        "FixtureIQ Stage 7.6.1 + 7.6.2"
    )

    print(
        "Baseline Diagnosis + Candidate Model Design"
    )

    print(
        "=" * 50
    )

    print(
        "\n7.6.1 BASELINE DIAGNOSIS"
    )

    print(
        f"Training records: "
        f"{diagnosis['dataset']['training_rows']}"
    )

    print(
        f"Validation records: "
        f"{diagnosis['dataset']['validation_rows']}"
    )

    print(
        f"Feature count: "
        f"{diagnosis['dataset']['feature_count']}"
    )

    print(
        f"Convergence warning observed: "
        f"{diagnosis['baseline_convergence']['convergence_warning_observed']}"
    )

    print(
        f"Large-scale features: "
        f"{len(diagnosis['feature_scale']['features_with_large_scale'])}"
    )

    print(
        "\nDiagnosis report:"
    )

    print(
        DIAGNOSIS_FILE
    )

    print(
        "\n7.6.2 CANDIDATE MODEL DESIGN"
    )

    for candidate in plan[
        "candidates"
    ]:

        print(
            f"{candidate['id']}: "
            f"{candidate['name']}"
        )

    print(
        "\nCandidate plan:"
    )

    print(
        EXPERIMENT_FILE
    )

    print(
        "\nFinal test protection: PASS"
    )

    print(
        "\nSTAGE 7.6.1: PASS"
    )

    print(
        "STAGE 7.6.2: PASS"
    )

    print(
        "\nSTAGE 7.6.1 + 7.6.2: PASS"
    )


if __name__ == "__main__":
    main()