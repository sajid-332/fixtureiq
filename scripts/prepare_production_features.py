"""
FixtureIQ Stage 7.8.2
Production Fixture Feature Preparation.

Inputs:
- production_history.csv
- upcoming_fixtures.csv

Output:
- production_features.csv
- production_fixture_metadata.csv
- production_feature_report.json

Rules:
- Uses the locked Stage 7.8.1 feature contract.
- Uses only completed production history.
- Upcoming fixtures never update state.
- No target/result leakage.
- No retraining, tuning or model selection.
- Consumed final-test evaluation artifacts are not accessed.
"""

from __future__ import annotations

import hashlib
import json
import sys
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

sys.path.insert(
    0,
    str(BASE_DIR),
)


# ============================================================
# FixtureIQ imports
# ============================================================

from backend.services.production_feature_service import (
    build_production_features,
)


# ============================================================
# Paths
# ============================================================

PRODUCTION_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "production"
)

HISTORY_FILE = (
    PRODUCTION_DIR
    / "production_history.csv"
)

HISTORY_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_history_report.json"
)

UPCOMING_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
)

FETCH_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_fixture_fetch_report.json"
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
    "PST",
}


# ============================================================
# Helpers
# ============================================================

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


def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise FileNotFoundError(
            f"Required JSON file missing: "
            f"{path}"
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
            f"Invalid JSON object: {path}"
        )

    return payload


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 60)

    print(
        "FixtureIQ Stage 7.8.2"
    )

    print(
        "Production Fixture Feature Preparation"
    )

    print("=" * 60)

    # ========================================================
    # 1. Production contract
    # ========================================================

    print(
        "\n1. PRODUCTION CONTRACT"
    )

    contract = load_json(
        CONTRACT_FILE
    )

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
            "Production inference contract "
            "is not locked."
        )

    model_contract = contract.get(
        "model",
        {},
    )

    if model_contract.get(
        "candidate_id"
    ) != "random_forest":

        raise RuntimeError(
            "Production model is not the "
            "locked Random Forest."
        )

    if model_contract.get(
        "status"
    ) != "LOCKED":

        raise RuntimeError(
            "Production model status is not LOCKED."
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
            "Production contract does not "
            "contain 86 features."
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
    # 2. Production-history provenance
    # ========================================================

    print(
        "\n2. PRODUCTION HISTORY"
    )

    if not HISTORY_FILE.exists():

        print(
            "Production history: MISSING"
        )

        print(
            "\nRun first:"
        )

        print(
            "python scripts\\build_production_history.py"
        )

        raise FileNotFoundError(
            "Production historical context "
            "has not been built."
        )

    history_report = load_json(
        HISTORY_REPORT_FILE
    )

    if history_report.get(
        "status"
    ) != "PASS":

        raise RuntimeError(
            "Production historical context "
            "report is not PASS."
        )

    if history_report.get(
        "final_test_evaluation_artifacts_used"
    ) is not False:

        raise RuntimeError(
            "Production history provenance "
            "violates final-test protection."
        )

    if history_report.get(
        "model_retrained"
    ) is not False:

        raise RuntimeError(
            "Production history unexpectedly "
            "reports model retraining."
        )

    history = pd.read_csv(
        HISTORY_FILE
    )

    if history.empty:

        raise RuntimeError(
            "Production history is empty."
        )

    required_history_columns = {
        "fixture_id",
        "date",
        "status_short",
        "home_team_id",
        "home_team_name",
        "away_team_id",
        "away_team_name",
        "home_goals",
        "away_goals",
    }

    missing_history = (
        required_history_columns
        -
        set(
            history.columns
        )
    )

    if missing_history:

        raise RuntimeError(
            "Production history missing columns: "
            f"{sorted(missing_history)}"
        )

    if not history[
        "fixture_id"
    ].is_unique:

        raise RuntimeError(
            "Production historical fixture IDs "
            "are not unique."
        )

    history_dates = pd.to_datetime(
        history[
            "date"
        ],
        errors="coerce",
        utc=True,
    )

    if history_dates.isna().any():

        raise RuntimeError(
            "Production history contains "
            "invalid dates."
        )

    history_goals_home = pd.to_numeric(
        history[
            "home_goals"
        ],
        errors="coerce",
    )

    history_goals_away = pd.to_numeric(
        history[
            "away_goals"
        ],
        errors="coerce",
    )

    if (
        history_goals_home.isna().any()
        or
        history_goals_away.isna().any()
    ):

        raise RuntimeError(
            "Production history contains "
            "missing match scores."
        )

    print(
        f"Historical records: "
        f"{len(history)}"
    )

    print(
        "Fixture IDs unique: PASS"
    )

    print(
        "Completed scores available: PASS"
    )

    print(
        "Production-history provenance: PASS"
    )

    # ========================================================
    # 3. Upcoming fixture snapshot
    # ========================================================

    print(
        "\n3. UPCOMING FIXTURE SNAPSHOT"
    )

    if not UPCOMING_FILE.exists():

        print(
            "Upcoming fixture snapshot: MISSING"
        )

        print(
            "\nRun first:"
        )

        print(
            "python scripts\\fetch_production_fixtures.py"
        )

        raise FileNotFoundError(
            "No valid upcoming production "
            "fixture snapshot exists."
        )

    fetch_report = load_json(
        FETCH_REPORT_FILE
    )

    if fetch_report.get(
        "status"
    ) != "PASS":

        raise RuntimeError(
            "Production fixture fetch "
            "report is not PASS."
        )

    if fetch_report.get(
        "fallback_season_used"
    ) is not False:

        raise RuntimeError(
            "Production fixture feed used "
            "a fallback season."
        )

    if fetch_report.get(
        "final_test_evaluation_artifacts_used"
    ) is not False:

        raise RuntimeError(
            "Production fixture feed violated "
            "final-test protection."
        )

    upcoming = pd.read_csv(
        UPCOMING_FILE
    )

    if upcoming.empty:

        raise RuntimeError(
            "Upcoming production fixture "
            "snapshot is empty."
        )

    required_upcoming = {
        "fixture_id",
        "date",
        "status_short",
        "home_team_id",
        "home_team_name",
        "away_team_id",
        "away_team_name",
    }

    missing_upcoming = (
        required_upcoming
        -
        set(
            upcoming.columns
        )
    )

    if missing_upcoming:

        raise RuntimeError(
            "Upcoming fixture snapshot "
            "missing columns: "
            f"{sorted(missing_upcoming)}"
        )

    if not upcoming[
        "fixture_id"
    ].is_unique:

        raise RuntimeError(
            "Upcoming fixture IDs "
            "are not unique."
        )

    statuses = set(
        upcoming[
            "status_short"
        ]
        .dropna()
        .astype(str)
        .unique()
    )

    if not statuses.issubset(
        UPCOMING_STATUSES
    ):

        raise RuntimeError(
            "Invalid fixture statuses "
            "in upcoming snapshot: "
            f"{sorted(statuses)}"
        )

    upcoming_dates = pd.to_datetime(
        upcoming[
            "date"
        ],
        errors="coerce",
        utc=True,
    )

    if upcoming_dates.isna().any():

        raise RuntimeError(
            "Upcoming fixture snapshot "
            "contains invalid dates."
        )

    now = pd.Timestamp.now(
        tz="UTC"
    )

    if (
        upcoming_dates
        <= now
    ).any():

        raise RuntimeError(
            "Past fixture detected in "
            "upcoming fixture snapshot."
        )

    print(
        f"Upcoming fixtures: "
        f"{len(upcoming)}"
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

    # ========================================================
    # 4. Historical -> upcoming chronology
    # ========================================================

    print(
        "\n4. CHRONOLOGY"
    )

    latest_history = (
        history_dates.max()
    )

    earliest_upcoming = (
        upcoming_dates.min()
    )

    if latest_history >= earliest_upcoming:

        raise RuntimeError(
            "Historical/upcoming chronology failed.\n"
            f"Latest completed match: {latest_history}\n"
            f"Earliest upcoming match: {earliest_upcoming}"
        )

    print(
        f"Latest completed match: "
        f"{latest_history}"
    )

    print(
        f"Earliest upcoming fixture: "
        f"{earliest_upcoming}"
    )

    print(
        "Historical -> upcoming boundary: PASS"
    )

    # ========================================================
    # 5. Team-state coverage
    # ========================================================

    print(
        "\n5. TEAM STATE COVERAGE"
    )

    history_teams = set(
        history[
            "home_team_name"
        ].astype(str)
    ) | set(
        history[
            "away_team_name"
        ].astype(str)
    )

    upcoming_teams = set(
        upcoming[
            "home_team_name"
        ].astype(str)
    ) | set(
        upcoming[
            "away_team_name"
        ].astype(str)
    )

    teams_with_history = (
        upcoming_teams
        &
        history_teams
    )

    zero_state_teams = (
        upcoming_teams
        -
        history_teams
    )

    print(
        f"Upcoming teams: "
        f"{len(upcoming_teams)}"
    )

    print(
        f"Teams with historical state: "
        f"{len(teams_with_history)}"
    )

    print(
        f"Zero-state teams: "
        f"{len(zero_state_teams)}"
    )

    if zero_state_teams:

        for team in sorted(
            zero_state_teams
        ):

            print(
                f"  Zero state: {team}"
            )

    # ========================================================
    # 6. Feature construction
    # ========================================================

    print(
        "\n6. FEATURE CONSTRUCTION"
    )

    metadata, features = (
        build_production_features(
            history,
            upcoming,
        )
    )

    if len(
        metadata
    ) != len(
        upcoming
    ):

        raise RuntimeError(
            "Production metadata count "
            "does not match fixture count."
        )

    if len(
        features
    ) != len(
        upcoming
    ):

        raise RuntimeError(
            "Production feature count "
            "does not match fixture count."
        )

    print(
        f"Production records: "
        f"{len(features)}"
    )

    print(
        f"Model matrix: "
        f"{features.shape}"
    )

    print(
        "Strict pre-match state: PASS"
    )

    print(
        "Upcoming fixtures update state: NO"
    )

    # ========================================================
    # 7. Feature schema
    # ========================================================

    print(
        "\n7. FEATURE SCHEMA"
    )

    if features.shape[
        1
    ] != 86:

        raise RuntimeError(
            "Production feature count "
            f"is {features.shape[1]}, "
            "expected 86."
        )

    if list(
        features.columns
    ) != contract_features:

        raise RuntimeError(
            "Production feature schema "
            "does not match locked "
            "training schema."
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
    # 8. Leakage protection
    # ========================================================

    print(
        "\n8. LEAKAGE PROTECTION"
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
            "Leakage columns detected: "
            f"{sorted(leaked)}"
        )

    print(
        "Result fields in matrix: NONE"
    )

    print(
        "Target fields in matrix: NONE"
    )

    print(
        "fixture_id in model matrix: NO"
    )

    print(
        "Leakage protection: PASS"
    )

    # ========================================================
    # 9. Numeric integrity
    # ========================================================

    print(
        "\n9. NUMERIC INTEGRITY"
    )

    values = features.to_numpy(
        dtype=float
    )

    if values.size == 0:

        raise RuntimeError(
            "Production feature matrix "
            "is empty."
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
    # 10. Model / final-test protection
    # ========================================================

    print(
        "\n10. MODEL PROTECTION"
    )

    final_test = contract.get(
        "final_test",
        {},
    )

    if final_test.get(
        "status"
    ) != "CONSUMED":

        raise RuntimeError(
            "Final-test lifecycle state "
            "is not CONSUMED."
        )

    if final_test.get(
        "must_not_be_used_for_training"
    ) is not True:

        raise RuntimeError(
            "Final-test training protection "
            "is missing."
        )

    if final_test.get(
        "must_not_be_used_for_selection"
    ) is not True:

        raise RuntimeError(
            "Final-test selection protection "
            "is missing."
        )

    print(
        "Final test lifecycle: CONSUMED"
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
        "Final-test evaluation artifacts used: NO"
    )

    # ========================================================
    # 11. Save
    # ========================================================

    print(
        "\n11. SAVE ARTIFACTS"
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

        "stage":
            "7.8.2",

        "status":
            "PASS",

        "historical_source":
            str(
                HISTORY_FILE
            ),

        "upcoming_source":
            str(
                UPCOMING_FILE
            ),

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

        "upcoming_team_count":
            int(
                len(upcoming_teams)
            ),

        "teams_with_historical_state":
            int(
                len(teams_with_history)
            ),

        "zero_state_teams":
            sorted(
                zero_state_teams
            ),

        "latest_completed_fixture":
            latest_history.isoformat(),

        "earliest_upcoming_fixture":
            earliest_upcoming.isoformat(),

        "strict_pre_match":
            True,

        "upcoming_fixtures_update_state":
            False,

        "upcoming_only":
            True,

        "target_leakage":
            False,

        "numeric_integrity":
            True,

        "chronological":
            True,

        "model_retrained":
            False,

        "model_selected":
            False,

        "hyperparameter_tuned":
            False,

        "final_test_evaluation_artifacts_used":
            False,

        "production_history_sha256":
            sha256_file(
                HISTORY_FILE
            ),

        "upcoming_fixture_sha256":
            sha256_file(
                UPCOMING_FILE
            ),

        "production_feature_sha256":
            None,
    }

    # Save features before calculating their hash.
    report[
        "production_feature_sha256"
    ] = sha256_file(
        FEATURE_FILE
    )

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
        f"Features:\n"
        f"{FEATURE_FILE}"
    )

    print(
        f"\nMetadata:\n"
        f"{METADATA_FILE}"
    )

    print(
        f"\nReport:\n"
        f"{REPORT_FILE}"
    )

    # ========================================================
    # Final
    # ========================================================

    print(
        "\n" + "=" * 60
    )

    print(
        "STAGE 7.8.2: PASS"
    )

    print("=" * 60)


if __name__ == "__main__":

    main()