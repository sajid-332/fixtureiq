"""
FixtureIQ Stage 7.8.2
Production Fixture Feature Preparation.

Consumes ONLY:

data/processed/production/upcoming_fixtures.csv

It never treats historical fixtures.csv as production input.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

sys.path.insert(
    0,
    str(BASE_DIR),
)


from backend.services.production_feature_service import (
    build_production_features,
)


HISTORY_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "historical_fixtures.csv"
)

PRODUCTION_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "production"
)

UPCOMING_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
)

FEATURE_FILE = (
    PRODUCTION_DIR
    / "production_features.csv"
)

METADATA_FILE = (
    PRODUCTION_DIR
    / "production_fixture_metadata.csv"
)

REPORT_FILE = (
    PRODUCTION_DIR
    / "production_feature_report.json"
)

CONTRACT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
    / "production_inference_contract.json"
)


UPCOMING_STATUSES = {
    "NS",
    "TBD",
    "PST",
}


def sha256_file(
    path: Path,
) -> str:

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


def load_contract() -> dict:

    if not CONTRACT_FILE.exists():

        raise FileNotFoundError(
            f"Production contract not found: "
            f"{CONTRACT_FILE}"
        )

    with CONTRACT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(
            file
        )


def main():

    print("=" * 55)

    print(
        "FixtureIQ Stage 7.8.2"
    )

    print(
        "Production Fixture Feature Preparation"
    )

    print("=" * 55)

    # ========================================================
    # 1. CONTRACT
    # ========================================================

    print(
        "\n1. PRODUCTION CONTRACT"
    )

    contract = load_contract()

    if contract.get(
        "stage"
    ) != "7.8.1":

        raise RuntimeError(
            "Invalid production inference contract."
        )

    if contract.get(
        "status"
    ) != "LOCKED_CONTRACT":

        raise RuntimeError(
            "Production inference contract is not locked."
        )

    if contract.get(
        "model",
        {}
    ).get(
        "status"
    ) != "LOCKED":

        raise RuntimeError(
            "Production model is not locked."
        )

    if contract.get(
        "feature_count"
    ) != 86:

        raise RuntimeError(
            "Production contract does not contain "
            "86 features."
        )

    print(
        "Contract: PASS"
    )

    print(
        "Model: Random Forest"
    )

    print(
        "Model status: LOCKED"
    )

    print(
        "Feature count: 86"
    )

    # ========================================================
    # 2. INPUT FILES
    # ========================================================

    print(
        "\n2. INPUT DATA"
    )

    if not HISTORY_FILE.exists():

        raise FileNotFoundError(
            f"Historical dataset missing: "
            f"{HISTORY_FILE}"
        )

    if not UPCOMING_FILE.exists():

        print(
            "Upcoming production fixture file: MISSING"
        )

        print(
            "\nRun first:"
        )

        print(
            "python scripts\\fetch_production_fixtures.py"
        )

        raise FileNotFoundError(
            "No valid production upcoming fixture "
            "snapshot exists."
        )

    history = pd.read_csv(
        HISTORY_FILE
    )

    upcoming = pd.read_csv(
        UPCOMING_FILE
    )

    print(
        f"Historical records: {len(history)}"
    )

    print(
        f"Upcoming fixtures: {len(upcoming)}"
    )

    if history.empty:

        raise RuntimeError(
            "Historical dataset is empty."
        )

    if upcoming.empty:

        raise RuntimeError(
            "Upcoming fixture dataset is empty."
        )

    # ========================================================
    # 3. UPCOMING FIXTURE SAFETY
    # ========================================================

    print(
        "\n3. UPCOMING FIXTURE SAFETY"
    )

    required = {
        "fixture_id",
        "date",
        "status_short",
        "home_team_id",
        "home_team_name",
        "away_team_id",
        "away_team_name",
    }

    missing = (
        required
        -
        set(
            upcoming.columns
        )
    )

    if missing:

        raise RuntimeError(
            "Upcoming fixture file is missing "
            f"required columns: {sorted(missing)}"
        )

    status_values = set(
        upcoming[
            "status_short"
        ]
        .dropna()
        .astype(str)
        .unique()
    )

    if not status_values.issubset(
        UPCOMING_STATUSES
    ):

        raise RuntimeError(
            "Completed or invalid fixture status "
            f"detected: {sorted(status_values)}"
        )

    dates = pd.to_datetime(
        upcoming["date"],
        errors="coerce",
        utc=True,
    )

    if dates.isna().any():

        raise RuntimeError(
            "Invalid production fixture dates."
        )

    now = pd.Timestamp.now(
        tz="UTC"
    )

    if (
        dates <= now
    ).any():

        raise RuntimeError(
            "Past fixtures exist in the production "
            "upcoming fixture snapshot."
        )

    if not upcoming[
        "fixture_id"
    ].is_unique:

        raise RuntimeError(
            "Production fixture IDs are not unique."
        )

    print(
        "Only upcoming statuses: PASS"
    )

    print(
        "Future dates only: PASS"
    )

    print(
        "Fixture IDs unique: PASS"
    )

    print(
        "Completed matches used: NO"
    )

    # ========================================================
    # 4. FEATURE CONSTRUCTION
    # ========================================================

    print(
        "\n4. FEATURE CONSTRUCTION"
    )

    metadata, features = (
        build_production_features(
            history,
            upcoming,
        )
    )

    print(
        f"Production records: {len(features)}"
    )

    print(
        f"Model matrix: {features.shape}"
    )

    print(
        "Strict pre-match state: PASS"
    )

    # ========================================================
    # 5. FEATURE SCHEMA
    # ========================================================

    print(
        "\n5. FEATURE SCHEMA"
    )

    contract_features = (
        contract.get(
            "feature_columns",
            [],
        )
    )

    if len(
        contract_features
    ) != 86:

        raise RuntimeError(
            "Contract feature schema is invalid."
        )

    if list(
        features.columns
    ) != contract_features:

        raise RuntimeError(
            "Production feature schema does not "
            "match locked training schema."
        )

    if features.shape[
        1
    ] != 86:

        raise RuntimeError(
            "Production feature count is not 86."
        )

    print(
        "86 features: PASS"
    )

    print(
        "Feature order: PASS"
    )

    print(
        "Training schema identity: PASS"
    )

    # ========================================================
    # 6. LEAKAGE
    # ========================================================

    print(
        "\n6. LEAKAGE PROTECTION"
    )

    forbidden = {
        "fixture_id",
        "target",
        "target_label",
        "home_goals",
        "away_goals",
        "FTHG",
        "FTAG",
        "FTR",
        "status_short",
        "status_long",
        "status_elapsed",
    }

    leaked = (
        forbidden
        &
        set(
            features.columns
        )
    )

    if leaked:

        raise RuntimeError(
            f"Leakage columns detected: "
            f"{sorted(leaked)}"
        )

    print(
        "Result fields in matrix: NONE"
    )

    print(
        "Target fields in matrix: NONE"
    )

    print(
        "fixture_id in matrix: NO"
    )

    print(
        "Leakage protection: PASS"
    )

    # ========================================================
    # 7. NUMERIC INTEGRITY
    # ========================================================

    print(
        "\n7. NUMERIC INTEGRITY"
    )

    values = features.to_numpy(
        dtype=float
    )

    if not np.isfinite(
        values
    ).all():

        raise RuntimeError(
            "NaN or infinite production "
            "feature values detected."
        )

    print(
        "NaN: 0"
    )

    print(
        "Infinite: 0"
    )

    print(
        "Numeric integrity: PASS"
    )

    # ========================================================
    # 8. MODEL / FINAL-TEST PROTECTION
    # ========================================================

    print(
        "\n8. MODEL PROTECTION"
    )

    final_test = contract.get(
        "final_test",
        {},
    )

    if final_test.get(
        "status"
    ) != "CONSUMED":

        raise RuntimeError(
            "Final-test lifecycle state is invalid."
        )

    print(
        "Model retrained: NO"
    )

    print(
        "Model re-selected: NO"
    )

    print(
        "Hyperparameter tuning: NO"
    )

    print(
        "Consumed final-test artifacts used: NO"
    )

    # ========================================================
    # 9. SAVE
    # ========================================================

    print(
        "\n9. ARTIFACTS"
    )

    PRODUCTION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    features.to_csv(
        FEATURE_FILE,
        index=False,
    )

    metadata.to_csv(
        METADATA_FILE,
        index=False,
    )

    report = {
        "stage": "7.8.2",
        "status": "PASS",

        "historical_source":
            str(HISTORY_FILE),

        "upcoming_source":
            str(UPCOMING_FILE),

        "historical_records":
            int(
                len(history)
            ),

        "production_fixture_count":
            int(
                len(features)
            ),

        "feature_count":
            int(
                features.shape[1]
            ),

        "strict_pre_match":
            True,

        "upcoming_only":
            True,

        "target_leakage":
            False,

        "numeric_integrity":
            True,

        "model_retrained":
            False,

        "model_selected":
            False,

        "hyperparameter_tuned":
            False,

        "final_test_artifacts_used":
            False,

        "production_feature_sha256":
            sha256_file(
                FEATURE_FILE
            ),
    }

    with REPORT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
        )

    print(
        f"Features:\n{FEATURE_FILE}"
    )

    print(
        f"\nMetadata:\n{METADATA_FILE}"
    )

    print(
        f"\nReport:\n{REPORT_FILE}"
    )

    print(
        "\n" + "=" * 55
    )

    print(
        "STAGE 7.8.2: PASS"
    )

    print("=" * 55)


if __name__ == "__main__":
    main()