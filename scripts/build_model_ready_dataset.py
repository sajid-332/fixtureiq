"""
FixtureIQ Stage 7.4.5
Model-Ready Dataset Builder.
"""

import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR),
)


from backend.features.model_ready import (
    MODEL_DIR,
    X_TRAIN_FILE,
    Y_TRAIN_FILE,
    X_VALIDATION_FILE,
    Y_VALIDATION_FILE,
    FEATURE_SCHEMA_FILE,
    DATASET_METADATA_FILE,
    build_model_ready_datasets,
)


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.4.5"
    )

    print(
        "Final Model-Ready Dataset"
    )

    print("=" * 50)

    (
        X_train,
        y_train,
        X_validation,
        y_validation,
        feature_columns,
    ) = build_model_ready_datasets()

    print(
        "\nTraining"
    )

    print(
        f"Records: {len(X_train)}"
    )

    print(
        f"Features: {len(feature_columns)}"
    )

    print(
        "\nValidation"
    )

    print(
        f"Records: {len(X_validation)}"
    )

    print(
        f"Features: {len(feature_columns)}"
    )

    print(
        "\nGenerated files:"
    )

    print(
        f"X_train:       {X_TRAIN_FILE}"
    )

    print(
        f"y_train:       {Y_TRAIN_FILE}"
    )

    print(
        f"X_validation:  {X_VALIDATION_FILE}"
    )

    print(
        f"y_validation:  {Y_VALIDATION_FILE}"
    )

    print(
        f"Feature schema: {FEATURE_SCHEMA_FILE}"
    )

    print(
        f"Metadata:       {DATASET_METADATA_FILE}"
    )

    print(
        "\nModel-ready dataset: PASS"
    )

    print(
        "\nSTAGE 7.4.5: PASS"
    )


if __name__ == "__main__":
    main()