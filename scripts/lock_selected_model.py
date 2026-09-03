"""
FixtureIQ Stage 7.7.1
Selected Model Lock

Locks the model selected during Stage 7.6.5.

No retraining.
No validation changes.
No final-test access.
"""

import json
import hashlib
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
)

COMPARISON_FILE = (
    MODEL_DIR
    / "candidate_comparison.json"
)

MODEL_FILE = (
    MODEL_DIR
    / "candidates"
    / "random_forest.joblib"
)

MODEL_METADATA_FILE = (
    MODEL_DIR
    / "candidates"
    / "random_forest_metadata.json"
)

FEATURE_SCHEMA_FILE = (
    MODEL_DIR
    / "feature_schema.json"
)

OUTPUT_FILE = (
    MODEL_DIR
    / "selected_model.json"
)


def load_json(path):

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def sha256_file(path):

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as file:

        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):

            digest.update(chunk)

    return digest.hexdigest()


def main():

    print("=" * 50)
    print(
        "FixtureIQ Stage 7.7.1"
    )
    print(
        "Selected Model Lock"
    )
    print("=" * 50)

    # --------------------------------------------------------
    # Input existence
    # --------------------------------------------------------

    required_files = [
        COMPARISON_FILE,
        MODEL_FILE,
        MODEL_METADATA_FILE,
        FEATURE_SCHEMA_FILE,
    ]

    for path in required_files:

        if not path.exists():

            raise FileNotFoundError(
                f"Required file missing: {path}"
            )

    comparison = load_json(
        COMPARISON_FILE
    )

    metadata = load_json(
        MODEL_METADATA_FILE
    )

    feature_schema = load_json(
        FEATURE_SCHEMA_FILE
    )

    # --------------------------------------------------------
    # Selection validation
    # --------------------------------------------------------

    selected_candidate = comparison.get(
        "selected_candidate"
    )

    selected_model = comparison.get(
        "selected_model"
    )

    if selected_candidate != "random_forest":

        raise ValueError(
            "Stage 7.6.5 did not select Random Forest."
        )

    if selected_model != "Random Forest":

        raise ValueError(
            "Selected model name mismatch."
        )

    if comparison.get(
        "training_season"
    ) != 2023:

        raise ValueError(
            "Training season must be 2023."
        )

    if comparison.get(
        "validation_season"
    ) != 2024:

        raise ValueError(
            "Validation season must be 2024."
        )

    if comparison.get(
        "final_test_season"
    ) != "2025/26":

        raise ValueError(
            "Final test season mismatch."
        )

    if comparison.get(
        "final_test_used"
    ) is not False:

        raise ValueError(
            "Final test was marked as used."
        )

    # --------------------------------------------------------
    # Metadata validation
    # --------------------------------------------------------

    if metadata.get(
        "training_season"
    ) != 2023:

        raise ValueError(
            "Model metadata training season mismatch."
        )

    if metadata.get(
        "validation_season"
    ) != 2024:

        raise ValueError(
            "Model metadata validation season mismatch."
        )

    if metadata.get(
        "feature_count"
    ) != 86:

        raise ValueError(
            "Expected 86 model features."
        )

    if metadata.get(
        "final_test_used"
    ) is not False:

        raise ValueError(
            "Model metadata indicates final test usage."
        )

    # --------------------------------------------------------
    # Feature schema validation
    # --------------------------------------------------------

    feature_count = None

    if isinstance(
        feature_schema,
        dict,
    ):

        if isinstance(
            feature_schema.get(
                "features"
            ),
            list,
        ):

            feature_count = len(
                feature_schema[
                    "features"
                ]
            )

        elif isinstance(
            feature_schema.get(
                "feature_columns"
            ),
            list,
        ):

            feature_count = len(
                feature_schema[
                    "feature_columns"
                ]
            )

        elif isinstance(
            feature_schema.get(
                "columns"
            ),
            list,
        ):

            feature_count = len(
                feature_schema[
                    "columns"
                ]
            )

        elif isinstance(
            feature_schema.get(
                "feature_count"
            ),
            int,
        ):

            feature_count = feature_schema[
                "feature_count"
            ]

    if feature_count is not None:

        if feature_count != 86:

            raise ValueError(
                f"Feature schema contains "
                f"{feature_count} features; expected 86."
            )

    # --------------------------------------------------------
    # Artifact hash
    # --------------------------------------------------------

    model_hash = sha256_file(
        MODEL_FILE
    )

    # --------------------------------------------------------
    # Create lock record
    # --------------------------------------------------------

    lock_record = {
        "stage": "7.7.1",

        "purpose":
            "Formally lock the model selected "
            "during Stage 7.6.5.",

        "selected_candidate":
            "random_forest",

        "selected_model":
            "Random Forest",

        "status":
            "LOCKED",

        "training_season":
            2023,

        "training_rows":
            380,

        "validation_season":
            2024,

        "validation_rows":
            380,

        "feature_count":
            86,

        "target_mapping": {
            "0": "draw",
            "1": "home_win",
            "2": "away_win",
        },

        "model_source":
            "data/processed/model/candidates/"
            "random_forest.joblib",

        "model_sha256":
            model_hash,

        "selection_source":
            "data/processed/model/"
            "candidate_comparison.json",

        "final_test_season":
            "2025/26",

        "final_test_used":
            False,

        "lock_policy": [
            "Do not retrain after lock.",
            "Do not modify model weights.",
            "Do not use 2025/26 for selection.",
            "Do not tune using final-test results.",
        ],
    }

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            lock_record,
            file,
            indent=2,
        )

    print(
        "\nSelected candidate: "
        "Random Forest"
    )

    print(
        "Training season: 2023"
    )

    print(
        "Validation season: 2024"
    )

    print(
        "Feature count: 86"
    )

    print(
        "Final test used: NO"
    )

    print(
        "\nModel SHA256:"
    )

    print(
        model_hash
    )

    print(
        "\nLock file:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nSTAGE 7.7.1: PASS"
    )


if __name__ == "__main__":
    main()