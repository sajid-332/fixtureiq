"""
FixtureIQ Stage 7.5.1 + 7.5.2
Verification.
"""

import sys
from pathlib import Path

import numpy as np


BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR),
)


from backend.models.input import (
    load_training_data,
    load_validation_data,
    validate_model_contract,
)

from backend.models.baseline import (
    BASELINE_MODEL_FILE,
    BASELINE_METADATA_FILE,
    load_baseline_model,
    validate_probability_output,
)


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.5.1 + 7.5.2"
    )

    print(
        "Final Verification"
    )

    print("=" * 50)

    # ========================================================
    # Contract
    # ========================================================

    print(
        "\n1. MODEL INPUT CONTRACT"
    )

    contract = validate_model_contract()

    print(
        f"Training shape: "
        f"{tuple(contract['training_shape'])}"
    )

    print(
        f"Validation shape: "
        f"{tuple(contract['validation_shape'])}"
    )

    print(
        f"Feature count: "
        f"{contract['feature_count']}"
    )

    print(
        "Contract: PASS"
    )

    # ========================================================
    # Load
    # ========================================================

    X_train, y_train = (
        load_training_data()
    )

    X_validation, y_validation = (
        load_validation_data()
    )

    # ========================================================
    # Model
    # ========================================================

    print(
        "\n2. BASELINE MODEL"
    )

    model_exists = (
        BASELINE_MODEL_FILE.exists()
    )

    metadata_exists = (
        BASELINE_METADATA_FILE.exists()
    )

    print(
        f"Model artifact: "
        f"{'PASS' if model_exists else 'FAIL'}"
    )

    print(
        f"Model metadata: "
        f"{'PASS' if metadata_exists else 'FAIL'}"
    )

    if not model_exists:
        sys.exit(1)

    model = load_baseline_model()

    print(
        f"Model classes: "
        f"{list(model.classes_)}"
    )

    # ========================================================
    # Predictions
    # ========================================================

    print(
        "\n3. VALIDATION PREDICTIONS"
    )

    probabilities = (
        model.predict_proba(
            X_validation
        )
    )

    predictions = (
        model.predict(
            X_validation
        )
    )

    validate_probability_output(
        probabilities
    )

    prediction_pass = (
        len(predictions)
        ==
        len(y_validation)
    )

    print(
        f"Predictions: "
        f"{len(predictions)}"
    )

    print(
        f"Prediction count: "
        f"{'PASS' if prediction_pass else 'FAIL'}"
    )

    print(
        "Probability validity: PASS"
    )

    # ========================================================
    # Probability sums
    # ========================================================

    sums = probabilities.sum(
        axis=1
    )

    probability_sum_pass = (
        np.allclose(
            sums,
            1.0,
            atol=1e-8,
        )
    )

    print(
        f"Probability sums: "
        f"{'PASS' if probability_sum_pass else 'FAIL'}"
    )

    # ========================================================
    # Final
    # ========================================================

    overall = (
        model_exists
        and
        metadata_exists
        and
        prediction_pass
        and
        probability_sum_pass
    )

    print(
        "\n" + "=" * 50
    )

    print(
        "FINAL RESULT"
    )

    print(
        f"Stage 7.5.1: "
        f"{'PASS' if overall else 'FAIL'}"
    )

    print(
        f"Stage 7.5.2: "
        f"{'PASS' if overall else 'FAIL'}"
    )

    print(
        f"\n7.5.1 + 7.5.2: "
        f"{'PASS' if overall else 'FAIL'}"
    )

    if not overall:
        sys.exit(1)


if __name__ == "__main__":
    main()
