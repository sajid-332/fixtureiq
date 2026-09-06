"""
FixtureIQ Stage 7.8.5
Final Stage 7.8 Production Inference Verification.

Final read-only release gate for Stage 7.8.

Verifies:
- Stage 7.8.1 locked production inference contract
- locked Random Forest identity and SHA256
- canonical 86-feature schema
- Stage 7.8.2 production historical context
- current upcoming fixture snapshot
- production feature provenance and hashes
- Stage 7.8.3 prediction artifacts
- Stage 7.8.4 independent verification
- probability / target / confidence integrity
- fixture identity alignment
- snapshot freshness
- final-test consumption protection
- no retraining, tuning, or model reselection

This script DOES NOT:
- fetch provider data
- load the model with joblib
- call predict()
- call predict_proba()
- train
- tune
- select a model
- read final-test evaluation/prediction artifacts
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
# Directories
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

FINAL_TEST_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "final_test"
)


# ============================================================
# Model artifacts
# ============================================================

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

X_TRAIN_FILE = (
    MODEL_DIR
    / "X_train.csv"
)


# ============================================================
# Stage 7.8.2 artifacts
# ============================================================

PRODUCTION_HISTORY_FILE = (
    PRODUCTION_DIR
    / "production_history.csv"
)

PRODUCTION_HISTORY_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_history_report.json"
)

UPCOMING_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
)

FIXTURE_FETCH_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_fixture_fetch_report.json"
)

FEATURE_FILE = (
    PRODUCTION_DIR
    / "production_features.csv"
)

FEATURE_METADATA_FILE = (
    PRODUCTION_DIR
    / "production_fixture_metadata.csv"
)

FEATURE_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_feature_report.json"
)


# ============================================================
# Stage 7.8.3 artifacts
# ============================================================

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


# ============================================================
# Stage 7.8.4 artifact
# ============================================================

PREDICTION_VERIFICATION_FILE = (
    PRODUCTION_DIR
    / "production_prediction_verification.json"
)


# ============================================================
# Stage 7.8.5 output
# ============================================================

FINAL_VERIFICATION_FILE = (
    PRODUCTION_DIR
    / "stage7_8_final_verification.json"
)


# ============================================================
# Final-test lifecycle lock
# ============================================================

FINAL_TEST_LOCK_FILE = (
    FINAL_TEST_DIR
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

UPCOMING_STATUSES = {
    "NS",
    "PST",
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
            f"File missing: {path}"
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
            f"JSON artifact missing: {path}"
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

    hashes = set()

    pattern = re.compile(
        r"^[0-9a-fA-F]{64}$"
    )

    def walk(
        value,
        path="",
    ):

        if isinstance(
            value,
            dict,
        ):

            for key, child in value.items():

                child_path = (
                    f"{path}.{key}"
                    if path
                    else str(key)
                )

                walk(
                    child,
                    child_path,
                )

        elif isinstance(
            value,
            list,
        ):

            for child in value:
                walk(
                    child,
                    path,
                )

        elif isinstance(
            value,
            str,
        ):

            if (
                "sha256" in path.lower()
                and
                pattern.fullmatch(
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
    condition,
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

    dataframe = dataframe.copy()

    if "fixture_id" not in dataframe.columns:
        raise RuntimeError(
            "fixture_id column missing."
        )

    dataframe[
        "fixture_id"
    ] = pd.to_numeric(
        dataframe[
            "fixture_id"
        ],
        errors="raise",
    ).astype(
        "int64"
    )

    return dataframe


def to_builtin(
    value,
):
    """
    Convert NumPy/Pandas values recursively into objects
    that Python's json module can serialize safely.
    """

    if isinstance(
        value,
        np.bool_,
    ):
        return bool(
            value
        )

    if isinstance(
        value,
        np.integer,
    ):
        return int(
            value
        )

    if isinstance(
        value,
        np.floating,
    ):
        return float(
            value
        )

    if isinstance(
        value,
        pd.Timestamp,
    ):
        return value.isoformat()

    if isinstance(
        value,
        Path,
    ):
        return str(
            value
        )

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key):
                to_builtin(
                    child
                )
            for key, child
            in value.items()
        }

    if isinstance(
        value,
        list,
    ):
        return [
            to_builtin(
                child
            )
            for child in value
        ]

    if isinstance(
        value,
        tuple,
    ):
        return [
            to_builtin(
                child
            )
            for child in value
        ]

    if isinstance(
        value,
        set,
    ):
        return [
            to_builtin(
                child
            )
            for child in sorted(
                value,
                key=str,
            )
        ]

    return value


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 68)

    print(
        "FixtureIQ Stage 7.8.5"
    )

    print(
        "Final Stage 7.8 Production Inference Verification"
    )

    print("=" * 68)

    failures = []
    warnings = []

    verified_at = datetime.now(
        timezone.utc
    ).isoformat()

    # ========================================================
    # 1. Artifact inventory
    # ========================================================

    print(
        "\n1. ARTIFACT INVENTORY"
    )

    required_files = [
        MODEL_FILE,
        MODEL_LIFECYCLE_FILE,
        MODEL_MANIFEST_FILE,
        CONTRACT_FILE,
        X_TRAIN_FILE,

        PRODUCTION_HISTORY_FILE,
        PRODUCTION_HISTORY_REPORT_FILE,

        UPCOMING_FILE,
        FIXTURE_FETCH_REPORT_FILE,

        FEATURE_FILE,
        FEATURE_METADATA_FILE,
        FEATURE_REPORT_FILE,

        PREDICTION_FILE,
        PREDICTION_METADATA_FILE,
        PREDICTION_REPORT_FILE,

        PREDICTION_VERIFICATION_FILE,

        FINAL_TEST_LOCK_FILE,
    ]

    for path in required_files:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        print(
            "\nRequired artifacts are missing."
        )

        print(
            "STAGE 7.8.5: FAIL"
        )

        sys.exit(1)

    # ========================================================
    # Load JSON artifacts
    # ========================================================

    contract = load_json(
        CONTRACT_FILE
    )

    lifecycle = load_json(
        MODEL_LIFECYCLE_FILE
    )

    manifest = load_json(
        MODEL_MANIFEST_FILE
    )

    history_report = load_json(
        PRODUCTION_HISTORY_REPORT_FILE
    )

    fetch_report = load_json(
        FIXTURE_FETCH_REPORT_FILE
    )

    feature_report = load_json(
        FEATURE_REPORT_FILE
    )

    prediction_metadata = load_json(
        PREDICTION_METADATA_FILE
    )

    prediction_report = load_json(
        PREDICTION_REPORT_FILE
    )

    stage_7_8_4 = load_json(
        PREDICTION_VERIFICATION_FILE
    )

    # ========================================================
    # 2. Stage 7.8.1 contract
    # ========================================================

    print(
        "\n2. STAGE 7.8.1 CONTRACT"
    )

    check(
        "Contract stage = 7.8.1",
        contract.get(
            "stage"
        ) == "7.8.1",
        failures,
    )

    check(
        "Contract status = LOCKED_CONTRACT",
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
        "Selected model = random_forest",
        model_contract.get(
            "candidate_id"
        ) == "random_forest",
        failures,
    )

    check(
        "Model status = LOCKED",
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

    check(
        "Target mapping contract",
        contract.get(
            "target_mapping"
        )
        ==
        {
            "0": "draw",
            "1": "home_win",
            "2": "away_win",
        },
        failures,
    )

    # ========================================================
    # 3. Canonical feature schema
    # ========================================================

    print(
        "\n3. CANONICAL FEATURE SCHEMA"
    )

    x_train_columns = list(
        pd.read_csv(
            X_TRAIN_FILE,
            nrows=0,
        ).columns
    )

    check(
        "X_train feature count = 86",
        len(
            x_train_columns
        ) == EXPECTED_FEATURE_COUNT,
        failures,
    )

    check(
        "X_train excludes fixture_id",
        "fixture_id"
        not in x_train_columns,
        failures,
    )

    check(
        "Contract schema = X_train schema",
        contract_features
        ==
        x_train_columns,
        failures,
    )

    # ========================================================
    # 4. Locked model integrity
    # ========================================================

    print(
        "\n4. LOCKED MODEL INTEGRITY"
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
        "Production model SHA256 MATCH",
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

    final_test_contract = contract.get(
        "final_test",
        {},
    )

    check(
        "Final test lifecycle = CONSUMED",
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

    print(
        f"Model SHA256: "
        f"{actual_model_hash}"
    )

    # ========================================================
    # 5. Production historical context
    # ========================================================

    print(
        "\n5. PRODUCTION HISTORICAL CONTEXT"
    )

    history = pd.read_csv(
        PRODUCTION_HISTORY_FILE
    )

    history = normalize_fixture_ids(
        history
    )

    check(
        "History report stage = 7.8.2",
        history_report.get(
            "stage"
        ) == "7.8.2",
        failures,
    )

    check(
        "History report status = PASS",
        history_report.get(
            "status"
        ) == "PASS",
        failures,
    )

    base_count = int(
        history_report.get(
            "base_historical_records",
            -1,
        )
    )

    season_2025_count = int(
        history_report.get(
            "season_2025_26_records",
            -1,
        )
    )

    current_completed_count = int(
        history_report.get(
            "current_season_completed_records",
            -1,
        )
    )

    reported_history_total = int(
        history_report.get(
            "total_production_history",
            -1,
        )
    )

    check(
        "History component count consistency",
        (
            base_count
            +
            season_2025_count
            +
            current_completed_count
        )
        ==
        reported_history_total,
        failures,
    )

    check(
        "History CSV count = report count",
        len(
            history
        )
        ==
        reported_history_total,
        failures,
    )

    check(
        "Historical fixture IDs unique",
        history[
            "fixture_id"
        ].is_unique,
        failures,
    )

    history_dates = pd.to_datetime(
        history[
            "date"
        ],
        errors="coerce",
        utc=True,
    )

    history_dates_valid = (
        not history_dates.isna().any()
    )

    check(
        "Historical dates valid",
        history_dates_valid,
        failures,
    )

    now = pd.Timestamp.now(
        tz="UTC"
    )

    historical_not_future = (
        history_dates_valid
        and
        (
            history_dates <= now
        ).all()
    )

    check(
        "Historical fixtures are not future",
        historical_not_future,
        failures,
    )

    try:

        home_goals = pd.to_numeric(
            history[
                "home_goals"
            ],
            errors="raise",
        )

        away_goals = pd.to_numeric(
            history[
                "away_goals"
            ],
            errors="raise",
        )

        score_integrity = bool(
            np.isfinite(
                home_goals.to_numpy(
                    dtype=float
                )
            ).all()
            and
            np.isfinite(
                away_goals.to_numpy(
                    dtype=float
                )
            ).all()
            and
            (
                home_goals >= 0
            ).all()
            and
            (
                away_goals >= 0
            ).all()
        )

    except Exception:

        score_integrity = False

    check(
        "Completed-score integrity",
        score_integrity,
        failures,
    )

    check(
        "History uses completed results only",
        history_report.get(
            "completed_results_only"
        ) is True,
        failures,
    )

    check(
        "Protected historical dataset unchanged",
        history_report.get(
            "historical_fixtures_modified"
        ) is False,
        failures,
    )

    check(
        "History final-test evaluation artifacts used = false",
        history_report.get(
            "final_test_evaluation_artifacts_used"
        ) is False,
        failures,
    )

    check(
        "History model retrained = false",
        history_report.get(
            "model_retrained"
        ) is False,
        failures,
    )

    check(
        "History model reselected = false",
        history_report.get(
            "model_reselected"
        ) is False,
        failures,
    )

    # ========================================================
    # 6. Production upcoming fixtures
    # ========================================================

    print(
        "\n6. PRODUCTION UPCOMING FIXTURES"
    )

    upcoming = pd.read_csv(
        UPCOMING_FILE
    )

    upcoming = normalize_fixture_ids(
        upcoming
    )

    check(
        "Fixture fetch stage = 7.8.2",
        fetch_report.get(
            "stage"
        ) == "7.8.2",
        failures,
    )

    check(
        "Fixture fetch status = PASS",
        fetch_report.get(
            "status"
        ) == "PASS",
        failures,
    )

    check(
        "Provider = football-data.org",
        fetch_report.get(
            "provider"
        ) == "football-data.org",
        failures,
    )

    check(
        "Fallback season used = false",
        fetch_report.get(
            "fallback_season_used"
        ) is False,
        failures,
    )

    check(
        "Completed fixtures used = false",
        fetch_report.get(
            "completed_fixtures_used"
        ) is False,
        failures,
    )

    check(
        "Fixture feed final-test artifacts used = false",
        fetch_report.get(
            "final_test_evaluation_artifacts_used"
        ) is False,
        failures,
    )

    check(
        "Upcoming count = fetch report",
        len(
            upcoming
        )
        ==
        int(
            fetch_report.get(
                "upcoming_fixture_count",
                -1,
            )
        ),
        failures,
    )

    check(
        "Upcoming fixture IDs unique",
        upcoming[
            "fixture_id"
        ].is_unique,
        failures,
    )

    statuses = set(
        upcoming[
            "status_short"
        ]
        .dropna()
        .astype(str)
        .unique()
    )

    check(
        "Upcoming statuses valid",
        statuses.issubset(
            UPCOMING_STATUSES
        ),
        failures,
    )

    upcoming_dates = pd.to_datetime(
        upcoming[
            "date"
        ],
        errors="coerce",
        utc=True,
    )

    upcoming_dates_valid = (
        not upcoming_dates.isna().any()
    )

    check(
        "Upcoming dates valid",
        upcoming_dates_valid,
        failures,
    )

    snapshot_fresh = bool(
        upcoming_dates_valid
        and
        (
            upcoming_dates > now
        ).all()
    )

    check(
        "All fixtures are still upcoming",
        snapshot_fresh,
        failures,
    )

    # ========================================================
    # 7. As-of chronology
    # ========================================================

    print(
        "\n7. AS-OF CHRONOLOGY"
    )

    latest_history = (
        history_dates.max()
    )

    earliest_upcoming = (
        upcoming_dates.min()
        if len(
            upcoming_dates
        ) > 0
        else pd.NaT
    )

    chronology_ok = bool(
        pd.notna(
            latest_history
        )
        and
        pd.notna(
            earliest_upcoming
        )
        and
        latest_history
        <
        earliest_upcoming
    )

    check(
        "Completed history precedes upcoming snapshot",
        chronology_ok,
        failures,
    )

    print(
        f"Latest completed match: "
        f"{latest_history}"
    )

    print(
        f"Earliest upcoming fixture: "
        f"{earliest_upcoming}"
    )

    # ========================================================
    # 8. Production features
    # ========================================================

    print(
        "\n8. PRODUCTION FEATURES"
    )

    features = pd.read_csv(
        FEATURE_FILE
    )

    feature_metadata = pd.read_csv(
        FEATURE_METADATA_FILE
    )

    feature_metadata = normalize_fixture_ids(
        feature_metadata
    )

    check(
        "Feature report stage = 7.8.2",
        feature_report.get(
            "stage"
        ) == "7.8.2",
        failures,
    )

    check(
        "Feature report status = PASS",
        feature_report.get(
            "status"
        ) == "PASS",
        failures,
    )

    check(
        "Feature count = 86",
        features.shape[
            1
        ] == EXPECTED_FEATURE_COUNT,
        failures,
    )

    check(
        "Feature schema = locked schema",
        list(
            features.columns
        )
        ==
        contract_features,
        failures,
    )

    check(
        "Feature rows = upcoming rows",
        len(
            features
        )
        ==
        len(
            upcoming
        ),
        failures,
    )

    check(
        "Feature metadata rows = upcoming rows",
        len(
            feature_metadata
        )
        ==
        len(
            upcoming
        ),
        failures,
    )

    try:

        feature_values = features.to_numpy(
            dtype=float
        )

        feature_numeric_ok = bool(
            np.isfinite(
                feature_values
            ).all()
        )

    except Exception:

        feature_numeric_ok = False

    check(
        "Feature numeric integrity",
        feature_numeric_ok,
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
        "Feature target leakage = NONE",
        len(
            forbidden_features
            &
            set(
                features.columns
            )
        ) == 0,
        failures,
    )

    check(
        "Strict pre-match feature state",
        feature_report.get(
            "strict_pre_match"
        ) is True,
        failures,
    )

    check(
        "Upcoming fixtures do not update state",
        feature_report.get(
            "upcoming_fixtures_update_state"
        ) is False,
        failures,
    )

    # ========================================================
    # 9. Stage 7.8.2 hash chain
    # ========================================================

    print(
        "\n9. STAGE 7.8.2 HASH CHAIN"
    )

    actual_history_hash = sha256_file(
        PRODUCTION_HISTORY_FILE
    ).lower()

    actual_upcoming_hash = sha256_file(
        UPCOMING_FILE
    ).lower()

    actual_feature_hash = sha256_file(
        FEATURE_FILE
    ).lower()

    check(
        "Production history SHA256",
        actual_history_hash
        ==
        str(
            feature_report.get(
                "production_history_sha256",
                "",
            )
        ).lower(),
        failures,
    )

    check(
        "Upcoming fixture SHA256",
        actual_upcoming_hash
        ==
        str(
            feature_report.get(
                "upcoming_fixture_sha256",
                "",
            )
        ).lower(),
        failures,
    )

    check(
        "Production feature SHA256",
        actual_feature_hash
        ==
        str(
            feature_report.get(
                "production_feature_sha256",
                "",
            )
        ).lower(),
        failures,
    )

    # ========================================================
    # 10. Fixture identity alignment
    # ========================================================

    print(
        "\n10. FIXTURE IDENTITY ALIGNMENT"
    )

    upcoming_ids = (
        upcoming[
            "fixture_id"
        ].tolist()
    )

    metadata_ids = (
        feature_metadata[
            "fixture_id"
        ].tolist()
    )

    check(
        "Feature metadata fixture order",
        metadata_ids
        ==
        upcoming_ids,
        failures,
    )

    identity_fields = [
        "home_team_id",
        "home_team_name",
        "away_team_id",
        "away_team_name",
    ]

    for field in identity_fields:

        field_ok = (
            field in upcoming.columns
            and
            field in feature_metadata.columns
        )

        if field_ok:

            field_ok = (
                upcoming[
                    field
                ]
                .astype(str)
                .tolist()
                ==
                feature_metadata[
                    field
                ]
                .astype(str)
                .tolist()
            )

        check(
            f"{field} alignment",
            field_ok,
            failures,
        )

    # ========================================================
    # 11. Production predictions
    # ========================================================

    print(
        "\n11. PRODUCTION PREDICTIONS"
    )

    predictions = pd.read_csv(
        PREDICTION_FILE
    )

    predictions = normalize_fixture_ids(
        predictions
    )

    check(
        "Prediction metadata stage = 7.8.3",
        prediction_metadata.get(
            "stage"
        ) == "7.8.3",
        failures,
    )

    check(
        "Prediction metadata status = PASS",
        prediction_metadata.get(
            "status"
        ) == "PASS",
        failures,
    )

    check(
        "Prediction report stage = 7.8.3",
        prediction_report.get(
            "stage"
        ) == "7.8.3",
        failures,
    )

    check(
        "Prediction report status = PASS",
        prediction_report.get(
            "status"
        ) == "PASS",
        failures,
    )

    prediction_count = len(
        predictions
    )

    check(
        "Prediction count > 0",
        prediction_count > 0,
        failures,
    )

    check(
        "Prediction count = feature count",
        prediction_count
        ==
        len(
            features
        ),
        failures,
    )

    check(
        "Prediction count = metadata",
        prediction_count
        ==
        int(
            prediction_metadata.get(
                "prediction_count",
                -1,
            )
        ),
        failures,
    )

    check(
        "Prediction count = report",
        prediction_count
        ==
        int(
            prediction_report.get(
                "prediction_count",
                -1,
            )
        ),
        failures,
    )

    check(
        "Prediction fixture IDs unique",
        predictions[
            "fixture_id"
        ].is_unique,
        failures,
    )

    check(
        "Prediction fixture order = feature metadata",
        predictions[
            "fixture_id"
        ].tolist()
        ==
        metadata_ids,
        failures,
    )

    # ========================================================
    # 12. Prediction integrity
    # ========================================================

    print(
        "\n12. PREDICTION INTEGRITY"
    )

    required_prediction_columns = {
        "fixture_id",
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

    prediction_schema_ok = bool(
        required_prediction_columns
        .issubset(
            set(
                predictions.columns
            )
        )
    )

    check(
        "Prediction schema",
        prediction_schema_ok,
        failures,
    )

    probability_range_ok = False
    probability_sum_ok = False
    target_ok = False
    argmax_ok = False
    label_ok = False
    confidence_ok = False

    if prediction_schema_ok:

        try:

            probability_values = (
                predictions[
                    PROBABILITY_COLUMNS
                ].to_numpy(
                    dtype=float
                )
            )

            probability_range_ok = bool(
                np.isfinite(
                    probability_values
                ).all()
                and
                (
                    probability_values >= 0
                ).all()
                and
                (
                    probability_values <= 1
                ).all()
            )

            probability_sum_ok = bool(
                np.allclose(
                    probability_values.sum(
                        axis=1
                    ),
                    1.0,
                    atol=1e-8,
                    rtol=0.0,
                )
            )

            targets = (
                pd.to_numeric(
                    predictions[
                        "predicted_target"
                    ],
                    errors="raise",
                )
                .astype(int)
                .to_numpy()
            )

            target_ok = bool(
                set(
                    targets.tolist()
                ).issubset(
                    EXPECTED_TARGETS
                )
            )

            expected_targets = np.argmax(
                probability_values,
                axis=1,
            ).astype(
                int
            )

            argmax_ok = bool(
                np.array_equal(
                    targets,
                    expected_targets,
                )
            )

            expected_labels = [
                LABEL_MAPPING[
                    int(target)
                ]
                for target in targets
            ]

            actual_labels = (
                predictions[
                    "predicted_label"
                ]
                .astype(str)
                .tolist()
            )

            label_ok = bool(
                expected_labels
                ==
                actual_labels
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

            confidence_ok = bool(
                np.allclose(
                    expected_confidence,
                    actual_confidence,
                    atol=1e-12,
                    rtol=0.0,
                )
            )

        except Exception:

            pass

    check(
        "Probability range [0,1]",
        probability_range_ok,
        failures,
    )

    check(
        "Probability sums = 1",
        probability_sum_ok,
        failures,
    )

    check(
        "Predicted targets valid",
        target_ok,
        failures,
    )

    check(
        "Prediction = probability argmax",
        argmax_ok,
        failures,
    )

    check(
        "Prediction label mapping",
        label_ok,
        failures,
    )

    check(
        "Confidence integrity",
        confidence_ok,
        failures,
    )

    # ========================================================
    # 13. Prediction model provenance
    # ========================================================

    print(
        "\n13. PREDICTION MODEL PROVENANCE"
    )

    check(
        "Prediction metadata model = random_forest",
        prediction_metadata.get(
            "model_id"
        ) == "random_forest",
        failures,
    )

    check(
        "Prediction metadata model status = LOCKED",
        prediction_metadata.get(
            "model_status"
        ) == "LOCKED",
        failures,
    )

    check(
        "Prediction metadata model SHA256",
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

    row_model_id_ok = bool(
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
        "Every prediction row model ID",
        row_model_id_ok,
        failures,
    )

    row_model_hash_ok = bool(
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
        "Every prediction row model SHA256",
        row_model_hash_ok,
        failures,
    )

    try:

        row_feature_counts = (
            pd.to_numeric(
                predictions[
                    "feature_count"
                ],
                errors="raise",
            )
            .astype(int)
        )

        row_feature_count_ok = bool(
            set(
                row_feature_counts.tolist()
            )
            ==
            {
                EXPECTED_FEATURE_COUNT
            }
        )

    except Exception:

        row_feature_count_ok = False

    check(
        "Every prediction row feature_count = 86",
        row_feature_count_ok,
        failures,
    )

    # ========================================================
    # 14. Stage 7.8.3 hash chain
    # ========================================================

    print(
        "\n14. STAGE 7.8.3 HASH CHAIN"
    )

    actual_prediction_hash = sha256_file(
        PREDICTION_FILE
    ).lower()

    check(
        "Prediction CSV -> metadata SHA256",
        actual_prediction_hash
        ==
        str(
            prediction_metadata.get(
                "prediction_sha256",
                "",
            )
        ).lower(),
        failures,
    )

    check(
        "Prediction CSV -> report SHA256",
        actual_prediction_hash
        ==
        str(
            prediction_report.get(
                "prediction_sha256",
                "",
            )
        ).lower(),
        failures,
    )

    check(
        "Prediction metadata -> feature SHA256",
        actual_feature_hash
        ==
        str(
            prediction_metadata.get(
                "production_feature_sha256",
                "",
            )
        ).lower(),
        failures,
    )

    check(
        "Prediction metadata -> upcoming SHA256",
        actual_upcoming_hash
        ==
        str(
            prediction_metadata.get(
                "upcoming_fixture_sha256",
                "",
            )
        ).lower(),
        failures,
    )

    # ========================================================
    # 15. Stage 7.8.4 independent verification
    # ========================================================

    print(
        "\n15. STAGE 7.8.4 INDEPENDENT VERIFICATION"
    )

    check(
        "7.8.4 stage",
        stage_7_8_4.get(
            "stage"
        ) == "7.8.4",
        failures,
    )

    check(
        "7.8.4 status = PASS",
        stage_7_8_4.get(
            "status"
        ) == "PASS",
        failures,
    )

    check(
        "7.8.4 failures = 0",
        len(
            stage_7_8_4.get(
                "failures",
                [],
            )
        ) == 0,
        failures,
    )

    check(
        "7.8.4 prediction count",
        int(
            stage_7_8_4.get(
                "prediction_count",
                -1,
            )
        )
        ==
        prediction_count,
        failures,
    )

    check(
        "7.8.4 model SHA256",
        str(
            stage_7_8_4.get(
                "model_sha256",
                "",
            )
        ).lower()
        ==
        actual_model_hash,
        failures,
    )

    check(
        "7.8.4 prediction SHA256",
        str(
            stage_7_8_4.get(
                "prediction_sha256",
                "",
            )
        ).lower()
        ==
        actual_prediction_hash,
        failures,
    )

    check(
        "7.8.4 feature SHA256",
        str(
            stage_7_8_4.get(
                "production_feature_sha256",
                "",
            )
        ).lower()
        ==
        actual_feature_hash,
        failures,
    )

    check(
        "7.8.4 upcoming SHA256",
        str(
            stage_7_8_4.get(
                "upcoming_fixture_sha256",
                "",
            )
        ).lower()
        ==
        actual_upcoming_hash,
        failures,
    )

    previous_warnings = (
        stage_7_8_4.get(
            "warnings",
            [],
        )
    )

    if isinstance(
        previous_warnings,
        list,
    ):

        warnings.extend(
            str(item)
            for item in previous_warnings
        )

    # ========================================================
    # 16. Cross-stage protection
    # ========================================================

    print(
        "\n16. CROSS-STAGE PROTECTION"
    )

    protections = [

        history_report.get(
            "model_retrained"
        ) is False,

        history_report.get(
            "model_reselected"
        ) is False,

        history_report.get(
            "hyperparameter_tuning"
        ) is False,

        fetch_report.get(
            "model_retrained"
        ) is False,

        fetch_report.get(
            "model_reselected"
        ) is False,

        fetch_report.get(
            "hyperparameter_tuned"
        ) is False,

        feature_report.get(
            "model_retrained"
        ) is False,

        feature_report.get(
            "model_selected"
        ) is False,

        feature_report.get(
            "hyperparameter_tuned"
        ) is False,

        prediction_metadata.get(
            "model_retrained"
        ) is False,

        prediction_metadata.get(
            "model_reselected"
        ) is False,

        prediction_metadata.get(
            "hyperparameter_tuned"
        ) is False,

        prediction_report.get(
            "model_retrained"
        ) is False,

        prediction_report.get(
            "model_reselected"
        ) is False,

        prediction_report.get(
            "hyperparameter_tuned"
        ) is False,
    ]

    check(
        "No retraining/reselection/tuning",
        all(
            protections
        ),
        failures,
    )

    final_test_protections = [

        history_report.get(
            "final_test_evaluation_artifacts_used"
        ) is False,

        fetch_report.get(
            "final_test_evaluation_artifacts_used"
        ) is False,

        feature_report.get(
            "final_test_evaluation_artifacts_used"
        ) is False,

        prediction_metadata.get(
            "final_test_evaluation_artifacts_used"
        ) is False,

        prediction_report.get(
            "final_test_evaluation_artifacts_used"
        ) is False,

        stage_7_8_4.get(
            "final_test_evaluation_artifacts_used"
        ) is False,
    ]

    check(
        "Final-test evaluation artifacts excluded",
        all(
            final_test_protections
        ),
        failures,
    )

    check(
        "Final-test consumption lock exists",
        FINAL_TEST_LOCK_FILE.exists(),
        failures,
    )

    # ========================================================
    # 17. Production readiness diagnostics
    # ========================================================

    print(
        "\n17. PRODUCTION READINESS DIAGNOSTICS"
    )

    upcoming_team_count = int(
        feature_report.get(
            "upcoming_team_count",
            0,
        )
    )

    historical_team_count = int(
        feature_report.get(
            "teams_with_historical_state",
            0,
        )
    )

    zero_state_teams = (
        feature_report.get(
            "zero_state_teams",
            [],
        )
    )

    if not isinstance(
        zero_state_teams,
        list,
    ):
        zero_state_teams = []

    print(
        f"Production history records: "
        f"{len(history)}"
    )

    print(
        f"Upcoming fixtures: "
        f"{len(upcoming)}"
    )

    print(
        f"Feature matrix: "
        f"{features.shape}"
    )

    print(
        f"Predictions: "
        f"{prediction_count}"
    )

    print(
        f"Upcoming teams: "
        f"{upcoming_team_count}"
    )

    print(
        f"Teams with historical state: "
        f"{historical_team_count}"
    )

    print(
        f"Zero-state teams: "
        f"{len(zero_state_teams)}"
    )

    if zero_state_teams:

        warning = (
            "Production snapshot contains "
            f"{len(zero_state_teams)} "
            "zero-state team(s): "
            +
            ", ".join(
                str(team)
                for team in zero_state_teams
            )
        )

        warnings.append(
            warning
        )

        print(
            "Zero-state diagnostic: WARNING"
        )

    else:

        print(
            "Zero-state diagnostic: PASS"
        )

    # --------------------------------------------------------
    # Draw-class diagnostic
    # --------------------------------------------------------

    try:

        targets = (
            pd.to_numeric(
                predictions[
                    "predicted_target"
                ],
                errors="raise",
            )
            .astype(int)
        )

        draw_count = int(
            (
                targets == 0
            ).sum()
        )

        draw_share = float(
            draw_count
            /
            prediction_count
            if prediction_count > 0
            else 0.0
        )

        print(
            f"Draw predictions: "
            f"{draw_count} "
            f"({draw_share * 100:.2f}%)"
        )

        if (
            prediction_count > 0
            and
            draw_share < 0.01
        ):

            draw_warning = (
                "Draw predictions represent less "
                "than 1% of the production snapshot. "
                "This remains a model-behavior "
                "diagnostic and does not invalidate "
                "pipeline integrity."
            )

            if draw_warning not in warnings:

                warnings.append(
                    draw_warning
                )

            print(
                "Draw-class diagnostic: WARNING"
            )

        else:

            print(
                "Draw-class diagnostic: PASS"
            )

    except Exception:

        check(
            "Draw distribution calculation",
            False,
            failures,
        )

        draw_count = None
        draw_share = None

    # ========================================================
    # 18. Final snapshot freshness
    # ========================================================

    print(
        "\n18. FINAL SNAPSHOT FRESHNESS"
    )

    final_now = pd.Timestamp.now(
        tz="UTC"
    )

    final_prediction_dates = pd.to_datetime(
        predictions[
            "date"
        ],
        errors="coerce",
        utc=True,
    )

    final_freshness = bool(
        not final_prediction_dates.isna().any()
        and
        (
            final_prediction_dates
            > final_now
        ).all()
    )

    check(
        "Prediction snapshot currently servable",
        final_freshness,
        failures,
    )

    if not final_freshness:

        warnings.append(
            "Production snapshot became stale. "
            "Refresh 7.8.2, rerun 7.8.3, then "
            "rerun 7.8.4 before final verification."
        )

    # ========================================================
    # 19. Save final verification
    # ========================================================

    print(
        "\n19. SAVE FINAL VERIFICATION"
    )

    final_status = (
        "PASS"
        if len(
            failures
        ) == 0
        else "FAIL"
    )

    # Deduplicate warnings while retaining order.
    warnings = list(
        dict.fromkeys(
            warnings
        )
    )

    history_integrity = bool(
        bool(
            history[
                "fixture_id"
            ].is_unique
        )
        and
        bool(
            score_integrity
        )
    )

    contract_schema_verified = bool(
        contract_features
        ==
        x_train_columns
    )

    feature_schema_verified = bool(
        list(
            features.columns
        )
        ==
        contract_features
    )

    probability_integrity = bool(
        probability_range_ok
        and
        probability_sum_ok
    )

    final_target_integrity = bool(
        target_ok
        and
        argmax_ok
        and
        label_ok
    )

    stage_7_8_4_verified = bool(
        stage_7_8_4.get(
            "status"
        ) == "PASS"
    )

    final_report = {

        "stage":
            "7.8.5",

        "stage_7_8_status":
            (
                "COMPLETE"
                if final_status == "PASS"
                else "INCOMPLETE"
            ),

        "status":
            final_status,

        "verified_at_utc":
            verified_at,

        "model_id":
            "random_forest",

        "model_status":
            "LOCKED",

        "model_sha256":
            actual_model_hash,

        "feature_count":
            EXPECTED_FEATURE_COUNT,

        "production_history_records":
            int(
                len(history)
            ),

        "upcoming_fixture_count":
            int(
                len(upcoming)
            ),

        "production_feature_count":
            int(
                len(features)
            ),

        "prediction_count":
            int(
                prediction_count
            ),

        "model_hash_verified":
            bool(
                actual_model_hash
                in declared_hashes
            ),

        "contract_schema_verified":
            contract_schema_verified,

        "history_integrity":
            history_integrity,

        "chronology_verified":
            bool(
                chronology_ok
            ),

        "snapshot_fresh":
            bool(
                final_freshness
            ),

        "feature_schema_verified":
            feature_schema_verified,

        "probability_integrity":
            probability_integrity,

        "target_integrity":
            final_target_integrity,

        "confidence_integrity":
            bool(
                confidence_ok
            ),

        "stage_7_8_4_verified":
            stage_7_8_4_verified,

        "model_retrained":
            False,

        "model_reselected":
            False,

        "hyperparameter_tuned":
            False,

        "final_test_evaluation_artifacts_used":
            False,

        "final_test_status":
            "CONSUMED",

        "draw_prediction_count":
            draw_count,

        "draw_prediction_share":
            draw_share,

        "warnings":
            warnings,

        "failures":
            failures,

        "artifact_hashes":
            {
                "model_sha256":
                    actual_model_hash,

                "production_history_sha256":
                    actual_history_hash,

                "upcoming_fixture_sha256":
                    actual_upcoming_hash,

                "production_feature_sha256":
                    actual_feature_hash,

                "production_prediction_sha256":
                    actual_prediction_hash,
            },
    }

    PRODUCTION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with FINAL_VERIFICATION_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            to_builtin(
                final_report
            ),
            file,
            indent=2,
        )

    print(
        f"Final verification:\n"
        f"{FINAL_VERIFICATION_FILE}"
    )

    # ========================================================
    # Final result
    # ========================================================

    print(
        "\n" + "=" * 68
    )

    if failures:

        print(
            "STAGE 7.8.5: FAIL"
        )

        print(
            "STAGE 7.8: INCOMPLETE"
        )

        print(
            f"Failures: {len(failures)}"
        )

        for failure in failures:

            print(
                f"  - {failure}"
            )

        if warnings:

            print(
                f"Warnings: {len(warnings)}"
            )

            for warning in warnings:

                print(
                    f"  WARNING: {warning}"
                )

    else:

        print(
            "STAGE 7.8.5: PASS"
        )

        print(
            "STAGE 7.8: COMPLETE"
        )

        print(
            "Production inference pipeline "
            "is internally verified and "
            "currently servable."
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

    print("=" * 68)

    sys.exit(
        0
        if not failures
        else 1
    )


if __name__ == "__main__":

    main()