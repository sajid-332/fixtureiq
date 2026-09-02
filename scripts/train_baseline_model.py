"""
FixtureIQ Stage 7.5.1 + 7.5.2
Model Input Contract + Baseline Training.
"""

import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR),
)


from backend.models.input import (
    load_training_data,
    load_validation_data,
    validate_model_contract,
    get_feature_columns,
)

from backend.models.baseline import (
    train_baseline,
    validate_probability_output,
    save_baseline_model,
)


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.5.1 + 7.5.2"
    )

    print(
        "Model Input Contract + Baseline Model"
    )

    print("=" * 50)

    # ========================================================
    # 7.5.1
    # ========================================================

    print(
        "\n7.5.1 MODEL INPUT CONTRACT"
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
        "Feature columns match: PASS"
    )

    print(
        "Numeric feature validation: PASS"
    )

    print(
        "Target validation: PASS"
    )

    print(
        "\nSTAGE 7.5.1: PASS"
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
    # 7.5.2
    # ========================================================

    print(
        "\n7.5.2 BASELINE MODEL"
    )

    print(
        "Model: Logistic Regression"
    )

    print(
        f"Training rows: "
        f"{len(X_train)}"
    )

    print(
        f"Training features: "
        f"{X_train.shape[1]}"
    )

    model = train_baseline(
        X_train,
        y_train,
    )

    print(
        "Model fitting: PASS"
    )

    # --------------------------------------------------------
    # Validation probabilities
    # --------------------------------------------------------

    probabilities = (
        model.predict_proba(
            X_validation
        )
    )

    validate_probability_output(
        probabilities
    )

    predictions = (
        model.predict(
            X_validation
        )
    )

    print(
        f"Validation predictions: "
        f"{len(predictions)}"
    )

    print(
        "Probability generation: PASS"
    )

    print(
        "Probability validation: PASS"
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    model_path, metadata_path = (
        save_baseline_model(
            model,
            get_feature_columns(),
            len(X_train),
        )
    )

    print(
        "\nBaseline model:"
    )

    print(
        model_path
    )

    print(
        "Baseline metadata:"
    )

    print(
        metadata_path
    )

    print(
        "\nSTAGE 7.5.2: PASS"
    )

    print(
        "\n" + "=" * 50
    )

    print(
        "7.5.1 + 7.5.2 COMPLETE"
    )

    print(
        "=" * 50
    )


if __name__ == "__main__":
    main()