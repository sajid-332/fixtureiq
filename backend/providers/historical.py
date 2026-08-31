"""
FixtureIQ Stage 7.3.1 - 7.3.2
Historical Fixture Data Management.

7.3.1:
    Process and ingest a specific historical season.

7.3.2:
    Maintain a multi-season historical fixture dataset
    with safe incremental updates and duplicate prevention.

Production configuration is never modified by this module.
"""

from pathlib import Path
from typing import Dict, Optional, Set

import pandas as pd

from backend.providers.processor import (
    fixture_to_row,
    clean_dataframe,
)


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = (
    BASE_DIR
    / "data"
    / "processed"
)

HISTORICAL_FILE = (
    PROCESSED_DIR
    / "historical_fixtures.csv"
)


# ============================================================
# Historical dataset schema
# ============================================================

HISTORICAL_COLUMNS = [
    "fixture_id",
    "season",
    "date",
    "timestamp",
    "timezone",
    "status_short",
    "status_long",
    "status_elapsed",
    "league_id",
    "league_name",
    "country",
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
# Convert normalized fixture
# ============================================================

def historical_fixture_to_row(
    fixture: Dict,
    season: int,
) -> Dict:
    """
    Convert one normalized fixture into a historical
    dataset row.

    The supplied season is explicitly assigned so that
    historical records cannot accidentally inherit the
    production configuration season.
    """

    row = fixture_to_row(
        fixture
    )

    row["season"] = season

    return {
        column: row.get(column)
        for column in HISTORICAL_COLUMNS
    }


# ============================================================
# Prepare historical fixtures
# ============================================================

def prepare_historical_fixtures(
    payload: Dict,
    season: int,
) -> pd.DataFrame:
    """
    Normalize and validate fixtures for one historical season.
    """

    from backend.providers.normalizer import (
        normalize_fixtures,
    )

    from backend.providers.validators import (
        validate_fixture,
    )

    normalized = normalize_fixtures(
        payload
    )

    valid_fixtures = []

    for fixture in normalized:

        try:

            result = validate_fixture(
                fixture
            )

        except Exception:

            continue

        if (
            isinstance(
                result,
                dict,
            )
            and
            result.get("valid")
        ):

            valid_fixtures.append(
                fixture
            )

    rows = [
        historical_fixture_to_row(
            fixture,
            season,
        )
        for fixture in valid_fixtures
    ]

    dataframe = pd.DataFrame(
        rows,
        columns=HISTORICAL_COLUMNS,
    )

    return clean_historical_dataframe(
        dataframe
    )


# ============================================================
# Clean historical dataframe
# ============================================================

def clean_historical_dataframe(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Clean and standardize historical fixture records.
    """

    if dataframe.empty:

        return pd.DataFrame(
            columns=HISTORICAL_COLUMNS
        )

    dataframe = dataframe.copy()

    # Make sure all expected columns exist.

    for column in HISTORICAL_COLUMNS:

        if column not in dataframe.columns:

            dataframe[column] = None

    dataframe = dataframe[
        HISTORICAL_COLUMNS
    ]

    # --------------------------------------------------------
    # Fixture ID
    # --------------------------------------------------------

    dataframe["fixture_id"] = pd.to_numeric(
        dataframe["fixture_id"],
        errors="coerce",
    )

    dataframe = dataframe.dropna(
        subset=["fixture_id"]
    )

    dataframe["fixture_id"] = (
        dataframe["fixture_id"]
        .astype("int64")
    )

    # --------------------------------------------------------
    # Season
    # --------------------------------------------------------

    dataframe["season"] = pd.to_numeric(
        dataframe["season"],
        errors="coerce",
    )

    dataframe = dataframe.dropna(
        subset=["season"]
    )

    dataframe["season"] = (
        dataframe["season"]
        .astype("int64")
    )

    # --------------------------------------------------------
    # Date
    # --------------------------------------------------------

    dataframe["date"] = pd.to_datetime(
        dataframe["date"],
        errors="coerce",
        utc=True,
    )

    # --------------------------------------------------------
    # Duplicate fixture IDs
    # --------------------------------------------------------

    dataframe = (
        dataframe
        .drop_duplicates(
            subset=["fixture_id"],
            keep="last",
        )
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    dataframe = (
        dataframe
        .sort_values(
            by=[
                "season",
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
# Load historical dataset
# ============================================================

def load_historical_fixtures(
    input_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Load the existing historical fixture dataset.
    """

    if input_path is None:

        input_path = HISTORICAL_FILE

    input_path = Path(
        input_path
    )

    if not input_path.exists():

        return pd.DataFrame(
            columns=HISTORICAL_COLUMNS
        )

    try:

        dataframe = pd.read_csv(
            input_path
        )

    except (
        OSError,
        pd.errors.EmptyDataError,
    ):

        return pd.DataFrame(
            columns=HISTORICAL_COLUMNS
        )

    return clean_historical_dataframe(
        dataframe
    )


# ============================================================
# Save historical dataset
# ============================================================

def save_historical_fixtures(
    dataframe: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Save the complete historical fixture dataset.
    """

    if output_path is None:

        output_path = HISTORICAL_FILE

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe = clean_historical_dataframe(
        dataframe
    )

    dataframe.to_csv(
        output_path,
        index=False,
    )

    return output_path


# ============================================================
# Get available seasons
# ============================================================

def get_dataset_seasons(
    dataframe: pd.DataFrame,
) -> Set[int]:
    """
    Return all seasons currently present.
    """

    if dataframe.empty:

        return set()

    return set(
        dataframe["season"]
        .dropna()
        .astype(int)
        .tolist()
    )


# ============================================================
# Merge datasets
# ============================================================

def merge_historical_fixtures(
    existing: pd.DataFrame,
    incoming: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge existing and incoming historical fixtures.

    fixture_id is the stable global key.
    """

    existing = clean_historical_dataframe(
        existing
    )

    incoming = clean_historical_dataframe(
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

    return clean_historical_dataframe(
        combined
    )


# ============================================================
# Incremental update
# ============================================================

def update_historical_fixtures(
    incoming: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> Dict:
    """
    Incrementally update the historical dataset.
    """

    if output_path is None:

        output_path = HISTORICAL_FILE

    existing = load_historical_fixtures(
        output_path
    )

    incoming = clean_historical_dataframe(
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

    merged = merge_historical_fixtures(
        existing,
        incoming,
    )

    save_historical_fixtures(
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

        "existing_seasons":
            sorted(
                get_dataset_seasons(
                    existing
                )
            ),

        "incoming_seasons":
            sorted(
                get_dataset_seasons(
                    incoming
                )
            ),

        "final_seasons":
            sorted(
                get_dataset_seasons(
                    merged
                )
            ),

        "duplicate_free":
            (
                merged.empty
                or
                merged["fixture_id"].is_unique
            ),
    }