"""
FixtureIQ Stage 7.5.5
Calibration Verification.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR),
)


from backend.models.calibration import (
    PREDICTIONS_FILE,
    CALIBRATION_REPORT_FILE,
    CALIBRATION_PLOT_FILE,
    CLASS_NAMES,
)


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.5.5"
    )

    print(
        "Calibration Verification"
    )

    print("=" * 50)

    # ========================================================
    # Prediction artifact
    # ========================================================

    print(
        "\n1. PREDICTION ARTIFACT"
    )

    prediction_exists = (
        PREDICTIONS_FILE.exists()
    )

    print(
        f"Prediction file: "
        f"{'PASS' if prediction_exists else 'FAIL'}"
    )

    if not prediction_exists:
        sys.exit(1)

    predictions = pd.read_csv(
        PREDICTIONS_FILE
    )

    count_pass = (
        len(predictions) == 380
    )

    print(
        f"Prediction count: "
        f"{len(predictions)}"
    )

    print(
        f"Expected 380: "
        f"{'PASS' if count_pass else 'FAIL'}"
    )

    # ========================================================
    # Probability integrity
    # ========================================================

    print(
        "\n2. PROBABILITY INTEGRITY"
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

    finite_pass = np.isfinite(
        probabilities
    ).all()

    range_pass = (
        (probabilities >= 0).all()
        and
        (probabilities <= 1).all()
    )

    sums_pass = np.allclose(
        probabilities.sum(axis=1),
        1.0,
        atol=1e-8,
    )

    print(
        f"Finite: "
        f"{'PASS' if finite_pass else 'FAIL'}"
    )

    print(
        f"Range: "
        f"{'PASS' if range_pass else 'FAIL'}"
    )

    print(
        f"Probability sums: "
        f"{'PASS' if sums_pass else 'FAIL'}"
    )

    probability_pass = (
        finite_pass
        and
        range_pass
        and
        sums_pass
    )

    # ========================================================
    # Calibration report
    # ========================================================

    print(
        "\n3. CALIBRATION REPORT"
    )

    report_exists = (
        CALIBRATION_REPORT_FILE.exists()
    )

    print(
        f"Report exists: "
        f"{'PASS' if report_exists else 'FAIL'}"
    )

    if not report_exists:
        sys.exit(1)

    with CALIBRATION_REPORT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        report = json.load(file)

    required_report_fields = {
        "sample_count",
        "bin_count",
        "binning_method",
        "ece_definition",
        "mce_definition",
        "ece",
        "mce",
        "class_order",
        "per_class",
    }

    report_schema_pass = (
        required_report_fields
        <=
        set(report.keys())
    )

    print(
        f"Report schema: "
        f"{'PASS' if report_schema_pass else 'FAIL'}"
    )

    sample_count_pass = (
        report["sample_count"] == 380
    )

    print(
        f"Report sample count: "
        f"{'PASS' if sample_count_pass else 'FAIL'}"
    )

    # ========================================================
    # ECE / MCE
    # ========================================================

    print(
        "\n4. CALIBRATION METRICS"
    )

    metric_values = [
        report["ece"],
        report["mce"],
    ]

    metrics_finite = np.isfinite(
        metric_values
    ).all()

    metrics_range = (
        all(
            0 <= value <= 1
            for value in metric_values
        )
    )

    print(
        f"ECE: "
        f"{report['ece']:.6f}"
    )

    print(
        f"MCE: "
        f"{report['mce']:.6f}"
    )

    print(
        f"Metric validity: "
        f"{'PASS' if (metrics_finite and metrics_range) else 'FAIL'}"
    )

    metric_pass = (
        metrics_finite
        and
        metrics_range
    )

    # ========================================================
    # Per-class
    # ========================================================

    print(
        "\n5. PER-CLASS CALIBRATION"
    )

    expected_classes = {
        "draw",
        "home_win",
        "away_win",
    }

    actual_classes = set(
        report["per_class"].keys()
    )

    class_schema_pass = (
        actual_classes
        ==
        expected_classes
    )

    print(
        f"All three classes: "
        f"{'PASS' if class_schema_pass else 'FAIL'}"
    )

    bins_pass = True

    for class_name in (
        expected_classes
    ):

        class_report = (
            report["per_class"]
            [class_name]
        )

        if class_report[
            "bin_count"
        ] != 10:

            bins_pass = False

        if len(
            class_report["bins"]
        ) != 10:

            bins_pass = False

        if not (
            0 <= class_report["ece"] <= 1
        ):

            bins_pass = False

        if not (
            0 <= class_report["mce"] <= 1
        ):

            bins_pass = False

    print(
        f"10 bins per class: "
        f"{'PASS' if bins_pass else 'FAIL'}"
    )

    per_class_pass = (
        class_schema_pass
        and
        bins_pass
    )

    # ========================================================
    # Plot
    # ========================================================

    print(
        "\n6. CALIBRATION PLOT"
    )

    plot_exists = (
        CALIBRATION_PLOT_FILE.exists()
    )

    print(
        f"Plot exists: "
        f"{'PASS' if plot_exists else 'FAIL'}"
    )

    # ========================================================
    # Final
    # ========================================================

    overall = all(
        [
            prediction_exists,
            count_pass,
            probability_pass,
            report_exists,
            report_schema_pass,
            sample_count_pass,
            metric_pass,
            per_class_pass,
            plot_exists,
        ]
    )

    print(
        "\n" + "=" * 50
    )

    print(
        "FINAL RESULT"
    )

    print(
        f"Stage 7.5.5: "
        f"{'PASS' if overall else 'FAIL'}"
    )

    if not overall:
        sys.exit(1)


if __name__ == "__main__":
    main()