"""
FixtureIQ Stage 7.5.5
Baseline Calibration Analysis.

Analyzes the probability quality of the frozen baseline
predictions produced in Stage 7.5.3.

This module does NOT:
- retrain the model
- modify predictions
- calibrate/correct probabilities
- modify the validation dataset

It only analyzes the existing predictions.
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

CALIBRATION_REPORT_FILE = (
    MODEL_DIR
    / "baseline_calibration.json"
)

CALIBRATION_PLOT_FILE = (
    MODEL_DIR
    / "baseline_calibration.png"
)


CLASS_IDS = [0, 1, 2]

CLASS_NAMES = {
    0: "draw",
    1: "home_win",
    2: "away_win",
}


REQUIRED_COLUMNS = {
    "fixture_id",
    "actual",
    "predicted",
    "prob_home",
    "prob_draw",
    "prob_away",
}


def load_predictions():
    """
    Load the frozen Stage 7.5.3 prediction artifact.
    """

    if not PREDICTIONS_FILE.exists():
        raise FileNotFoundError(
            "Baseline prediction file not found: "
            f"{PREDICTIONS_FILE}"
        )

    predictions = pd.read_csv(
        PREDICTIONS_FILE
    )

    missing = (
        REQUIRED_COLUMNS
        -
        set(predictions.columns)
    )

    if missing:
        raise ValueError(
            "Prediction file is missing columns: "
            f"{sorted(missing)}"
        )

    if predictions.empty:
        raise ValueError(
            "Prediction dataset is empty."
        )

    return predictions


def validate_probabilities(
    predictions: pd.DataFrame,
):
    """
    Validate all probability values before calibration.
    """

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
            "Probability data contains NaN or Inf."
        )

    if (
        probabilities < 0
    ).any() or (
        probabilities > 1
    ).any():

        raise ValueError(
            "Probability values must be "
            "between 0 and 1."
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

    return probabilities


def calculate_class_calibration(
    y_true,
    probabilities,
    class_id,
    bin_count=10,
):
    """
    Calculate one-vs-rest calibration statistics
    for a single outcome class.

    Bins:
        [0.0, 0.1)
        ...
        [0.9, 1.0]

    For every populated bin:
        predicted_mean = average predicted probability
        observed_frequency = actual class frequency

    Calibration error:
        absolute(predicted_mean - observed_frequency)
    """

    y_true = np.asarray(
        y_true,
        dtype=int,
    )

    probabilities = np.asarray(
        probabilities,
        dtype=float,
    )

    class_probabilities = probabilities[
        :,
        class_id,
    ]

    bin_edges = np.linspace(
        0.0,
        1.0,
        bin_count + 1,
    )

    bins = []

    weighted_error = 0.0
    maximum_error = 0.0
    total_samples = len(
        y_true
    )

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
                    "bin":
                        index + 1,

                    "lower":
                        float(lower),

                    "upper":
                        float(upper),

                    "count":
                        0,

                    "mean_predicted":
                        None,

                    "observed_frequency":
                        None,

                    "calibration_error":
                        None,
                }
            )

            continue

        predicted_mean = float(
            class_probabilities[mask].mean()
        )

        observed_frequency = float(
            (
                y_true[mask] == class_id
            ).mean()
        )

        error = abs(
            predicted_mean
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
                "bin":
                    index + 1,

                "lower":
                    float(lower),

                "upper":
                    float(upper),

                "count":
                    count,

                "mean_predicted":
                    predicted_mean,

                "observed_frequency":
                    observed_frequency,

                "calibration_error":
                    float(error),
            }
        )

    return {
        "class_id":
            int(class_id),

        "class_name":
            CLASS_NAMES[class_id],

        "bin_count":
            int(bin_count),

        "bins":
            bins,

        "ece":
            float(weighted_error),

        "mce":
            float(maximum_error),
    }


def calculate_calibration(
    predictions: pd.DataFrame,
    bin_count=10,
):
    """
    Calculate overall and per-class calibration.
    """

    probabilities = validate_probabilities(
        predictions
    )

    y_true = (
        predictions["actual"]
        .astype(int)
        .to_numpy()
    )

    if not set(y_true).issubset(
        set(CLASS_IDS)
    ):
        raise ValueError(
            "Actual targets contain invalid classes."
        )

    per_class = {}

    eces = []
    mces = []

    for class_id in CLASS_IDS:

        result = (
            calculate_class_calibration(
                y_true,
                probabilities,
                class_id,
                bin_count,
            )
        )

        per_class[
            CLASS_NAMES[class_id]
        ] = result

        eces.append(
            result["ece"]
        )

        mces.append(
            result["mce"]
        )

    # Macro-average class calibration.
    macro_ece = float(
        np.mean(eces)
    )

    macro_mce = float(
        np.mean(mces)
    )

    return {
        "sample_count":
            int(len(predictions)),

        "bin_count":
            int(bin_count),

        "binning_method":
            "equal_width_10_bins",

        "ece_definition":
            "macro-average of one-vs-rest "
            "weighted absolute calibration errors",

        "mce_definition":
            "macro-average of one-vs-rest "
            "maximum absolute calibration error",

        "ece":
            macro_ece,

        "mce":
            macro_mce,

        "class_order": [
            "draw",
            "home_win",
            "away_win",
        ],

        "per_class":
            per_class,
    }


def save_calibration_report(
    report: dict,
):
    """
    Save calibration statistics.
    """

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with CALIBRATION_REPORT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return CALIBRATION_REPORT_FILE


def create_calibration_plot(
    report: dict,
):
    """
    Create a simple reliability plot.

    The plot contains:
        - perfect calibration line
        - observed vs predicted values
        - one curve per class
    """

    import matplotlib.pyplot as plt

    plt.figure(
        figsize=(8, 8)
    )

    plt.plot(
        [0, 1],
        [0, 1],
        linestyle="--",
        label="Perfect calibration",
    )

    for class_name in [
        "draw",
        "home_win",
        "away_win",
    ]:

        class_report = report[
            "per_class"
        ][class_name]

        x_values = []
        y_values = []

        for item in class_report[
            "bins"
        ]:

            if (
                item["count"] > 0
                and
                item["mean_predicted"] is not None
            ):

                x_values.append(
                    item["mean_predicted"]
                )

                y_values.append(
                    item["observed_frequency"]
                )

        if x_values:

            plt.plot(
                x_values,
                y_values,
                marker="o",
                label=class_name,
            )

    plt.xlabel(
        "Mean predicted probability"
    )

    plt.ylabel(
        "Observed frequency"
    )

    plt.title(
        "FixtureIQ Baseline Calibration"
    )

    plt.xlim(
        0,
        1,
    )

    plt.ylim(
        0,
        1,
    )

    plt.grid(
        True,
        alpha=0.3,
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        CALIBRATION_PLOT_FILE,
        dpi=150,
    )

    plt.close()

    return CALIBRATION_PLOT_FILE