"""
FixtureIQ Stage 7.8.2
Production Fixture Feature Preparation.

Builds the exact 86-feature model matrix required by the
locked production Random Forest.

Rules:
- Historical completed matches may update team state.
- Upcoming fixtures never update team state.
- A fixture can only see information available before kickoff.
- fixture_id and identity fields are metadata only.
- The returned model matrix contains exactly the canonical
  86 training features.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from backend.features.historical_features import (
    empty_team_state,
    team_features,
    update_team_state,
)


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
)

X_TRAIN_FILE = (
    MODEL_DIR
    / "X_train.csv"
)


REQUIRED_UPCOMING_COLUMNS = [
    "fixture_id",
    "date",
    "home_team_id",
    "home_team_name",
    "away_team_id",
    "away_team_name",
]


def load_canonical_feature_columns() -> list[str]:
    """Load the exact canonical training feature order."""

    if not X_TRAIN_FILE.exists():
        raise FileNotFoundError(
            f"Canonical training schema not found: "
            f"{X_TRAIN_FILE}"
        )

    columns = list(
        pd.read_csv(
            X_TRAIN_FILE,
            nrows=0,
        ).columns
    )

    if len(columns) != 86:
        raise ValueError(
            f"Expected 86 canonical features, "
            f"found {len(columns)}."
        )

    if "fixture_id" in columns:
        raise ValueError(
            "fixture_id must not be a model feature."
        )

    return columns


def validate_upcoming_input(
    upcoming: pd.DataFrame,
) -> pd.DataFrame:
    """Validate and normalize upcoming fixtures."""

    dataframe = upcoming.copy()

    missing = [
        column
        for column in REQUIRED_UPCOMING_COLUMNS
        if column not in dataframe.columns
    ]

    if missing:
        raise ValueError(
            "Missing required upcoming fixture columns: "
            f"{missing}"
        )

    dataframe["fixture_id"] = pd.to_numeric(
        dataframe["fixture_id"],
        errors="coerce",
    )

    dataframe["home_team_id"] = pd.to_numeric(
        dataframe["home_team_id"],
        errors="coerce",
    )

    dataframe["away_team_id"] = pd.to_numeric(
        dataframe["away_team_id"],
        errors="coerce",
    )

    dataframe["date"] = pd.to_datetime(
        dataframe["date"],
        errors="coerce",
        utc=True,
    )

    dataframe = dataframe.dropna(
        subset=[
            "fixture_id",
            "date",
            "home_team_id",
            "away_team_id",
        ]
    ).copy()

    if dataframe.empty:
        raise ValueError(
            "No valid upcoming fixtures remain."
        )

    dataframe["fixture_id"] = (
        dataframe["fixture_id"].astype(int)
    )

    dataframe["home_team_id"] = (
        dataframe["home_team_id"].astype(int)
    )

    dataframe["away_team_id"] = (
        dataframe["away_team_id"].astype(int)
    )

    if not dataframe["fixture_id"].is_unique:
        raise ValueError(
            "Upcoming fixture IDs must be unique."
        )

    if (
        dataframe["home_team_id"]
        ==
        dataframe["away_team_id"]
    ).any():

        raise ValueError(
            "A fixture cannot contain the same "
            "team as both home and away."
        )

    return (
        dataframe
        .sort_values(
            [
                "date",
                "fixture_id",
            ]
        )
        .reset_index(drop=True)
    )


def validate_history(
    history: pd.DataFrame,
) -> pd.DataFrame:
    """Validate completed historical fixtures."""

    required = [
        "fixture_id",
        "date",
        "home_team_id",
        "home_team_name",
        "away_team_id",
        "away_team_name",
        "home_goals",
        "away_goals",
    ]

    missing = [
        column
        for column in required
        if column not in history.columns
    ]

    if missing:
        raise ValueError(
            "Missing historical columns: "
            f"{missing}"
        )

    dataframe = history.copy()

    dataframe["fixture_id"] = pd.to_numeric(
        dataframe["fixture_id"],
        errors="coerce",
    )

    dataframe["home_team_id"] = pd.to_numeric(
        dataframe["home_team_id"],
        errors="coerce",
    )

    dataframe["away_team_id"] = pd.to_numeric(
        dataframe["away_team_id"],
        errors="coerce",
    )

    dataframe["home_goals"] = pd.to_numeric(
        dataframe["home_goals"],
        errors="coerce",
    )

    dataframe["away_goals"] = pd.to_numeric(
        dataframe["away_goals"],
        errors="coerce",
    )

    dataframe["date"] = pd.to_datetime(
        dataframe["date"],
        errors="coerce",
        utc=True,
    )

    dataframe = dataframe.dropna(
        subset=[
            "fixture_id",
            "date",
            "home_team_id",
            "away_team_id",
            "home_goals",
            "away_goals",
        ]
    ).copy()

    dataframe["fixture_id"] = (
        dataframe["fixture_id"].astype(int)
    )

    dataframe["home_team_id"] = (
        dataframe["home_team_id"].astype(int)
    )

    dataframe["away_team_id"] = (
        dataframe["away_team_id"].astype(int)
    )

    dataframe["home_goals"] = (
        dataframe["home_goals"].astype(int)
    )

    dataframe["away_goals"] = (
        dataframe["away_goals"].astype(int)
    )

    if not dataframe["fixture_id"].is_unique:
        raise ValueError(
            "Historical fixture IDs must be unique."
        )

    return (
        dataframe
        .sort_values(
            [
                "date",
                "fixture_id",
            ]
        )
        .reset_index(drop=True)
    )


def _safe_team_feature_dict(
    state,
    side: str,
) -> dict:
    """
    Convert the project's team_features() output into a
    defensive dictionary.

    The existing Stage 7.4 feature implementation remains the
    source of truth for actual feature definitions.
    """

    result = team_features(
        state,
        side,
    )

    if not isinstance(result, dict):
        raise TypeError(
            "team_features() must return a dictionary."
        )

    return result


def _build_feature_row(
    home_state,
    away_state,
    fixture_id: int,
    date,
    home_team_id: int,
    home_team_name: str,
    away_team_id: int,
    away_team_name: str,
) -> dict:
    """Construct the pre-match feature state."""

    row = {
        "fixture_id": fixture_id,
        "date": date,
        "home_team_id": home_team_id,
        "home_team_name": home_team_name,
        "away_team_id": away_team_id,
        "away_team_name": away_team_name,
    }

    home_features = _safe_team_feature_dict(
        home_state,
        "home",
    )

    away_features = _safe_team_feature_dict(
        away_state,
        "away",
    )

    row.update(home_features)
    row.update(away_features)

    difference_pairs = [
        (
            "points_per_match",
            "points_per_match",
        ),
        (
            "goals_for_per_match",
            "goals_for_per_match",
        ),
        (
            "goals_against_per_match",
            "goals_against_per_match",
        ),
        (
            "goal_difference",
            "goal_difference",
        ),
        (
            "last5_points",
            "last5_points",
        ),
        (
            "last10_points",
            "last10_points",
        ),
        (
            "last5_goals_for",
            "last5_goals_for",
        ),
        (
            "last10_goals_for",
            "last10_goals_for",
        ),
    ]

    for home_key, away_key in difference_pairs:

        home_column = (
            f"home_{home_key}"
        )

        away_column = (
            f"away_{away_key}"
        )

        if (
            home_column in row
            and
            away_column in row
        ):

            row[
                f"diff_{home_key}"
            ] = (
                row[home_column]
                -
                row[away_column]
            )

    row[
        "home_prior_matches"
    ] = home_state["matches"]

    row[
        "away_prior_matches"
    ] = away_state["matches"]

    row[
        "home_prior_points"
    ] = home_state["points"]

    row[
        "away_prior_points"
    ] = away_state["points"]

    return row


def build_production_features(
    history: pd.DataFrame,
    upcoming: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Build production features using only historical state
    available before each upcoming fixture.
    """

    history = validate_history(
        history
    )

    upcoming = validate_upcoming_input(
        upcoming
    )

    feature_columns = (
        load_canonical_feature_columns()
    )

    latest_history_date = (
        history["date"].max()
    )

    earliest_upcoming_date = (
        upcoming["date"].min()
    )

    if earliest_upcoming_date <= latest_history_date:

        raise ValueError(
            "Upcoming fixtures must occur after "
            "the latest historical fixture."
        )

    states = defaultdict(
        empty_team_state
    )

    # --------------------------------------------------------
    # Replay historical state.
    # --------------------------------------------------------

    for _, match in history.iterrows():

        home_id = int(
            match["home_team_id"]
        )

        away_id = int(
            match["away_team_id"]
        )

        home_goals = int(
            match["home_goals"]
        )

        away_goals = int(
            match["away_goals"]
        )

        if home_goals > away_goals:

            home_result = "W"
            away_result = "L"

        elif home_goals < away_goals:

            home_result = "L"
            away_result = "W"

        else:

            home_result = "D"
            away_result = "D"

        update_team_state(
            states[home_id],
            home_result,
            home_goals,
            away_goals,
            "home",
        )

        update_team_state(
            states[away_id],
            away_result,
            away_goals,
            home_goals,
            "away",
        )

    # --------------------------------------------------------
    # Build upcoming features.
    #
    # IMPORTANT:
    # Upcoming fixtures NEVER update state.
    # --------------------------------------------------------

    feature_rows = []
    metadata_rows = []

    for _, fixture in upcoming.iterrows():

        home_id = int(
            fixture["home_team_id"]
        )

        away_id = int(
            fixture["away_team_id"]
        )

        home_name = str(
            fixture["home_team_name"]
        )

        away_name = str(
            fixture["away_team_name"]
        )

        row = _build_feature_row(
            home_state=states[home_id],
            away_state=states[away_id],
            fixture_id=int(
                fixture["fixture_id"]
            ),
            date=fixture["date"],
            home_team_id=home_id,
            home_team_name=home_name,
            away_team_id=away_id,
            away_team_name=away_name,
        )

        feature_rows.append(
            row
        )

        metadata_rows.append(
            {
                "fixture_id":
                    int(
                        fixture["fixture_id"]
                    ),

                "date":
                    fixture["date"],

                "home_team_id":
                    home_id,

                "home_team_name":
                    home_name,

                "away_team_id":
                    away_id,

                "away_team_name":
                    away_name,
            }
        )

    raw_features = pd.DataFrame(
        feature_rows
    )

    metadata = pd.DataFrame(
        metadata_rows
    )

    missing = [
        column
        for column in feature_columns
        if column not in raw_features.columns
    ]

    if missing:
        raise ValueError(
            "Production feature constructor is missing "
            f"canonical features: {missing}"
        )

    model_matrix = raw_features[
        feature_columns
    ].copy()

    if model_matrix.shape != (
        len(upcoming),
        86,
    ):

        raise ValueError(
            "Unexpected production model matrix shape: "
            f"{model_matrix.shape}"
        )

    if "fixture_id" in model_matrix.columns:
        raise ValueError(
            "fixture_id entered the model matrix."
        )

    for column in model_matrix.columns:

        model_matrix[column] = pd.to_numeric(
            model_matrix[column],
            errors="raise",
        )

    values = model_matrix.to_numpy(
        dtype=float
    )

    if not np.isfinite(
        values
    ).all():

        raise ValueError(
            "Production feature matrix contains "
            "NaN or infinite values."
        )

    return (
        metadata,
        model_matrix,
    )