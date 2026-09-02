"""
FixtureIQ Stage 7.4.3
Chronological Train / Validation Split.

Development split:
    Older season(s)  -> Training
    Later season(s)  -> Validation

No random shuffling is used.
The final 2025/26 test period remains outside this pipeline.
"""

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_FEATURES_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "model_features.csv"
)

TRAIN_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "train_features.csv"
)

VALIDATION_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "validation_features.csv"
)

SPLIT_METADATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "split_metadata.json"
)


def load_model_features(
    input_path: Path = MODEL_FEATURES_FILE,
) -> pd.DataFrame:

    if not input_path.exists():

        raise FileNotFoundError(
            f"Model feature dataset not found: "
            f"{input_path}"
        )

    dataframe = pd.read_csv(
        input_path
    )

    required = [
        "fixture_id",
        "season",
        "date",
        "target",
        "target_label",
    ]

    missing = [
        column
        for column in required
        if column not in dataframe.columns
    ]

    if missing:

        raise ValueError(
            f"Missing required columns: {missing}"
        )

    dataframe["fixture_id"] = pd.to_numeric(
        dataframe["fixture_id"],
        errors="coerce",
    )

    dataframe["season"] = pd.to_numeric(
        dataframe["season"],
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
            "season",
            "date",
        ]
    )

    dataframe["fixture_id"] = (
        dataframe["fixture_id"]
        .astype(int)
    )

    dataframe["season"] = (
        dataframe["season"]
        .astype(int)
    )

    dataframe = (
        dataframe
        .sort_values(
            [
                "date",
                "fixture_id",
            ]
        )
        .reset_index(drop=True)
    )

    return dataframe


def chronological_split(
    dataframe: pd.DataFrame,
    training_seasons,
    validation_seasons,
):

    training_seasons = sorted(
        set(training_seasons)
    )

    validation_seasons = sorted(
        set(validation_seasons)
    )

    if set(training_seasons) & set(
        validation_seasons
    ):

        raise ValueError(
            "Training and validation seasons "
            "overlap."
        )

    if not training_seasons:
        raise ValueError(
            "Training season list is empty."
        )

    if not validation_seasons:
        raise ValueError(
            "Validation season list is empty."
        )

    dataframe_seasons = set(
        dataframe["season"]
        .astype(int)
        .unique()
    )

    requested = set(
        training_seasons
        +
        validation_seasons
    )

    missing_seasons = (
        requested
        -
        dataframe_seasons
    )

    if missing_seasons:

        raise ValueError(
            "Requested seasons are missing "
            f"from dataset: {sorted(missing_seasons)}"
        )

    train = dataframe[
        dataframe["season"].isin(
            training_seasons
        )
    ].copy()

    validation = dataframe[
        dataframe["season"].isin(
            validation_seasons
        )
    ].copy()

    train = (
        train
        .sort_values(
            [
                "date",
                "fixture_id",
            ]
        )
        .reset_index(drop=True)
    )

    validation = (
        validation
        .sort_values(
            [
                "date",
                "fixture_id",
            ]
        )
        .reset_index(drop=True)
    )

    return train, validation


def save_split(
    train: pd.DataFrame,
    validation: pd.DataFrame,
):

    TRAIN_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    train.to_csv(
        TRAIN_FILE,
        index=False,
    )

    validation.to_csv(
        VALIDATION_FILE,
        index=False,
    )

    return TRAIN_FILE, VALIDATION_FILE