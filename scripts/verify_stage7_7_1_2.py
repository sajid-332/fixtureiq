"""
FixtureIQ Stage 7.7.1 + 7.7.2
Final Verification

Selected Model Lock + Production Packaging
"""

import json
import hashlib
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
)

LOCK_FILE = (
    MODEL_DIR
    / "selected_model.json"
)

COMPARISON_FILE = (
    MODEL_DIR
    / "candidate_comparison.json"
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

SOURCE_SCHEMA = (
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


def check(value):

    return (
        "PASS"
        if value
        else "FAIL"
    )


def main():

    print("=" * 50)
    print(
        "FixtureIQ Stage 7.7.1 + 7.7.2"
    )
    print(
        "Final Verification"
    )
    print("=" * 50)

    overall = True

    # ========================================================
    # 1. SELECTION LOCK
    # ========================================================

    print(
        "\n1. SELECTED MODEL LOCK"
    )

    lock_exists = LOCK_FILE.exists()

    print(
        f"Lock file: "
        f"{check(lock_exists)}"
    )

    lock_pass = False

    if lock_exists:

        lock = load_json(
            LOCK_FILE
        )

        lock_pass = all(
            [
                lock.get(
                    "stage"
                )
                ==
                "7.7.1",

                lock.get(
                    "selected_candidate"
                )
                ==
                "random_forest",

                lock.get(
                    "selected_model"
                )
                ==
                "Random Forest",

                lock.get(
                    "status"
                )
                ==
                "LOCKED",

                lock.get(
                    "training_season"
                )
                ==
                2023,

                lock.get(
                    "validation_season"
                )
                ==
                2024,

                lock.get(
                    "feature_count"
                )
                ==
                86,

                lock.get(
                    "final_test_season"
                )
                ==
                "2025/26",

                lock.get(
                    "final_test_used"
                )
                is False,
            ]
        )

        print(
            f"Lock integrity: "
            f"{check(lock_pass)}"
        )

    if not lock_pass:
        overall = False

    # ========================================================
    # 2. SELECTION SOURCE
    # ========================================================

    print(
        "\n2. SELECTION SOURCE"
    )

    comparison_pass = False

    if COMPARISON_FILE.exists():

        comparison = load_json(
            COMPARISON_FILE
        )

        comparison_pass = all(
            [
                comparison.get(
                    "selected_candidate"
                )
                ==
                "random_forest",

                comparison.get(
                    "selected_model"
                )
                ==
                "Random Forest",

                comparison.get(
                    "training_season"
                )
                ==
                2023,

                comparison.get(
                    "validation_season"
                )
                ==
                2024,

                comparison.get(
                    "final_test_used"
                )
                is False,
            ]
        )

    print(
        f"Stage 7.6.5 selection: "
        f"{check(comparison_pass)}"
    )

    if not comparison_pass:
        overall = False

    # ========================================================
    # 3. SOURCE MODEL
    # ========================================================

    print(
        "\n3. SOURCE MODEL"
    )

    source_model_pass = (
        SOURCE_MODEL.exists()
        and
        SOURCE_METADATA.exists()
        and
        SOURCE_SCHEMA.exists()
    )

    print(
        f"Source artifacts: "
        f"{check(source_model_pass)}"
    )

    if not source_model_pass:
        overall = False

    # ========================================================
    # 4. PACKAGE ARTIFACTS
    # ========================================================

    print(
        "\n4. PRODUCTION PACKAGE"
    )

    package_files = [
        PACKAGE_MODEL,
        PACKAGE_METADATA,
        PACKAGE_SCHEMA,
        PACKAGE_MANIFEST,
    ]

    package_pass = all(
        path.exists()
        for path in package_files
    )

    print(
        f"Package artifacts: "
        f"{check(package_pass)}"
    )

    if not package_pass:
        overall = False

    # ========================================================
    # 5. MODEL IDENTITY
    # ========================================================

    print(
        "\n5. MODEL IDENTITY"
    )

    identity_pass = False

    if (
        SOURCE_MODEL.exists()
        and
        PACKAGE_MODEL.exists()
    ):

        source_hash = sha256_file(
            SOURCE_MODEL
        )

        package_hash = sha256_file(
            PACKAGE_MODEL
        )

        identity_pass = (
            source_hash
            ==
            package_hash
        )

        print(
            f"Source/package hash match: "
            f"{check(identity_pass)}"
        )

    if not identity_pass:
        overall = False

    # ========================================================
    # 6. FEATURE SCHEMA IDENTITY
    # ========================================================

    print(
        "\n6. FEATURE SCHEMA"
    )

    schema_pass = False

    if (
        SOURCE_SCHEMA.exists()
        and
        PACKAGE_SCHEMA.exists()
    ):

        source_schema_hash = (
            sha256_file(
                SOURCE_SCHEMA
            )
        )

        package_schema_hash = (
            sha256_file(
                PACKAGE_SCHEMA
            )
        )

        schema_pass = (
            source_schema_hash
            ==
            package_schema_hash
        )

        print(
            f"Schema identity preserved: "
            f"{check(schema_pass)}"
        )

    if not schema_pass:
        overall = False

    # ========================================================
    # 7. PACKAGE METADATA
    # ========================================================

    print(
        "\n7. PACKAGE METADATA"
    )

    metadata_pass = False

    if PACKAGE_METADATA.exists():

        metadata = load_json(
            PACKAGE_METADATA
        )

        metadata_pass = all(
            [
                metadata.get(
                    "stage"
                )
                ==
                "7.7.2",

                metadata.get(
                    "package_status"
                )
                ==
                "PRODUCTION_READY",

                metadata.get(
                    "selected_candidate"
                )
                ==
                "random_forest",

                metadata.get(
                    "selected_model"
                )
                ==
                "Random Forest",

                metadata.get(
                    "training_season"
                )
                ==
                2023,

                metadata.get(
                    "validation_season"
                )
                ==
                2024,

                metadata.get(
                    "feature_count"
                )
                ==
                86,

                metadata.get(
                    "final_test_used"
                )
                is False,
            ]
        )

    print(
        f"Metadata integrity: "
        f"{check(metadata_pass)}"
    )

    if not metadata_pass:
        overall = False

    # ========================================================
    # 8. MANIFEST
    # ========================================================

    print(
        "\n8. PACKAGE MANIFEST"
    )

    manifest_pass = False

    if PACKAGE_MANIFEST.exists():

        manifest = load_json(
            PACKAGE_MANIFEST
        )

        manifest_pass = all(
            [
                manifest.get(
                    "stage"
                )
                ==
                "7.7.2",

                manifest.get(
                    "selected_candidate"
                )
                ==
                "random_forest",

                manifest.get(
                    "selected_model"
                )
                ==
                "Random Forest",

                manifest.get(
                    "artifact_identity_preserved"
                )
                is True,

                manifest.get(
                    "feature_schema_identity_preserved"
                )
                is True,

                manifest.get(
                    "retrained"
                )
                is False,

                manifest.get(
                    "final_test_accessed"
                )
                is False,

                manifest.get(
                    "final_test_used"
                )
                is False,
            ]
        )

    print(
        f"Manifest integrity: "
        f"{check(manifest_pass)}"
    )

    if not manifest_pass:
        overall = False

    # ========================================================
    # 9. FINAL TEST PROTECTION
    # ========================================================

    print(
        "\n9. FINAL TEST PROTECTION"
    )

    final_test_pass = (
        lock.get(
            "final_test_used"
        )
        is False
        if lock_exists
        else False
    )

    if comparison_pass:

        final_test_pass = (
            final_test_pass
            and
            comparison.get(
                "final_test_used"
            )
            is False
        )

    if PACKAGE_METADATA.exists():

        package_metadata = load_json(
            PACKAGE_METADATA
        )

        final_test_pass = (
            final_test_pass
            and
            package_metadata.get(
                "final_test_used"
            )
            is False
        )

    if PACKAGE_MANIFEST.exists():

        manifest = load_json(
            PACKAGE_MANIFEST
        )

        final_test_pass = (
            final_test_pass
            and
            manifest.get(
                "final_test_used"
            )
            is False
            and
            manifest.get(
                "final_test_accessed"
            )
            is False
        )

    print(
        f"2025/26 final test protected: "
        f"{check(final_test_pass)}"
    )

    if not final_test_pass:
        overall = False

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print(
        "\n" + "=" * 50
    )

    print(
        "STAGE 7.7.1 + 7.7.2 FINAL RESULT"
    )

    print("=" * 50)

    print(
        f"7.7.1 Selected Model Lock       "
        f"{check(lock_pass)}"
    )

    print(
        f"7.7.2 Production Packaging      "
        f"{check(package_pass)}"
    )

    print(
        f"Selection consistency             "
        f"{check(comparison_pass)}"
    )

    print(
        f"Model identity                    "
        f"{check(identity_pass)}"
    )

    print(
        f"Feature schema                    "
        f"{check(schema_pass)}"
    )

    print(
        f"Package metadata                  "
        f"{check(metadata_pass)}"
    )

    print(
        f"Package manifest                  "
        f"{check(manifest_pass)}"
    )

    print(
        f"Final test protection             "
        f"{check(final_test_pass)}"
    )

    print(
        "\n" + "=" * 50
    )

    if overall:

        print(
            "7.7.1: PASS"
        )

        print(
            "7.7.2: PASS"
        )

        print(
            "7.7.1 + 7.7.2: PASS"
        )

        print(
            "Selected model: Random Forest"
        )

        print(
            "Model status: LOCKED"
        )

        print(
            "2025/26 final test: PROTECTED"
        )

    else:

        print(
            "7.7.1 + 7.7.2: FAIL"
        )

        sys.exit(1)


if __name__ == "__main__":
    main()