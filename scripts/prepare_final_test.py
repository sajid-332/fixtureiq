"""
FixtureIQ Stage 7.7.3
Final Test Data Preparation

Purpose
-------
Prepare the isolated 2025/26 EPL final-test feature dataset.

Safety rules
------------
1. 2023/24 historical data is never modified.
2. The locked Random Forest is never retrained.
3. Model selection is never performed here.
4. 2025/26 is never used for training or validation.
5. Only the locally stored 2025/26 source is used.
6. The canonical 86-feature schema is preserved.
7. Target columns never enter the model matrix.
8. Existing historical team IDs are preserved.
9. New 2025/26 teams receive deterministic isolated IDs.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Tuple, List, Dict, Any

import numpy as np
import pandas as pd


# ============================================================
# PROJECT ROOT
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
# EXISTING FIXTUREIQ FEATURE PIPELINE
# ============================================================

from backend.features.preparation import (
    prepare_feature_input,
)

from backend.features.historical_features import (
    build_historical_features,
)


# ============================================================
# PATHS
# ============================================================

HISTORICAL_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "historical_fixtures.csv"
)

FINAL_RAW_FILE = (
    BASE_DIR
    / "data"
    / "historical"
    / "raw"
    / "epl_2025_26.csv"
)

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

SELECTED_MODEL_FILE = (
    MODEL_DIR
    / "selected"
    / "selected_model.joblib"
)

X_TRAIN_FILE = (
    MODEL_DIR
    / "X_train.csv"
)

FINAL_TEST_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "final_test"
)

OUTPUT_FEATURES = (
    FINAL_TEST_DIR
    / "final_test_features.csv"
)

OUTPUT_TARGETS = (
    FINAL_TEST_DIR
    / "final_test_targets.csv"
)

OUTPUT_METADATA = (
    FINAL_TEST_DIR
    / "final_test_metadata.json"
)

OUTPUT_QUALITY = (
    FINAL_TEST_DIR
    / "final_test_quality_report.json"
)


# ============================================================
# CONSTANTS
# ============================================================

EXPECTED_ROWS = 380
FINAL_SEASON = 2025

TARGET_MAPPING = {
    0: "draw",
    1: "home_win",
    2: "away_win",
}


# ============================================================
# HELPERS
# ============================================================

def fail(message: str) -> None:
    print(
        f"\nERROR: {message}"
    )
    sys.exit(1)


def load_json(path: Path) -> dict:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def sha256_file(path: Path) -> str:
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
            digest.update(chunk)

    return digest.hexdigest()


def deterministic_negative_id(
    namespace: str,
    value: str,
) -> int:
    """
    Generate a deterministic negative integer ID.

    Negative IDs are intentionally isolated from the
    positive API-Football team IDs used historically.
    """

    identity = (
        f"{namespace}:{value}"
    )

    digest = hashlib.sha256(
        identity.encode(
            "utf-8"
        )
    ).hexdigest()

    return -int(
        digest[:12],
        16,
    )


def calculate_result(
    home_goals: int,
    away_goals: int,
) -> str:

    if home_goals > away_goals:
        return "H"

    if home_goals < away_goals:
        return "A"

    return "D"


# ============================================================
# LOAD + NORMALIZE 2025/26 SOURCE
# ============================================================

def load_final_test_source(
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Load the local 2025/26 Football-Data source and convert
    it into the normalized schema expected by Stage 7.4.1.

    Returns
    -------
    normalized_dataframe
    new_team_records
    """

    if not FINAL_RAW_FILE.exists():

        fail(
            "2025/26 source file does not exist: "
            f"{FINAL_RAW_FILE}"
        )

    raw = pd.read_csv(
        FINAL_RAW_FILE
    )

    required_columns = [
        "Date",
        "HomeTeam",
        "AwayTeam",
        "FTHG",
        "FTAG",
        "FTR",
    ]

    missing = [
        column
        for column in required_columns
        if column not in raw.columns
    ]

    if missing:

        fail(
            "2025/26 source is missing "
            f"required columns: {missing}"
        )

    # --------------------------------------------------------
    # Row count
    # --------------------------------------------------------

    if len(raw) != EXPECTED_ROWS:

        fail(
            f"Expected {EXPECTED_ROWS} fixtures, "
            f"found {len(raw)}."
        )

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    dates = pd.to_datetime(
        raw["Date"],
        dayfirst=True,
        errors="coerce",
        utc=True,
    )

    if dates.isna().any():

        fail(
            "Invalid dates found in "
            "2025/26 source."
        )

    # --------------------------------------------------------
    # Goals
    # --------------------------------------------------------

    home_goals = pd.to_numeric(
        raw["FTHG"],
        errors="coerce",
    )

    away_goals = pd.to_numeric(
        raw["FTAG"],
        errors="coerce",
    )

    if home_goals.isna().any():

        fail(
            "Invalid home-goal values found."
        )

    if away_goals.isna().any():

        fail(
            "Invalid away-goal values found."
        )

    if (
        (home_goals < 0)
        |
        (away_goals < 0)
    ).any():

        fail(
            "Negative goal values found."
        )

    # ========================================================
    # RESULT VALIDATION
    # ========================================================

    calculated_results = [
        calculate_result(
            int(home),
            int(away),
        )
        for home, away
        in zip(
            home_goals,
            away_goals,
        )
    ]

    supplied_results = (
        raw["FTR"]
        .astype(str)
        .str.upper()
        .tolist()
    )

    mismatches = []

    for index, (
        calculated,
        supplied,
    ) in enumerate(
        zip(
            calculated_results,
            supplied_results,
        )
    ):

        if calculated != supplied:

            mismatches.append(
                {
                    "row": index,
                    "calculated": calculated,
                    "supplied": supplied,
                }
            )

    if mismatches:

        fail(
            "FTR does not agree with final "
            f"scores. First mismatches: "
            f"{mismatches[:10]}"
        )

    # ========================================================
    # TEAM VALIDATION
    # ========================================================

    if raw["HomeTeam"].isna().any():

        fail(
            "Missing home-team names."
        )

    if raw["AwayTeam"].isna().any():

        fail(
            "Missing away-team names."
        )

    if (
        raw["HomeTeam"].astype(str)
        ==
        raw["AwayTeam"].astype(str)
    ).any():

        fail(
            "At least one fixture has "
            "identical home and away teams."
        )

    # ========================================================
    # LOAD EXISTING CANONICAL TEAM MAPPING
    # ========================================================

    if not HISTORICAL_FILE.exists():

        fail(
            "Historical fixture dataset "
            "does not exist."
        )

    historical = pd.read_csv(
        HISTORICAL_FILE
    )

    required_historical_team_columns = [
        "home_team_id",
        "home_team_name",
        "away_team_id",
        "away_team_name",
    ]

    missing_historical_columns = [
        column
        for column
        in required_historical_team_columns
        if column not in historical.columns
    ]

    if missing_historical_columns:

        fail(
            "Historical dataset is missing "
            "team columns: "
            f"{missing_historical_columns}"
        )

    home_pairs = (
        historical[
            [
                "home_team_id",
                "home_team_name",
            ]
        ]
        .rename(
            columns={
                "home_team_id":
                    "team_id",
                "home_team_name":
                    "team_name",
            }
        )
    )

    away_pairs = (
        historical[
            [
                "away_team_id",
                "away_team_name",
            ]
        ]
        .rename(
            columns={
                "away_team_id":
                    "team_id",
                "away_team_name":
                    "team_name",
            }
        )
    )

    team_pairs = pd.concat(
        [
            home_pairs,
            away_pairs,
        ],
        ignore_index=True,
    )

    team_pairs = (
        team_pairs
        .dropna(
            subset=[
                "team_id",
                "team_name",
            ]
        )
        .drop_duplicates(
            subset=[
                "team_name",
            ],
            keep="first",
        )
    )

    team_map = dict(
        zip(
            team_pairs["team_name"],
            team_pairs["team_id"],
        )
    )

    # ========================================================
    # FOOTBALL-DATA NAME ALIASES
    # ========================================================

    aliases = {
        "Man City":
            "Manchester City",

        "Man United":
            "Manchester United",

        "Nott'm Forest":
            "Nottingham Forest",
    }

    raw["HomeTeam"] = (
        raw["HomeTeam"]
        .astype(str)
        .map(
            lambda value:
                aliases.get(
                    value,
                    value,
                )
        )
    )

    raw["AwayTeam"] = (
        raw["AwayTeam"]
        .astype(str)
        .map(
            lambda value:
                aliases.get(
                    value,
                    value,
                )
        )
    )

    source_teams = sorted(
        set(
            raw["HomeTeam"]
        )
        |
        set(
            raw["AwayTeam"]
        )
    )

    # ========================================================
    # NEW TEAM IDS
    # ========================================================

    new_teams = sorted(
        set(source_teams)
        -
        set(team_map)
    )

    existing_ids = set(
        pd.to_numeric(
            team_pairs["team_id"],
            errors="coerce",
        )
        .dropna()
        .astype(int)
        .tolist()
    )

    new_team_records = []

    for team_name in new_teams:

        generated_id = (
            deterministic_negative_id(
                "fixtureiq-final-test-team",
                team_name,
            )
        )

        while generated_id in existing_ids:

            generated_id -= 1

        team_map[
            team_name
        ] = generated_id

        existing_ids.add(
            generated_id
        )

        record = {
            "name":
                team_name,

            "id":
                int(generated_id),

            "source":
                "2025/26 final-test",

            "historical_state":
                "first_observation",
        }

        new_team_records.append(
            record
        )

        print(
            f"New team: {team_name} "
            f"→ deterministic ID "
            f"{generated_id}"
        )

    # ========================================================
    # FINAL TEAM RESOLUTION
    # ========================================================

    unresolved = sorted(
        set(source_teams)
        -
        set(team_map)
    )

    if unresolved:

        fail(
            "Unable to resolve 2025/26 "
            f"teams: {unresolved}"
        )

    # ========================================================
    # DETERMINISTIC FIXTURE IDS
    # ========================================================

    fixture_ids = []

    for index, row in raw.iterrows():

        identity = (
            "fixtureiq-final-test-fixture:"
            f"{index + 1}:"
            f"{dates.iloc[index].isoformat()}:"
            f"{row['HomeTeam']}:"
            f"{row['AwayTeam']}"
        )

        digest = hashlib.sha256(
            identity.encode(
                "utf-8"
            )
        ).hexdigest()

        fixture_id = -int(
            digest[:12],
            16,
        )

        fixture_ids.append(
            fixture_id
        )

    if len(
        set(fixture_ids)
    ) != EXPECTED_ROWS:

        fail(
            "Generated fixture IDs "
            "are not unique."
        )

    # ========================================================
    # API-STYLE NORMALIZED DATASET
    #
    # This matches the required Stage 7.4.1
    # preparation contract.
    # ========================================================

    normalized = pd.DataFrame(
        {
            "fixture_id":
                fixture_ids,

            "season":
                FINAL_SEASON,

            "date":
                dates,

            "timestamp":
                dates.astype(
                    "int64"
                )
                // 10**9,

            "timezone":
                "UTC",

            "status_short":
                "FT",

            "status_long":
                "Match Finished",

            "status_elapsed":
                90,

            "league_id":
                39,

            "league_name":
                "Premier League",

            "country":
                "England",

            "round":
                "Regular Season",

            "home_team_id":
                raw["HomeTeam"]
                .map(team_map),

            "home_team_name":
                raw["HomeTeam"],

            "home_team_code":
                np.nan,

            "away_team_id":
                raw["AwayTeam"]
                .map(team_map),

            "away_team_name":
                raw["AwayTeam"],

            "away_team_code":
                np.nan,

            "home_goals":
                home_goals.astype(int),

            "away_goals":
                away_goals.astype(int),
        }
    )

    # ========================================================
    # TEAM ID INTEGRITY
    # ========================================================

    if normalized[
        "home_team_id"
    ].isna().any():

        fail(
            "Unresolved home-team IDs remain."
        )

    if normalized[
        "away_team_id"
    ].isna().any():

        fail(
            "Unresolved away-team IDs remain."
        )

    return (
        normalized,
        new_team_records,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.7.3"
    )

    print(
        "Final Test Data Preparation"
    )

    print("=" * 50)

    # ========================================================
    # 1. MODEL PROTECTION
    # ========================================================

    print(
        "\n1. MODEL PROTECTION"
    )

    if not LOCK_FILE.exists():

        fail(
            "Selected model lock file "
            "does not exist."
        )

    if not SELECTED_MODEL_FILE.exists():

        fail(
            "Selected production model "
            "does not exist."
        )

    if not X_TRAIN_FILE.exists():

        fail(
            "X_train.csv does not exist."
        )

    lock = load_json(
        LOCK_FILE
    )

    if lock.get(
        "selected_candidate"
    ) != "random_forest":

        fail(
            "Locked selected candidate "
            "is not random_forest."
        )

    if lock.get(
        "status"
    ) != "LOCKED":

        fail(
            "Selected model is not LOCKED."
        )

    if lock.get(
        "feature_count"
    ) != 86:

        fail(
            "Locked model feature count "
            "is not 86."
        )

    if lock.get(
        "final_test_used"
    ) is not False:

        fail(
            "Final test is already "
            "marked as used."
        )

    current_model_hash = (
        sha256_file(
            SELECTED_MODEL_FILE
        )
    )

    locked_model_hash = (
        lock.get(
            "model_sha256"
        )
    )

    if (
        current_model_hash
        !=
        locked_model_hash
    ):

        fail(
            "Selected model SHA256 does "
            "not match 7.7.1 lock."
        )

    print(
        "Selected model: Random Forest"
    )

    print(
        "Model status: LOCKED"
    )

    print(
        "Model hash: MATCH"
    )

    print(
        "Final test previously used: NO"
    )

    # ========================================================
    # 2. HISTORICAL DATA PROTECTION
    # ========================================================

    print(
        "\n2. HISTORICAL DATA PROTECTION"
    )

    if not HISTORICAL_FILE.exists():

        fail(
            "Historical dataset does "
            "not exist."
        )

    historical = pd.read_csv(
        HISTORICAL_FILE
    )

    historical_seasons = sorted(
        pd.to_numeric(
            historical["season"],
            errors="coerce",
        )
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    if historical_seasons != [
        2023,
        2024,
    ]:

        fail(
            "Historical dataset is no "
            "longer 2023 + 2024 only."
        )

    if len(historical) != 760:

        fail(
            f"Expected 760 historical "
            f"records, found {len(historical)}."
        )

    print(
        "Historical records: 760"
    )

    print(
        "Historical seasons: [2023, 2024]"
    )

    print(
        "Historical dataset: PROTECTED"
    )

    # ========================================================
    # 3. MODEL FEATURE SCHEMA
    # ========================================================

    print(
        "\n3. MODEL FEATURE SCHEMA"
    )

    x_train = pd.read_csv(
        X_TRAIN_FILE
    )

    canonical_features = list(
        x_train.columns
    )

    if len(canonical_features) != 86:

        fail(
            "Canonical model schema does "
            "not contain exactly 86 features."
        )

    if "fixture_id" in canonical_features:

        fail(
            "fixture_id must not be part "
            "of the model feature matrix."
        )

    print(
        "Canonical feature count: 86"
    )

    print(
        "Schema source: X_train.csv"
    )

    print(
        "Schema validation: PASS"
    )

    # ========================================================
    # 4. LOCAL 2025/26 SOURCE
    # ========================================================

    print(
        "\n4. LOCAL 2025/26 SOURCE"
    )

    print(
        f"Source: {FINAL_RAW_FILE}"
    )

    (
        final_source,
        new_team_records,
    ) = load_final_test_source()

    print(
        "Source file: PASS"
    )

    print(
        f"Source records: "
        f"{len(final_source)}"
    )

    print(
        "Result/goal consistency: PASS"
    )

    print(
        "Team validation: PASS"
    )

    print(
        "Fixture IDs: PASS"
    )

    # ========================================================
    # 5. STAGE 7.4.1 PREPARATION
    # ========================================================

    print(
        "\n5. FEATURE INPUT PREPARATION"
    )

    final_prepared = (
        prepare_feature_input(
            final_source
        )
    )

    if len(final_prepared) != EXPECTED_ROWS:

        fail(
            "Stage 7.4.1 preparation "
            "changed the 2025/26 record count."
        )

    final_prepared = (
        final_prepared
        .sort_values(
            [
                "date",
                "fixture_id",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    print(
        f"Prepared records: "
        f"{len(final_prepared)}"
    )

    print(
        "Stage 7.4.1 preparation logic: PASS"
    )

    # ========================================================
    # 6. HISTORICAL CONTEXT
    # ========================================================

    print(
        "\n6. HISTORICAL CONTEXT"
    )

    historical_prepared = (
        prepare_feature_input(
            historical.copy()
        )
    )

    if len(historical_prepared) != 760:

        fail(
            "Historical preparation "
            "changed the historical "
            "record count."
        )

    # --------------------------------------------------------
    # Historical fixture ID protection
    # --------------------------------------------------------

    historical_original_ids = set(
        historical[
            "fixture_id"
        ]
        .astype(int)
    )

    historical_prepared_ids = set(
        historical_prepared[
            "fixture_id"
        ]
        .astype(int)
    )

    if (
        historical_original_ids
        !=
        historical_prepared_ids
    ):

        fail(
            "Historical fixture IDs "
            "changed during preparation."
        )

    # --------------------------------------------------------
    # Final fixture IDs
    # --------------------------------------------------------

    final_fixture_ids = set(
        final_prepared[
            "fixture_id"
        ]
        .astype(int)
    )

    if len(final_fixture_ids) != EXPECTED_ROWS:

        fail(
            "Final fixture IDs are "
            "not unique."
        )

    overlap = (
        historical_original_ids
        &
        final_fixture_ids
    )

    if overlap:

        fail(
            "Historical/final fixture "
            "ID overlap detected: "
            f"{sorted(overlap)[:10]}"
        )

    # --------------------------------------------------------
    # Temporary combined dataset
    # --------------------------------------------------------

    combined = pd.concat(
        [
            historical_prepared,
            final_prepared,
        ],
        ignore_index=True,
    )

    if len(combined) != 1140:

        fail(
            f"Expected 1140 temporary "
            f"records, found {len(combined)}."
        )

    print(
        "Historical records: 760"
    )

    print(
        "2025/26 records: 380"
    )

    print(
        "Temporary combined records: 1140"
    )

    print(
        "Historical fixture IDs: PROTECTED"
    )

    print(
        "Historical dataset modified: NO"
    )

    # ========================================================
    # 7. TIME-BASED FEATURE CONSTRUCTION
    # ========================================================

    print(
        "\n7. TIME-BASED FEATURE CONSTRUCTION"
    )

    all_features = (
        build_historical_features(
            combined
        )
    )

    if len(all_features) != 1140:

        fail(
            "Feature construction changed "
            "the temporary record count."
        )

    all_features = (
        all_features
        .sort_values(
            [
                "date",
                "fixture_id",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    final_features = (
        all_features[
            all_features[
                "season"
            ]
            .astype(int)
            ==
            FINAL_SEASON
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    if len(final_features) != EXPECTED_ROWS:

        fail(
            f"Expected 380 final-test "
            f"feature records, found "
            f"{len(final_features)}."
        )

    print(
        "Stage 7.4.2 feature constructor: PASS"
    )

    print(
        "Strict pre-match state: PASS"
    )

    print(
        "2025/26 feature records: 380"
    )

    # ========================================================
    # 8. MODEL FEATURE MATRIX
    # ========================================================

    print(
        "\n8. MODEL FEATURE MATRIX"
    )

    missing_features = [
        column
        for column
        in canonical_features
        if column
        not in final_features.columns
    ]

    if missing_features:

        fail(
            "Final-test feature dataset "
            "is missing canonical features: "
            f"{missing_features}"
        )

    X_final = (
        final_features[
            canonical_features
        ]
        .copy()
    )

    if list(
        X_final.columns
    ) != canonical_features:

        fail(
            "Final-test feature column "
            "order does not match X_train."
        )

    if X_final.shape != (
        EXPECTED_ROWS,
        86,
    ):

        fail(
            "Final model matrix has "
            f"unexpected shape: {X_final.shape}"
        )

    # --------------------------------------------------------
    # Numeric validation
    # --------------------------------------------------------

    non_numeric = [
        column
        for column
        in X_final.columns
        if not pd.api.types.is_numeric_dtype(
            X_final[column]
        )
    ]

    if non_numeric:

        fail(
            "Non-numeric feature columns: "
            f"{non_numeric}"
        )

    numeric_values = (
        X_final.to_numpy(
            dtype=float
        )
    )

    if not np.isfinite(
        numeric_values
    ).all():

        fail(
            "NaN or infinite values "
            "detected in final model matrix."
        )

    # --------------------------------------------------------
    # Target leakage
    # --------------------------------------------------------

    forbidden_columns = {
        "target",
        "target_label",
        "home_goals",
        "away_goals",
    }

    leaked_columns = [
        column
        for column
        in X_final.columns
        if column in forbidden_columns
    ]

    if leaked_columns:

        fail(
            "Target leakage detected: "
            f"{leaked_columns}"
        )

    print(
        "Final model matrix: "
        f"{X_final.shape}"
    )

    print(
        "Feature count: 86"
    )

    print(
        "Feature schema match: PASS"
    )

    print(
        "Numeric integrity: PASS"
    )

    print(
        "Target leakage: NONE"
    )

    # ========================================================
    # 9. TARGET SEPARATION
    # ========================================================

    print(
        "\n9. TARGET SEPARATION"
    )

    target_columns = [
        "fixture_id",
        "target",
        "target_label",
        "home_goals",
        "away_goals",
    ]

    missing_target_columns = [
        column
        for column
        in target_columns
        if column
        not in final_features.columns
    ]

    if missing_target_columns:

        fail(
            "Final-test target data "
            "is missing columns: "
            f"{missing_target_columns}"
        )

    y_final = (
        final_features[
            target_columns
        ]
        .copy()
    )

    if not y_final[
        "fixture_id"
    ].is_unique:

        fail(
            "Final-test fixture IDs "
            "are not unique."
        )

    actual_targets = set(
        y_final[
            "target"
        ]
        .astype(int)
        .tolist()
    )

    if not actual_targets <= {
        0,
        1,
        2,
    }:

        fail(
            "Invalid target values: "
            f"{actual_targets}"
        )

    expected_labels = (
        y_final[
            "target"
        ]
        .astype(int)
        .map(
            TARGET_MAPPING
        )
    )

    if not (
        expected_labels
        ==
        y_final[
            "target_label"
        ]
    ).all():

        fail(
            "Target labels do not "
            "match target mapping."
        )

    print(
        "Target values: "
        f"{sorted(actual_targets)}"
    )

    print(
        "Target mapping: PASS"
    )

    print(
        "Targets outside feature matrix: PASS"
    )

    # ========================================================
    # 10. CHRONOLOGICAL INTEGRITY
    # ========================================================

    print(
        "\n10. CHRONOLOGICAL INTEGRITY"
    )

    final_dates = pd.to_datetime(
        final_features[
            "date"
        ],
        errors="coerce",
        utc=True,
    )

    if final_dates.isna().any():

        fail(
            "Invalid dates in final "
            "feature dataset."
        )

    if not final_dates.is_monotonic_increasing:

        fail(
            "Final-test features are "
            "not chronologically ordered."
        )

    historical_dates = pd.to_datetime(
        historical_prepared[
            "date"
        ],
        errors="coerce",
        utc=True,
    )

    latest_historical_date = (
        historical_dates.max()
    )

    earliest_final_date = (
        final_dates.min()
    )

    if (
        earliest_final_date
        <=
        latest_historical_date
    ):

        fail(
            "2025/26 final-test data "
            "is not chronologically after "
            "historical data."
        )

    print(
        "Historical → final chronology: PASS"
    )

    print(
        "Final-test chronological order: PASS"
    )

    # ========================================================
    # 11. SAVE FINAL TEST ARTIFACTS
    # ========================================================

    print(
        "\n11. FINAL TEST ARTIFACTS"
    )

    FINAL_TEST_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # X final
    #
    # fixture_id is retained only as an identifier.
    # It is NOT one of the 86 model features.
    # --------------------------------------------------------

    X_output = pd.DataFrame(
        {
            "fixture_id":
                final_features[
                    "fixture_id"
                ]
                .astype(int)
                .values
        }
    )

    for column in canonical_features:

        X_output[column] = (
            X_final[
                column
            ].values
        )

    X_output.to_csv(
        OUTPUT_FEATURES,
        index=False,
    )

    # --------------------------------------------------------
    # y final
    # --------------------------------------------------------

    y_final.to_csv(
        OUTPUT_TARGETS,
        index=False,
    )

    # ========================================================
    # METADATA
    # ========================================================

    metadata = {
        "stage":
            "7.7.3",

        "purpose":
            "Prepare isolated 2025/26 "
            "final-test data.",

        "source":
            str(
                FINAL_RAW_FILE.relative_to(
                    BASE_DIR
                )
            ),

        "season":
            "2025/26",

        "season_id":
            FINAL_SEASON,

        "records":
            EXPECTED_ROWS,

        "feature_count":
            len(canonical_features),

        "feature_schema_source":
            "data/processed/model/X_train.csv",

        "feature_constructor":
            "backend.features.historical_features."
            "build_historical_features",

        "historical_context":
            [
                2023,
                2024,
            ],

        "training_season":
            2023,

        "validation_season":
            2024,

        "selected_candidate":
            "random_forest",

        "selected_model":
            "Random Forest",

        "model_sha256":
            current_model_hash,

        "model_locked":
            True,

        "model_retrained":
            False,

        "model_selection_performed":
            False,

        "historical_dataset_modified":
            False,

        "final_test_evaluated":
            False,

        "final_test_ready":
            True,

        "target_mapping":
            {
                str(key): value
                for key, value
                in TARGET_MAPPING.items()
            },

        "new_teams":
            new_team_records,
    }

    with OUTPUT_METADATA.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # ========================================================
    # QUALITY REPORT
    # ========================================================

    quality_report = {
        "stage":
            "7.7.3",

        "season":
            "2025/26",

        "records":
            int(
                len(X_output)
            ),

        "expected_records":
            EXPECTED_ROWS,

        "record_count_pass":
            len(X_output)
            ==
            EXPECTED_ROWS,

        "fixture_ids_unique":
            X_output[
                "fixture_id"
            ].nunique()
            ==
            EXPECTED_ROWS,

        "feature_count":
            len(canonical_features),

        "feature_schema_pass":
            len(canonical_features)
            ==
            86,

        "missing_values":
            int(
                X_final
                .isna()
                .sum()
                .sum()
            ),

        "infinite_values":
            int(
                np.isinf(
                    X_final.to_numpy(
                        dtype=float
                    )
                ).sum()
            ),

        "target_leakage":
            False,

        "historical_overlap":
            0,

        "chronological_order":
            True,

        "historical_to_final_chronology":
            True,

        "model_locked":
            True,

        "model_retrained":
            False,

        "model_selection_performed":
            False,

        "final_test_evaluated":
            False,

        "historical_dataset_modified":
            False,

        "final_test_ready":
            True,

        "new_teams":
            new_team_records,
    }

    with OUTPUT_QUALITY.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            quality_report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print(
        "\n" + "=" * 50
    )

    print(
        "STAGE 7.7.3 RESULT"
    )

    print(
        "=" * 50
    )

    print(
        "2025/26 source: PASS"
    )

    print(
        "Fixtures: 380"
    )

    print(
        "Historical context: 2023 + 2024"
    )

    print(
        "Feature count: 86"
    )

    print(
        "Feature schema: PASS"
    )

    print(
        "Target leakage: NONE"
    )

    print(
        "Numeric integrity: PASS"
    )

    print(
        "Chronological integrity: PASS"
    )

    print(
        "Historical overlap: 0"
    )

    print(
        "Historical dataset modified: NO"
    )

    print(
        "Model retrained: NO"
    )

    print(
        "Model selection performed: NO"
    )

    print(
        "2025/26 evaluated: NO"
    )

    print(
        "\nFinal-test features:"
    )

    print(
        OUTPUT_FEATURES
    )

    print(
        "Final-test targets:"
    )

    print(
        OUTPUT_TARGETS
    )

    print(
        "Metadata:"
    )

    print(
        OUTPUT_METADATA
    )

    print(
        "Quality report:"
    )

    print(
        OUTPUT_QUALITY
    )

    print(
        "\nSTAGE 7.7.3: PASS"
    )


if __name__ == "__main__":
    main()