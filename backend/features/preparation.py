"""
FixtureIQ Stage 7.4.1
Feature Input Preparation.

Prepares the verified historical fixture dataset for
time-based feature construction.

This module does not modify the original historical dataset.
"""

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

HISTORICAL_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "historical_fixtures.csv"
)

FEATURE_INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "feature_input.csv"
)


REQUIRED_COLUMNS = [
    "fixture_id",
    "season",
    "date",
    "status_short",
    "home_team_id",
    "home_team_name",
    "away_team_id",
    "away_team_name",
    "home_goals",
    "away_goals",
]


def load_historical_input(
    input_path: Path = HISTORICAL_FILE,
) -> pd.DataFrame:
    """Load the verified historical fixture dataset."""

    if not input_path.exists():
        raise FileNotFoundError(
            f"Historical dataset not found: {input_path}"
        )

    dataframe = pd.read_csv(
        input_path
    )

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing:
        raise ValueError(
            "Missing required columns: "
            f"{missing}"
        )

    return dataframe


def prepare_feature_input(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepare chronological model-input records.

    Only completed fixtures with usable scores are retained.
    """

    dataframe = dataframe.copy()

    # --------------------------------------------------------
    # Types
    # --------------------------------------------------------

    dataframe["fixture_id"] = pd.to_numeric(
        dataframe["fixture_id"],
        errors="coerce",
    )

    dataframe["season"] = pd.to_numeric(
        dataframe["season"],
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

    # --------------------------------------------------------
    # Required data
    # --------------------------------------------------------

    dataframe = dataframe.dropna(
        subset=[
            "fixture_id",
            "season",
            "date",
            "home_team_id",
            "away_team_id",
            "home_goals",
            "away_goals",
        ]
    )

    # --------------------------------------------------------
    # Completed-match filter
    # --------------------------------------------------------

    completed_statuses = {
        "FT",
        "AET",
        "PEN",
    }

    dataframe = dataframe[
        dataframe["status_short"]
        .astype(str)
        .isin(completed_statuses)
    ]

    # --------------------------------------------------------
    # Basic score validation
    # --------------------------------------------------------

    dataframe = dataframe[
        (dataframe["home_goals"] >= 0)
        &
        (dataframe["away_goals"] >= 0)
    ]

    # --------------------------------------------------------
    # Target
    # --------------------------------------------------------

    dataframe["target"] = 0

    dataframe.loc[
        dataframe["home_goals"]
        >
        dataframe["away_goals"],
        "target",
    ] = 1

    dataframe.loc[
        dataframe["home_goals"]
        <
        dataframe["away_goals"],
        "target",
    ] = 2

    # 0 = Draw
    # 1 = Home win
    # 2 = Away win

    dataframe["target_label"] = (
        dataframe["target"]
        .map(
            {
                0: "draw",
                1: "home_win",
                2: "away_win",
            }
        )
    )

    # --------------------------------------------------------
    # Chronological ordering
    # --------------------------------------------------------

    dataframe = (
        dataframe
        .sort_values(
            [
                "date",
                "fixture_id",
            ]
        )
        .drop_duplicates(
            subset=["fixture_id"],
            keep="last",
        )
        .reset_index(
            drop=True
        )
    )

    # --------------------------------------------------------
    # Cast integer fields
    # --------------------------------------------------------

    integer_columns = [
        "fixture_id",
        "season",
        "home_team_id",
        "away_team_id",
        "home_goals",
        "away_goals",
        "target",
    ]

    for column in integer_columns:

        dataframe[column] = (
            dataframe[column]
            .astype(int)
        )

    return dataframe


def save_feature_input(
    dataframe: pd.DataFrame,
    output_path: Path = FEATURE_INPUT_FILE,
) -> Path:
    """Save prepared feature input."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        output_path,
        index=False,
    )

    return output_path