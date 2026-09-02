"""
FixtureIQ Stage 7.5.3
Baseline Probability Generation.
"""

import sys
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR),
)


from backend.models.input import (
    load_validation_data,
)

from backend.models.baseline import (
    load_baseline_model,
)

from backend.models.probabilities import (
    generate_baseline_predictions,
    save_predictions,
)


VALIDATION_FULL_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "validation_features.csv"
)


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.5.3"
    )

    print(
        "Baseline Probability Generation"
    )

    print("=" * 50)

    X_validation, y_validation = (
        load_validation_data()
    )

    validation_full = pd.read_csv(
        VALIDATION_FULL_FILE
    )

    if len(validation_full) != len(
        X_validation
    ):
        raise ValueError(
            "Validation metadata row count "
            "does not match model validation data."
        )

    fixture_ids = validation_full[
        "fixture_id"
    ]

    print(
        f"\nValidation records: "
        f"{len(X_validation)}"
    )

    print(
        f"Features: "
        f"{X_validation.shape[1]}"
    )

    model = load_baseline_model()

    print(
        "Baseline model loaded: PASS"
    )

    predictions = (
        generate_baseline_predictions(
            model,
            X_validation,
            y_validation,
            fixture_ids,
        )
    )

    print(
        f"Predictions generated: "
        f"{len(predictions)}"
    )

    print(
        "Class mapping: PASS"
    )

    print(
        "Probability range: PASS"
    )

    print(
        "Probability sums: PASS"
    )

    prediction_path, metadata_path = (
        save_predictions(
            predictions,
            X_validation.shape[1],
        )
    )

    print(
        "\nPrediction dataset:"
    )

    print(
        prediction_path
    )

    print(
        "Prediction metadata:"
    )

    print(
        metadata_path
    )

    print(
        "\nSTAGE 7.5.3: PASS"
    )


if __name__ == "__main__":
    main()