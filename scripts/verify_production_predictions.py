"""
FixtureIQ Stage 7.8.4
Independent Production Prediction Validation.

This verifier DOES NOT:
- load the model with joblib
- call predict()
- call predict_proba()
- retrain
- tune
- select a model

It independently validates the artifacts produced by
Stages 7.8.1, 7.8.2 and 7.8.3.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Project root
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)


# ============================================================
# Paths
# ============================================================

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
)

PRODUCTION_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "production"
)


MODEL_FILE = (
    MODEL_DIR
    / "selected"
    / "selected_model.joblib"
)

MODEL_LIFECYCLE_FILE = (
    MODEL_DIR
    / "selected_model.json"
)

MODEL_MANIFEST_FILE = (
    MODEL_DIR
    / "selected"
    / "selected_model_manifest.json"
)

CONTRACT_FILE = (
    MODEL_DIR
    / "production_inference_contract.json"
)


FEATURE_FILE = (
    PRODUCTION_DIR
    / "production_features.csv"
)

FEATURE_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_feature_report.json"
)

FIXTURE_METADATA_FILE = (
    PRODUCTION_DIR
    / "production_fixture_metadata.csv"
)

UPCOMING_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
)


PREDICTION_FILE = (
    PRODUCTION_DIR
    / "production_predictions.csv"
)

PREDICTION_METADATA_FILE = (
    PRODUCTION_DIR
    / "production_prediction_metadata.json"
)

PREDICTION_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_prediction_report.json"
)

VERIFICATION_FILE = (
    PRODUCTION_DIR
    / "production_prediction_verification.json"
)


FINAL_TEST_LOCK_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "final_test"
    / "final_test_used.lock"
)


# ============================================================
# Constants
# ============================================================

EXPECTED_FEATURE_COUNT = 86

EXPECTED_TARGETS = {
    0,
    1,
    2,
}

LABEL_MAPPING = {
    0: "Draw",
    1: "Home Win",
    2: "Away Win",
}

PROBABILITY_COLUMNS = [
    "prob_draw",
    "prob_home_win",
    "prob_away_win",
]


# ============================================================
# Helpers
# ============================================================

def sha256_file(
    path: Path,
) -> str:

    if not path.exists():

        raise FileNotFoundError(
            f"File not found: {path}"
        )

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as file:

        for chunk in iter(
            lambda: file.read(
                1024 * 1024
            ),
            b"",
        ):

            digest.update(
                chunk
            )

    return digest.hexdigest()


def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise FileNotFoundError(
            f"Required JSON missing: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        payload = json.load(
            file
        )

    if not isinstance(
        payload,
        dict,
    ):

        raise RuntimeError(
            f"Expected JSON object: {path}"
        )

    return payload


def collect_declared_sha256(
    payload,
) -> set[str]:
    """
    Independently discover SHA256 values in lifecycle
    and manifest metadata.
    """

    hashes = set()

    sha_pattern = re.compile(
        r"^[0-9a-fA-F]{64}$"
    )

    def walk(
        value,
        key_path="",
    ):

        if isinstance(
            value,
            dict,
        ):

            for key, child in value.items():

                next_path = (
                    f"{key_path}.{key}"
                    if key_path
                    else str(key)
                )

                walk(
                    child,
                    next_path,
                )

        elif isinstance(
            value,
            list,
        ):

            for child in value:

                walk(
                    child,
                    key_path,
                )

        elif isinstance(
            value,
            str,
        ):

            if (
                "sha256"
                in key_path.lower()
                and
                sha_pattern.fullmatch(
                    value.strip()
                )
            ):

                hashes.add(
                    value.strip().lower()
                )

    walk(
        payload
    )

    return hashes


def check(
    label: str,
    condition: bool,
    failures: list[str],
) -> bool:

    passed = bool(
        condition
    )

    print(
        f"{label}: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    if not passed:

        failures.append(
            label
        )

    return passed


def normalize_fixture_ids(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    result = dataframe.copy()

    if "fixture_id" not in result.columns:

        raise RuntimeError(
            "fixture_id column is missing."
        )

    result[
        "fixture_id"
    ] = pd.to_numeric(
        result[
            "fixture_id"
        ],
        errors="raise",
    ).astype(
        "int64"
    )

    return result


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 64)

    print(
        "FixtureIQ Stage 7.8.4"
    )

    print(
        "Independent Production Prediction Validation"
    )

    print("=" * 64)

    failures = []
    warnings = []

    verified_at = datetime.now(
        timezone.utc
    ).isoformat()

    # ========================================================
    # 1. Required artifacts
    # ========================================================

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    required_files = [
        MODEL_FILE,
        MODEL_LIFECYCLE_FILE,
        MODEL_MANIFEST_FILE,
        CONTRACT_FILE,
        FEATURE_FILE,
        FEATURE_REPORT_FILE,
        FIXTURE_METADATA_FILE,
        UPCOMING_FILE,
        PREDICTION_FILE,
        PREDICTION_METADATA_FILE,
        PREDICTION_REPORT_FILE,
    ]

    for path in required_files:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        print(
            "\nCannot continue because required "
            "artifacts are missing."
        )

        sys.exit(1)

    # ========================================================
    # 2. Locked production contract
    # ========================================================

    print(
        "\n2. LOCKED PRODUCTION CONTRACT"
    )

    contract = load_json(
        CONTRACT_FILE
    )

    check(
        "Contract stage 7.8.1",
        contract.get(
            "stage"
        ) == "7.8.1",
        failures,
    )

    check(
        "Contract status LOCKED_CONTRACT",
        contract.get(
            "status"
        ) == "LOCKED_CONTRACT",
        failures,
    )

    model_contract = contract.get(
        "model",
        {},
    )

    check(
        "Model ID random_forest",
        model_contract.get(
            "candidate_id"
        ) == "random_forest",
        failures,
    )

    check(
        "Model status LOCKED",
        model_contract.get(
            "status"
        ) == "LOCKED",
        failures,
    )

    contract_features = contract.get(
        "feature_columns",
        [],
    )

    check(
        "Contract feature count = 86",
        len(
            contract_features
        ) == EXPECTED_FEATURE_COUNT,
        failures,
    )

    expected_contract_mapping = {
        "0": "draw",
        "1": "home_win",
        "2": "away_win",
    }

    check(
        "Target contract",
        contract.get(
            "target_mapping"
        ) == expected_contract_mapping,
        failures,
    )

    final_test_contract = contract.get(
        "final_test",
        {},
    )

    check(
        "Final test marked CONSUMED",
        final_test_contract.get(
            "status"
        ) == "CONSUMED",
        failures,
    )

    check(
        "Final-test training prohibited",
        final_test_contract.get(
            "must_not_be_used_for_training"
        ) is True,
        failures,
    )

    check(
        "Final-test selection prohibited",
        final_test_contract.get(
            "must_not_be_used_for_selection"
        ) is True,
        failures,
    )

    # ========================================================
    # 3. Model lifecycle and hash
    # ========================================================

    print(
        "\n3. MODEL INTEGRITY"
    )

    lifecycle = load_json(
        MODEL_LIFECYCLE_FILE
    )

    manifest = load_json(
        MODEL_MANIFEST_FILE
    )

    actual_model_hash = sha256_file(
        MODEL_FILE
    ).lower()

    declared_hashes = set()

    declared_hashes.update(
        collect_declared_sha256(
            lifecycle
        )
    )

    declared_hashes.update(
        collect_declared_sha256(
            manifest
        )
    )

    check(
        "Declared model SHA256 exists",
        len(
            declared_hashes
        ) > 0,
        failures,
    )

    check(
        "Locked model SHA256 MATCH",
        actual_model_hash
        in declared_hashes,
        failures,
    )

    check(
        "Lifecycle final_test_used = true",
        lifecycle.get(
            "final_test_used"
        ) is True,
        failures,
    )

    check(
        "Lifecycle final_test_evaluated = true",
        lifecycle.get(
            "final_test_evaluated"
        ) is True,
        failures,
    )

    print(
        f"Model SHA256: "
        f"{actual_model_hash}"
    )

    # ========================================================
    # 4. Stage 7.8.2 provenance
    # ========================================================

    print(
        "\n4. FEATURE PROVENANCE"
    )

    feature_report = load_json(
        FEATURE_REPORT_FILE
    )

    check(
        "Feature report stage 7.8.2",
        feature_report.get(
            "stage"
        ) == "7.8.2",
        failures,
    )

    check(
        "Feature report status PASS",
        feature_report.get(
            "status"
        ) == "PASS",
        failures,
    )

    check(
        "Feature model retrained = false",
        feature_report.get(
            "model_retrained"
        ) is False,
        failures,
    )

    check(
        "Feature model selected = false",
        feature_report.get(
            "model_selected"
        ) is False,
        failures,
    )

    check(
        "Feature hyperparameter tuned = false",
        feature_report.get(
            "hyperparameter_tuned"
        ) is False,
        failures,
    )

    check(
        "Feature final-test artifacts used = false",
        feature_report.get(
            "final_test_evaluation_artifacts_used"
        ) is False,
        failures,
    )

    actual_feature_hash = sha256_file(
        FEATURE_FILE
    ).lower()

    declared_feature_hash = str(
        feature_report.get(
            "production_feature_sha256",
            "",
        )
    ).lower()

    check(
        "Feature SHA256 MATCH",
        actual_feature_hash
        ==
        declared_feature_hash,
        failures,
    )

    # ========================================================
    # 5. Stage 7.8.3 metadata
    # ========================================================

    print(
        "\n5. PREDICTION PROVENANCE"
    )

    prediction_metadata = load_json(
        PREDICTION_METADATA_FILE
    )

    prediction_report = load_json(
        PREDICTION_REPORT_FILE
    )

    check(
        "Prediction metadata stage 7.8.3",
        prediction_metadata.get(
            "stage"
        ) == "7.8.3",
        failures,
    )

    check(
        "Prediction metadata status PASS",
        prediction_metadata.get(
            "status"
        ) == "PASS",
        failures,
    )

    check(
        "Prediction report stage 7.8.3",
        prediction_report.get(
            "stage"
        ) == "7.8.3",
        failures,
    )

    check(
        "Prediction report status PASS",
        prediction_report.get(
            "status"
        ) == "PASS",
        failures,
    )

    check(
        "Prediction model ID",
        prediction_metadata.get(
            "model_id"
        ) == "random_forest",
        failures,
    )

    check(
        "Prediction model status LOCKED",
        prediction_metadata.get(
            "model_status"
        ) == "LOCKED",
        failures,
    )

    check(
        "Prediction model hash MATCH",
        str(
            prediction_metadata.get(
                "model_sha256",
                "",
            )
        ).lower()
        ==
        actual_model_hash,
        failures,
    )

    check(
        "Prediction feature count = 86",
        prediction_metadata.get(
            "feature_count"
        ) == EXPECTED_FEATURE_COUNT,
        failures,
    )

    check(
        "Prediction model retrained = false",
        prediction_metadata.get(
            "model_retrained"
        ) is False,
        failures,
    )

    check(
        "Prediction model reselected = false",
        prediction_metadata.get(
            "model_reselected"
        ) is False,
        failures,
    )

    check(
        "Prediction tuning = false",
        prediction_metadata.get(
            "hyperparameter_tuned"
        ) is False,
        failures,
    )

    check(
        "Prediction final-test artifacts used = false",
        prediction_metadata.get(
            "final_test_evaluation_artifacts_used"
        ) is False,
        failures,
    )

    # ========================================================
    # 6. Artifact hash integrity
    # ========================================================

    print(
        "\n6. ARTIFACT HASH INTEGRITY"
    )

    actual_prediction_hash = sha256_file(
        PREDICTION_FILE
    ).lower()

    metadata_prediction_hash = str(
        prediction_metadata.get(
            "prediction_sha256",
            "",
        )
    ).lower()

    report_prediction_hash = str(
        prediction_report.get(
            "prediction_sha256",
            "",
        )
    ).lower()

    check(
        "Prediction CSV -> metadata SHA256",
        actual_prediction_hash
        ==
        metadata_prediction_hash,
        failures,
    )

    check(
        "Prediction CSV -> report SHA256",
        actual_prediction_hash
        ==
        report_prediction_hash,
        failures,
    )

    metadata_feature_hash = str(
        prediction_metadata.get(
            "production_feature_sha256",
            "",
        )
    ).lower()

    check(
        "Prediction metadata -> feature SHA256",
        metadata_feature_hash
        ==
        actual_feature_hash,
        failures,
    )

    actual_upcoming_hash = sha256_file(
        UPCOMING_FILE
    ).lower()

    metadata_upcoming_hash = str(
        prediction_metadata.get(
            "upcoming_fixture_sha256",
            "",
        )
    ).lower()

    check(
        "Prediction metadata -> upcoming SHA256",
        actual_upcoming_hash
        ==
        metadata_upcoming_hash,
        failures,
    )

    # ========================================================
    # 7. Load tabular artifacts
    # ========================================================

    print(
        "\n7. TABULAR ARTIFACTS"
    )

    features = pd.read_csv(
        FEATURE_FILE
    )

    metadata = pd.read_csv(
        FIXTURE_METADATA_FILE
    )

    upcoming = pd.read_csv(
        UPCOMING_FILE
    )

    predictions = pd.read_csv(
        PREDICTION_FILE
    )

    features = features.copy()

    metadata = normalize_fixture_ids(
        metadata
    )

    upcoming = normalize_fixture_ids(
        upcoming
    )

    predictions = normalize_fixture_ids(
        predictions
    )

    record_count = len(
        predictions
    )

    check(
        "Prediction records > 0",
        record_count > 0,
        failures,
    )

    check(
        "Feature rows = prediction rows",
        len(
            features
        ) == record_count,
        failures,
    )

    check(
        "Fixture metadata rows = prediction rows",
        len(
            metadata
        ) == record_count,
        failures,
    )

    check(
        "Upcoming rows = prediction rows",
        len(
            upcoming
        ) == record_count,
        failures,
    )

    check(
        "Prediction count metadata",
        prediction_metadata.get(
            "prediction_count"
        ) == record_count,
        failures,
    )

    check(
        "Prediction count report",
        prediction_report.get(
            "prediction_count"
        ) == record_count,
        failures,
    )

    print(
        f"Prediction records: "
        f"{record_count}"
    )

    # ========================================================
    # 8. Feature schema
    # ========================================================

    print(
        "\n8. FEATURE SCHEMA"
    )

    check(
        "Feature matrix has 86 columns",
        features.shape[
            1
        ] == EXPECTED_FEATURE_COUNT,
        failures,
    )

    check(
        "Feature schema matches contract",
        list(
            features.columns
        )
        ==
        list(
            contract_features
        ),
        failures,
    )

    forbidden_features = {
        "fixture_id",
        "target",
        "target_label",
        "home_goals",
        "away_goals",
        "FTHG",
        "FTAG",
        "FTR",
    }

    check(
        "No target/result leakage",
        len(
            forbidden_features
            &
            set(
                features.columns
            )
        ) == 0,
        failures,
    )

    try:

        feature_values = (
            features.to_numpy(
                dtype=float
            )
        )

        numeric_features_ok = (
            np.isfinite(
                feature_values
            ).all()
        )

    except Exception:

        numeric_features_ok = False

    check(
        "Feature numeric integrity",
        numeric_features_ok,
        failures,
    )

    # ========================================================
    # 9. Fixture alignment
    # ========================================================

    print(
        "\n9. FIXTURE ALIGNMENT"
    )

    check(
        "Prediction fixture IDs unique",
        predictions[
            "fixture_id"
        ].is_unique,
        failures,
    )

    check(
        "Metadata fixture IDs unique",
        metadata[
            "fixture_id"
        ].is_unique,
        failures,
    )

    check(
        "Upcoming fixture IDs unique",
        upcoming[
            "fixture_id"
        ].is_unique,
        failures,
    )

    prediction_ids = predictions[
        "fixture_id"
    ].tolist()

    metadata_ids = metadata[
        "fixture_id"
    ].tolist()

    upcoming_ids = upcoming[
        "fixture_id"
    ].tolist()

    check(
        "Prediction/metadata fixture order",
        prediction_ids
        ==
        metadata_ids,
        failures,
    )

    check(
        "Prediction/upcoming fixture set",
        set(
            prediction_ids
        )
        ==
        set(
            upcoming_ids
        ),
        failures,
    )

    upcoming_aligned = (
        upcoming
        .set_index(
            "fixture_id"
        )
        .loc[
            prediction_ids
        ]
        .reset_index()
    )

    identity_fields = [
        "home_team_id",
        "home_team_name",
        "away_team_id",
        "away_team_name",
    ]

    for field in identity_fields:

        field_ok = (
            field
            in predictions.columns
            and
            field
            in metadata.columns
            and
            field
            in upcoming_aligned.columns
        )

        if field_ok:

            prediction_values = (
                predictions[
                    field
                ]
                .astype(str)
                .tolist()
            )

            metadata_values = (
                metadata[
                    field
                ]
                .astype(str)
                .tolist()
            )

            upcoming_values = (
                upcoming_aligned[
                    field
                ]
                .astype(str)
                .tolist()
            )

            field_ok = (
                prediction_values
                ==
                metadata_values
                ==
                upcoming_values
            )

        check(
            f"{field} alignment",
            field_ok,
            failures,
        )

    # ========================================================
    # 10. Prediction schema
    # ========================================================

    print(
        "\n10. PREDICTION SCHEMA"
    )

    required_prediction_columns = {
        "fixture_id",
        "date",
        "home_team_id",
        "home_team_name",
        "away_team_id",
        "away_team_name",
        "predicted_target",
        "predicted_label",
        "prob_draw",
        "prob_home_win",
        "prob_away_win",
        "confidence",
        "model_id",
        "model_sha256",
        "feature_count",
    }

    check(
        "Required prediction columns",
        required_prediction_columns.issubset(
            set(
                predictions.columns
            )
        ),
        failures,
    )

    # ========================================================
    # 11. Probability integrity
    # ========================================================

    print(
        "\n11. PROBABILITY INTEGRITY"
    )

    probability_schema_ok = all(
        column
        in predictions.columns
        for column
        in PROBABILITY_COLUMNS
    )

    check(
        "Probability columns present",
        probability_schema_ok,
        failures,
    )

    probability_integrity = False
    sum_integrity = False
    confidence_integrity = False
    target_integrity = False
    argmax_integrity = False
    label_integrity = False

    if probability_schema_ok:

        try:

            probability_values = (
                predictions[
                    PROBABILITY_COLUMNS
                ].to_numpy(
                    dtype=float
                )
            )

            probability_integrity = (
                np.isfinite(
                    probability_values
                ).all()
                and
                (
                    probability_values
                    >= 0.0
                ).all()
                and
                (
                    probability_values
                    <= 1.0
                ).all()
            )

            row_sums = (
                probability_values.sum(
                    axis=1
                )
            )

            sum_integrity = (
                np.allclose(
                    row_sums,
                    1.0,
                    atol=1e-8,
                    rtol=0.0,
                )
            )

            expected_target = np.argmax(
                probability_values,
                axis=1,
            ).astype(
                int
            )

            predicted_target = (
                pd.to_numeric(
                    predictions[
                        "predicted_target"
                    ],
                    errors="raise",
                )
                .astype(int)
                .to_numpy()
            )

            target_integrity = (
                set(
                    predicted_target.tolist()
                )
                .issubset(
                    EXPECTED_TARGETS
                )
            )

            argmax_integrity = (
                np.array_equal(
                    expected_target,
                    predicted_target,
                )
            )

            expected_confidence = np.max(
                probability_values,
                axis=1,
            )

            actual_confidence = (
                pd.to_numeric(
                    predictions[
                        "confidence"
                    ],
                    errors="raise",
                )
                .to_numpy(
                    dtype=float
                )
            )

            confidence_integrity = (
                np.allclose(
                    expected_confidence,
                    actual_confidence,
                    atol=1e-12,
                    rtol=0.0,
                )
            )

            expected_labels = [
                LABEL_MAPPING[
                    int(target)
                ]
                for target
                in predicted_target
            ]

            actual_labels = (
                predictions[
                    "predicted_label"
                ]
                .astype(str)
                .tolist()
            )

            label_integrity = (
                expected_labels
                ==
                actual_labels
            )

        except Exception:

            pass

    check(
        "Probability range [0,1]",
        probability_integrity,
        failures,
    )

    check(
        "Probability sums = 1",
        sum_integrity,
        failures,
    )

    check(
        "Predicted targets valid",
        target_integrity,
        failures,
    )

    check(
        "Prediction = argmax probability",
        argmax_integrity,
        failures,
    )

    check(
        "Prediction label mapping",
        label_integrity,
        failures,
    )

    check(
        "Confidence = max probability",
        confidence_integrity,
        failures,
    )

    # ========================================================
    # 12. Model provenance inside prediction rows
    # ========================================================

    print(
        "\n12. ROW-LEVEL MODEL PROVENANCE"
    )

    model_id_ok = (
        "model_id"
        in predictions.columns
        and
        set(
            predictions[
                "model_id"
            ].astype(str)
        )
        ==
        {
            "random_forest"
        }
    )

    check(
        "Every row model_id=random_forest",
        model_id_ok,
        failures,
    )

    row_hash_ok = (
        "model_sha256"
        in predictions.columns
        and
        set(
            predictions[
                "model_sha256"
            ]
            .astype(str)
            .str.lower()
        )
        ==
        {
            actual_model_hash
        }
    )

    check(
        "Every row model SHA256 MATCH",
        row_hash_ok,
        failures,
    )

    feature_count_ok = False

    if "feature_count" in predictions.columns:

        try:

            feature_counts = (
                pd.to_numeric(
                    predictions[
                        "feature_count"
                    ],
                    errors="raise",
                )
                .astype(int)
            )

            feature_count_ok = (
                set(
                    feature_counts.tolist()
                )
                ==
                {
                    EXPECTED_FEATURE_COUNT
                }
            )

        except Exception:

            feature_count_ok = False

    check(
        "Every row feature_count=86",
        feature_count_ok,
        failures,
    )

    # ========================================================
    # 13. Prediction freshness
    # ========================================================

    print(
        "\n13. PREDICTION SNAPSHOT FRESHNESS"
    )

    prediction_dates = pd.to_datetime(
        predictions[
            "date"
        ],
        errors="coerce",
        utc=True,
    )

    valid_dates = (
        not prediction_dates.isna().any()
    )

    check(
        "Prediction dates valid",
        valid_dates,
        failures,
    )

    now = pd.Timestamp.now(
        tz="UTC"
    )

    future_only = (
        valid_dates
        and
        (
            prediction_dates
            > now
        ).all()
    )

    check(
        "All prediction fixtures still upcoming",
        future_only,
        failures,
    )

    if not future_only:

        warnings.append(
            "Prediction snapshot contains a fixture "
            "whose kickoff has passed. Refresh Stages "
            "7.8.2 and 7.8.3 before serving predictions."
        )

    # ========================================================
    # 14. Protection checks
    # ========================================================

    print(
        "\n14. PROTECTION"
    )

    metadata_protection = (
        prediction_metadata.get(
            "model_retrained"
        ) is False
        and
        prediction_metadata.get(
            "model_reselected"
        ) is False
        and
        prediction_metadata.get(
            "hyperparameter_tuned"
        ) is False
        and
        prediction_metadata.get(
            "final_test_evaluation_artifacts_used"
        ) is False
    )

    report_protection = (
        prediction_report.get(
            "model_retrained"
        ) is False
        and
        prediction_report.get(
            "model_reselected"
        ) is False
        and
        prediction_report.get(
            "hyperparameter_tuned"
        ) is False
        and
        prediction_report.get(
            "final_test_evaluation_artifacts_used"
        ) is False
    )

    check(
        "Prediction metadata protection",
        metadata_protection,
        failures,
    )

    check(
        "Prediction report protection",
        report_protection,
        failures,
    )

    check(
        "Final-test consumption lock exists",
        FINAL_TEST_LOCK_FILE.exists(),
        failures,
    )

    # ========================================================
    # 15. Distribution diagnostics
    # ========================================================

    print(
        "\n15. PREDICTION DISTRIBUTION DIAGNOSTICS"
    )

    target_counts = {
        0: 0,
        1: 0,
        2: 0,
    }

    target_shares = {
        0: 0.0,
        1: 0.0,
        2: 0.0,
    }

    if (
        "predicted_target"
        in predictions.columns
    ):

        numeric_targets = (
            pd.to_numeric(
                predictions[
                    "predicted_target"
                ],
                errors="coerce",
            )
        )

        counts = (
            numeric_targets
            .value_counts()
            .to_dict()
        )

        for target in target_counts:

            target_counts[
                target
            ] = int(
                counts.get(
                    target,
                    0,
                )
            )

            if record_count > 0:

                target_shares[
                    target
                ] = (
                    target_counts[
                        target
                    ]
                    /
                    record_count
                )

    print(
        f"Draw: "
        f"{target_counts[0]} "
        f"({target_shares[0] * 100:.2f}%)"
    )

    print(
        f"Home Win: "
        f"{target_counts[1]} "
        f"({target_shares[1] * 100:.2f}%)"
    )

    print(
        f"Away Win: "
        f"{target_counts[2]} "
        f"({target_shares[2] * 100:.2f}%)"
    )

    if (
        record_count > 0
        and
        target_shares[
            0
        ] < 0.01
    ):

        warnings.append(
            "Draw predictions represent less than 1% "
            "of the current production snapshot. "
            "This is a model-behavior diagnostic, "
            "not a pipeline-integrity failure."
        )

        print(
            "Draw-class diagnostic: WARNING"
        )

    else:

        print(
            "Draw-class diagnostic: OK"
        )

    average_confidence = None
    minimum_confidence = None
    maximum_confidence = None

    try:

        confidence = pd.to_numeric(
            predictions[
                "confidence"
            ],
            errors="raise",
        )

        average_confidence = float(
            confidence.mean()
        )

        minimum_confidence = float(
            confidence.min()
        )

        maximum_confidence = float(
            confidence.max()
        )

        print(
            f"Average confidence: "
            f"{average_confidence:.6f}"
        )

        print(
            f"Minimum confidence: "
            f"{minimum_confidence:.6f}"
        )

        print(
            f"Maximum confidence: "
            f"{maximum_confidence:.6f}"
        )

    except Exception:

        failures.append(
            "Confidence diagnostics"
        )

        print(
            "Confidence diagnostics: FAIL"
        )

    # ========================================================
    # 16. Independent verification report
    # ========================================================

    print(
        "\n16. SAVE VERIFICATION REPORT"
    )

    verification_status = (
        "PASS"
        if len(
            failures
        ) == 0
        else "FAIL"
    )

    verification = {

        "stage":
            "7.8.4",

        "component":
            "independent_production_prediction_validation",

        "status":
            verification_status,

        "verified_at_utc":
            verified_at,

        "prediction_count":
            int(
                record_count
            ),

        "feature_count":
            EXPECTED_FEATURE_COUNT,

        "model_id":
            "random_forest",

        "model_sha256":
            actual_model_hash,

        "model_hash_verified":
            actual_model_hash
            in declared_hashes,

        "feature_hash_verified":
            actual_feature_hash
            ==
            declared_feature_hash,

        "prediction_hash_verified":
            (
                actual_prediction_hash
                ==
                metadata_prediction_hash
                ==
                report_prediction_hash
            ),

        "fixture_alignment":
            (
                prediction_ids
                ==
                metadata_ids
                and
                set(
                    prediction_ids
                )
                ==
                set(
                    upcoming_ids
                )
            ),

        "schema_integrity":
            (
                features.shape[
                    1
                ]
                ==
                EXPECTED_FEATURE_COUNT
                and
                list(
                    features.columns
                )
                ==
                list(
                    contract_features
                )
            ),

        "probability_range_valid":
            bool(
                probability_integrity
            ),

        "probability_sum_valid":
            bool(
                sum_integrity
            ),

        "target_integrity":
            bool(
                target_integrity
            ),

        "argmax_integrity":
            bool(
                argmax_integrity
            ),

        "label_integrity":
            bool(
                label_integrity
            ),

        "confidence_integrity":
            bool(
                confidence_integrity
            ),

        "upcoming_snapshot_valid":
            bool(
                future_only
            ),

        "model_retrained":
            False,

        "model_reselected":
            False,

        "hyperparameter_tuned":
            False,

        "final_test_evaluation_artifacts_used":
            False,

        "prediction_distribution":
            {
                "draw": {
                    "count":
                        target_counts[
                            0
                        ],

                    "share":
                        target_shares[
                            0
                        ],
                },

                "home_win": {
                    "count":
                        target_counts[
                            1
                        ],

                    "share":
                        target_shares[
                            1
                        ],
                },

                "away_win": {
                    "count":
                        target_counts[
                            2
                        ],

                    "share":
                        target_shares[
                            2
                        ],
                },
            },

        "confidence":
            {
                "average":
                    average_confidence,

                "minimum":
                    minimum_confidence,

                "maximum":
                    maximum_confidence,
            },

        "warnings":
            warnings,

        "failures":
            failures,

        "prediction_sha256":
            actual_prediction_hash,

        "production_feature_sha256":
            actual_feature_hash,

        "upcoming_fixture_sha256":
            actual_upcoming_hash,
    }

    with VERIFICATION_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            verification,
            file,
            indent=2,
        )

    print(
        f"Verification report:\n"
        f"{VERIFICATION_FILE}"
    )

    # ========================================================
    # Final
    # ========================================================

    print(
        "\n" + "=" * 64
    )

    if failures:

        print(
            "STAGE 7.8.4: FAIL"
        )

        print(
            f"Failures: {len(failures)}"
        )

        for failure in failures:

            print(
                f"  - {failure}"
            )

    else:

        print(
            "STAGE 7.8.4: PASS"
        )

        print(
            "Independent production prediction "
            "validation complete."
        )

        if warnings:

            print(
                f"Diagnostic warnings: "
                f"{len(warnings)}"
            )

            for warning in warnings:

                print(
                    f"  WARNING: {warning}"
                )

    print("=" * 64)

    sys.exit(
        0
        if len(
            failures
        ) == 0
        else 1
    )


if __name__ == "__main__":

    main()