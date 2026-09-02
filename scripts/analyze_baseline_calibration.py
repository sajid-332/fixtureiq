"""
FixtureIQ Stage 7.5.5
Baseline Calibration Analysis.
"""

import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR),
)


from backend.models.calibration import (
    load_predictions,
    calculate_calibration,
    save_calibration_report,
    create_calibration_plot,
)


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.5.5"
    )

    print(
        "Baseline Calibration Analysis"
    )

    print("=" * 50)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    predictions = load_predictions()

    print(
        f"\nPrediction records: "
        f"{len(predictions)}"
    )

    # --------------------------------------------------------
    # Calculate
    # --------------------------------------------------------

    report = calculate_calibration(
        predictions,
        bin_count=10,
    )

    print(
        "\nCalibration"
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
        "\nPer-class calibration:"
    )

    for class_name, result in (
        report["per_class"].items()
    ):

        print(
            f"{class_name}: "
            f"ECE={result['ece']:.6f}, "
            f"MCE={result['mce']:.6f}"
        )

    # --------------------------------------------------------
    # Save report
    # --------------------------------------------------------

    report_path = (
        save_calibration_report(
            report
        )
    )

    print(
        "\nCalibration report:"
    )

    print(
        report_path
    )

    # --------------------------------------------------------
    # Plot
    # --------------------------------------------------------

    plot_path = (
        create_calibration_plot(
            report
        )
    )

    print(
        "\nCalibration plot:"
    )

    print(
        plot_path
    )

    print(
        "\nSTAGE 7.5.5: PASS"
    )


if __name__ == "__main__":
    main()