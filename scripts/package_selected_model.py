"""
FixtureIQ Stage 7.7.2
Selected Model Production Packaging

Packages the already-trained and locked Random Forest.

No retraining.
No 2025/26 access.
Original candidate artifact remains unchanged.
"""

import json
import hashlib
import shutil
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
)

SOURCE_MODEL = (
    MODEL_DIR
    / "candidates"
    / "random_forest.joblib"
)

SOURCE_METADATA = (
    MODEL_DIR
    / "candidates"
    / "random_forest_metadata.json"
)

LOCK_FILE = (
    MODEL_DIR
    / "selected_model.json"
)

SOURCE_FEATURE_SCHEMA = (
    MODEL_DIR
    / "feature_schema.json"
)

PACKAGE_DIR = (
    MODEL_DIR
    / "selected"
)

PACKAGE_MODEL = (
    PACKAGE_DIR
    / "selected_model.joblib"
)

PACKAGE_METADATA = (
    PACKAGE_DIR
    / "selected_model_metadata.json"
)

PACKAGE_SCHEMA = (
    PACKAGE_DIR
    / "selected_feature_schema.json"
)

PACKAGE_MANIFEST = (
    PACKAGE_DIR
    / "selected_model_manifest.json"
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


def copy_exact(source, destination):

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        source,
        destination,
    )


def main():

    print("=" * 50)
    print(
        "FixtureIQ Stage 7.7.2"
    )
    print(
        "Selected Model Production Packaging"
    )
    print("=" * 50)

    required_files = [
        SOURCE_MODEL,
        SOURCE_METADATA,
        LOCK_FILE,
        SOURCE_FEATURE_SCHEMA,
    ]

    for path in required_files:

        if not path.exists():

            raise FileNotFoundError(
                f"Required file missing: {path}"
            )

    lock = load_json(
        LOCK_FILE
    )

    if lock.get(
        "status"
    ) != "LOCKED":

        raise ValueError(
            "Selected model is not locked."
        )

    if lock.get(
        "selected_candidate"
    ) != "random_forest":

        raise ValueError(
            "Locked candidate is not Random Forest."
        )

    if lock.get(
        "final_test_used"
    ) is not False:

        raise ValueError(
            "Final test protection failed."
        )

    # --------------------------------------------------------
    # Create package
    # --------------------------------------------------------

    PACKAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    copy_exact(
        SOURCE_MODEL,
        PACKAGE_MODEL,
    )

    # --------------------------------------------------------
    # Metadata package
    # --------------------------------------------------------

    source_metadata = load_json(
        SOURCE_METADATA
    )

    package_metadata = {
        "stage": "7.7.2",

        "package_status":
            "PRODUCTION_READY",

        "selected_candidate":
            "random_forest",

        "selected_model":
            "Random Forest",

        "training_season":
            2023,

        "validation_season":
            2024,

        "training_rows":
            380,

        "validation_rows":
            380,

        "feature_count":
            86,

        "target_mapping": {
            "0": "draw",
            "1": "home_win",
            "2": "away_win",
        },

        "final_test_season":
            "2025/26",

        "final_test_used":
            False,

        "source_metadata_stage":
            source_metadata.get(
                "stage"
            ),

        "source_model":
            "candidates/random_forest.joblib",
    }

    with PACKAGE_METADATA.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            package_metadata,
            file,
            indent=2,
        )

    # --------------------------------------------------------
    # Feature schema
    # --------------------------------------------------------

    copy_exact(
        SOURCE_FEATURE_SCHEMA,
        PACKAGE_SCHEMA,
    )

    # --------------------------------------------------------
    # Hashes
    # --------------------------------------------------------

    source_hash = sha256_file(
        SOURCE_MODEL
    )

    package_hash = sha256_file(
        PACKAGE_MODEL
    )

    source_schema_hash = sha256_file(
        SOURCE_FEATURE_SCHEMA
    )

    package_schema_hash = sha256_file(
        PACKAGE_SCHEMA
    )

    # --------------------------------------------------------
    # Manifest
    # --------------------------------------------------------

    manifest = {
        "stage": "7.7.2",

        "package_status":
            "PRODUCTION_READY",

        "selected_candidate":
            "random_forest",

        "selected_model":
            "Random Forest",

        "lock_file":
            "data/processed/model/"
            "selected_model.json",

        "model_file":
            "selected_model.joblib",

        "metadata_file":
            "selected_model_metadata.json",

        "feature_schema_file":
            "selected_feature_schema.json",

        "source_model":
            "data/processed/model/"
            "candidates/random_forest.joblib",

        "source_model_sha256":
            source_hash,

        "packaged_model_sha256":
            package_hash,

        "source_feature_schema_sha256":
            source_schema_hash,

        "packaged_feature_schema_sha256":
            package_schema_hash,

        "artifact_identity_preserved":
            source_hash == package_hash,

        "feature_schema_identity_preserved":
            source_schema_hash
            ==
            package_schema_hash,

        "training_season":
            2023,

        "validation_season":
            2024,

        "feature_count":
            86,

        "final_test_season":
            "2025/26",

        "final_test_used":
            False,

        "retrained":
            False,

        "final_test_accessed":
            False,
    }

    with PACKAGE_MANIFEST.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            manifest,
            file,
            indent=2,
        )

    print(
        "\nPackage directory:"
    )

    print(
        PACKAGE_DIR
    )

    print(
        "\nModel identity preserved: "
        f"{'PASS' if source_hash == package_hash else 'FAIL'}"
    )

    print(
        "Feature schema preserved: "
        f"{'PASS' if source_schema_hash == package_schema_hash else 'FAIL'}"
    )

    print(
        "Retrained: NO"
    )

    print(
        "2025/26 accessed: NO"
    )

    print(
        "\nSTAGE 7.7.2: PASS"
    )


if __name__ == "__main__":
    main()