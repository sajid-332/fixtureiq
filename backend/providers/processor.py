"""
FixtureIQ Processed Fixture Dataset Processor.

Stage 7.2.3 - 7.2.4

7.2.3:
    Convert normalized fixture records into a clean
    processed CSV dataset.

7.2.4:
    Safely merge new fixture records with an existing
    processed dataset using fixture_id as the stable key.

The processor does not modify Stage 1-6 datasets.
"""

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from backend.providers.normalizer import normalize_fixtures
from backend.providers.validators import validate_fixtures


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = (
    BASE_DIR
    / "data"
    / "processed"
)

FIXTURES_FILE = (
    PROCESSED_DIR
    / "fixtures.csv"
)


# ============================================================
# Dataset schema
# ============================================================

FIXTURE_COLUMNS = [
    "fixture_id",
    "date",
    "timestamp",
    "timezone",
    "status_short",
    "status_long",
    "status_elapsed",
    "league_id",
    "league_name",
    "country",
    "season",
    "round",
    "home_team_id",
    "home_team_name",
    "home_team_code",
    "away_team_id",
    "away_team_name",
    "away_team_code",
    "home_goals",
    "away_goals",
]


# ============================================================
# Record conversion
# ============================================================

def fixture_to_row(
    fixture: Dict,
) -> Dict:
    """
    Convert one normalized fixture into a flat dataset row.
    """

    status = fixture.get(
        "status",
        {},
    )

    league = fixture.get(
        "league",
        {},
    )

    home_team = fixture.get(
        "home_team",
        {},
    )

    away_team = fixture.get(
        "away_team",
        {},
    )

    goals = fixture.get(
        "goals",
        {},
    )

    return {
        "fixture_id":
            fixture.get("fixture_id"),

        "date":
            fixture.get("date"),

        "timestamp":
            fixture.get("timestamp"),

        "timezone":
            fixture.get("timezone"),

        "status_short":
            status.get("short"),

        "status_long":
            status.get("long"),

        "status_elapsed":
            status.get("elapsed"),

        "league_id":
            league.get("id"),

        "league_name":
            league.get("name"),

        "country":
            league.get("country"),

        "season":
            league.get("season"),

        "round":
            league.get("round"),

        "home_team_id":
            home_team.get("id"),

        "home_team_name":
            home_team.get("name"),

        "home_team_code":
            home_team.get("code"),

        "away_team_id":
            away_team.get("id"),

        "away_team_name":
            away_team.get("name"),

        "away_team_code":
            away_team.get("code"),

        "home_goals":
            goals.get("home"),

        "away_goals":
            goals.get("away"),
    }


# ============================================================
# Normalize + validate
# ============================================================

def prepare_fixtures(
    payload: Dict,
) -> pd.DataFrame:
    """
    Normalize and validate an API-Football fixture payload.

    Invalid records are excluded.
    """

    normalized = normalize_fixtures(
        payload
    )

    validation = validate_fixtures(
        normalized
    )

    if not validation["valid"]:

        valid_fixtures = []

        for fixture in normalized:

            result = validate_fixture_safely(
                fixture
            )

            if result:

                valid_fixtures.append(
                    fixture
                )

        normalized = valid_fixtures

    rows = [
        fixture_to_row(
            fixture
        )
        for fixture in normalized
    ]

    dataframe = pd.DataFrame(
        rows,
        columns=FIXTURE_COLUMNS,
    )

    return clean_dataframe(
        dataframe
    )


def validate_fixture_safely(
    fixture: Dict,
) -> bool:
    """
    Validate an individual normalized fixture.

    Kept local to avoid changing the existing validator API.
    """

    from backend.providers.validators import (
        validate_fixture,
    )

    result = validate_fixture(
        fixture
    )

    return bool(
        result.get("valid")
    )


# ============================================================
# Data cleaning
# ============================================================

def clean_dataframe(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Clean and standardize the processed fixture dataset.
    """

    if dataframe.empty:

        return pd.DataFrame(
            columns=FIXTURE_COLUMNS
        )

    dataframe = dataframe.copy()

    # Ensure all expected columns exist.

    for column in FIXTURE_COLUMNS:

        if column not in dataframe.columns:

            dataframe[column] = None

    dataframe = dataframe[
        FIXTURE_COLUMNS
    ]

    # Stable fixture identifier.

    dataframe = dataframe.dropna(
        subset=["fixture_id"]
    )

    dataframe["fixture_id"] = (
        pd.to_numeric(
            dataframe["fixture_id"],
            errors="coerce",
        )
    )

    dataframe = dataframe.dropna(
        subset=["fixture_id"]
    )

    dataframe["fixture_id"] = (
        dataframe["fixture_id"]
        .astype("int64")
    )

    # Remove duplicate fixture IDs.

    dataframe = (
        dataframe
        .drop_duplicates(
            subset=["fixture_id"],
            keep="last",
        )
    )

    # Standardize dates.

    dataframe["date"] = pd.to_datetime(
        dataframe["date"],
        errors="coerce",
        utc=True,
    )

    # Sort chronologically.

    dataframe = (
        dataframe
        .sort_values(
            by=[
                "date",
                "fixture_id",
            ],
            na_position="last",
        )
        .reset_index(
            drop=True
        )
    )

    return dataframe


# ============================================================
# Save dataset
# ============================================================

def save_processed_fixtures(
    dataframe: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Save the processed fixture dataset.
    """

    if output_path is None:

        output_path = FIXTURES_FILE

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe = clean_dataframe(
        dataframe
    )

    dataframe.to_csv(
        output_path,
        index=False,
    )

    return output_path


# ============================================================
# Load dataset
# ============================================================

def load_processed_fixtures(
    input_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Load the existing processed fixture dataset.
    """

    if input_path is None:

        input_path = FIXTURES_FILE

    input_path = Path(
        input_path
    )

    if not input_path.exists():

        return pd.DataFrame(
            columns=FIXTURE_COLUMNS
        )

    dataframe = pd.read_csv(
        input_path
    )

    return clean_dataframe(
        dataframe
    )


# ============================================================
# Incremental merge
# ============================================================

def merge_fixture_datasets(
    existing: pd.DataFrame,
    incoming: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge incoming fixtures with existing fixtures.

    fixture_id is the stable unique key.

    New fixtures are added.
    Existing fixtures are replaced by the newest record.
    Duplicate fixture IDs are removed.
    """

    existing = clean_dataframe(
        existing
    )

    incoming = clean_dataframe(
        incoming
    )

    if existing.empty:

        return incoming

    if incoming.empty:

        return existing

    combined = pd.concat(
        [
            existing,
            incoming,
        ],
        ignore_index=True,
    )

    combined = (
        combined
        .drop_duplicates(
            subset=["fixture_id"],
            keep="last",
        )
    )

    return clean_dataframe(
        combined
    )


def update_processed_fixtures(
    incoming: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> Dict:
    """
    Incrementally update the processed fixture dataset.

    Returns statistics about the update.
    """

    if output_path is None:

        output_path = FIXTURES_FILE

    existing = load_processed_fixtures(
        output_path
    )

    incoming = clean_dataframe(
        incoming
    )

    existing_ids = set(
        existing["fixture_id"].tolist()
    )

    incoming_ids = set(
        incoming["fixture_id"].tolist()
    )

    new_ids = (
        incoming_ids
        - existing_ids
    )

    updated_ids = (
        incoming_ids
        & existing_ids
    )

    merged = merge_fixture_datasets(
        existing,
        incoming,
    )

    save_processed_fixtures(
        merged,
        output_path,
    )

    return {
        "existing_count":
            len(existing),

        "incoming_count":
            len(incoming),

        "new_count":
            len(new_ids),

        "updated_count":
            len(updated_ids),

        "final_count":
            len(merged),

        "duplicate_free":
            (
                merged["fixture_id"]
                .is_unique
            ),
    }