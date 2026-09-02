"""
FixtureIQ Stage 7.4.3
Chronological Train / Validation Dataset Split.
"""

import json
import sys


from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR),
)


from backend.features.splitting import (
    MODEL_FEATURES_FILE,
    TRAIN_FILE,
    VALIDATION_FILE,
    SPLIT_METADATA_FILE,
    load_model_features,
    chronological_split,
    save_split,
)


TRAINING_SEASONS = [2023]

VALIDATION_SEASONS = [2024]


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.4.3"
    )

    print(
        "Chronological Train / Validation Split"
    )

    print("=" * 50)

    print(
        f"\nInput: {MODEL_FEATURES_FILE}"
    )

    print(
        f"Training seasons: "
        f"{TRAINING_SEASONS}"
    )

    print(
        f"Validation seasons: "
        f"{VALIDATION_SEASONS}"
    )

    dataframe = load_model_features()

    print(
        f"Total model records: "
        f"{len(dataframe)}"
    )

    train, validation = (
        chronological_split(
            dataframe,
            TRAINING_SEASONS,
            VALIDATION_SEASONS,
        )
    )

    # --------------------------------------------------------
    # Safety checks
    # --------------------------------------------------------

    train_ids = set(
        train["fixture_id"]
    )

    validation_ids = set(
        validation["fixture_id"]
    )

    overlap = (
        train_ids
        &
        validation_ids
    )

    if overlap:

        print(
            "\nTrain/validation overlap: FAIL"
        )

        print(
            f"Overlapping IDs: "
            f"{len(overlap)}"
        )

        sys.exit(1)

    if not train.empty and not validation.empty:

        train_max_date = train["date"].max()

        validation_min_date = (
            validation["date"].min()
        )

        chronological = (
            train_max_date
            <
            validation_min_date
        )

    else:

        chronological = False

    if not chronological:

        print(
            "\nChronological separation: FAIL"
        )

        sys.exit(1)

    save_split(
        train,
        validation,
    )

    metadata = {
        "stage": "7.4.3",
        "input": str(
            MODEL_FEATURES_FILE
        ),
        "training_seasons":
            TRAINING_SEASONS,
        "validation_seasons":
            VALIDATION_SEASONS,
        "training_records":
            len(train),
        "validation_records":
            len(validation),
        "total_records":
            len(train) + len(validation),
        "train_validation_overlap":
            len(overlap),
        "training_first_date":
            str(train["date"].min()),
        "training_last_date":
            str(train["date"].max()),
        "validation_first_date":
            str(validation["date"].min()),
        "validation_last_date":
            str(validation["date"].max()),
        "chronological":
            chronological,
        "random_shuffle":
            False,
        "final_test_season":
            "2025/26",
        "final_test_touched":
            False,
    }

    with SPLIT_METADATA_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2,
        )

    print(
        "\nSplit result"
    )

    print(
        f"Training records: "
        f"{len(train)}"
    )

    print(
        f"Validation records: "
        f"{len(validation)}"
    )

    print(
        f"Train/validation overlap: "
        f"{len(overlap)}"
    )

    print(
        f"Chronological separation: "
        f"{'PASS' if chronological else 'FAIL'}"
    )

    print(
        "\nTraining dataset:"
    )

    print(
        TRAIN_FILE
    )

    print(
        "\nValidation dataset:"
    )

    print(
        VALIDATION_FILE
    )

    print(
        "\nSplit metadata:"
    )

    print(
        SPLIT_METADATA_FILE
    )

    print(
        "\nSTAGE 7.4.3: PASS"
    )


if __name__ == "__main__":
    main()