"""
FixtureIQ Stage 7.4.5
Final Model-Ready Dataset Preparation.

Creates explicit X/y datasets from the already verified
train_features.csv and validation_features.csv.

Target/result columns are never included in X.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

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

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
)

X_TRAIN_FILE = MODEL_DIR / "X_train.csv"
Y_TRAIN_FILE = MODEL_DIR / "y_train.csv"

X_VALIDATION_FILE = (
    MODEL_DIR / "X_validation.csv"
)

Y_VALIDATION_FILE = (
    MODEL_DIR / "y_validation.csv"
)

FEATURE_SCHEMA_FILE = (
    MODEL_DIR / "feature_schema.json"
)

DATASET_METADATA_FILE = (
    MODEL_DIR / "dataset_metadata.json"
)


IDENTIFIER_COLUMNS = {
    "fixture_id",
    "season",
    "date",
    "home_team_id",
    "home_team_name",
    "away_team_id",
    "away_team_name",
}

TARGET_COLUMNS = {
    "home_goals",
    "away_goals",
    "target",
    "target_label",
}


def load_split(path: Path) -> pd.DataFrame:

    if not path.exists():

        raise FileNotFoundError(
            f"Missing split dataset: {path}"
        )

    return pd.read_csv(path)


def get_feature_columns(
    dataframe: pd.DataFrame,
):

    excluded = (
        IDENTIFIER_COLUMNS
        |
        TARGET_COLUMNS
    )

    return [
        column
        for column in dataframe.columns
        if column not in excluded
    ]


def validate_feature_columns(
    train: pd.DataFrame,
    validation: pd.DataFrame,
):

    train_features = get_feature_columns(
        train
    )

    validation_features = get_feature_columns(
        validation
    )

    if train_features != validation_features:

        raise ValueError(
            "Training and validation feature "
            "columns do not match."
        )

    if not train_features:

        raise ValueError(
            "No model feature columns found."
        )

    return train_features


def build_model_ready_datasets():

    train = load_split(
        TRAIN_FILE
    )

    validation = load_split(
        VALIDATION_FILE
    )

    feature_columns = (
        validate_feature_columns(
            train,
            validation,
        )
    )

    # --------------------------------------------------------
    # Feature matrices
    # --------------------------------------------------------

    X_train = train[
        feature_columns
    ].copy()

    X_validation = validation[
        feature_columns
    ].copy()

    # --------------------------------------------------------
    # Targets
    # --------------------------------------------------------

    y_train = train[
        [
            "fixture_id",
            "target",
        ]
    ].copy()

    y_validation = validation[
        [
            "fixture_id",
            "target",
        ]
    ].copy()

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    for column in feature_columns:

        X_train[column] = pd.to_numeric(
            X_train[column],
            errors="coerce",
        )

        X_validation[column] = pd.to_numeric(
            X_validation[column],
            errors="coerce",
        )

    # --------------------------------------------------------
    # Safety validation
    # --------------------------------------------------------

    if X_train.isna().any().any():

        raise ValueError(
            "Training feature matrix contains NaN."
        )

    if X_validation.isna().any().any():

        raise ValueError(
            "Validation feature matrix contains NaN."
        )

    if np.isinf(
        X_train.to_numpy()
    ).any():

        raise ValueError(
            "Training feature matrix contains "
            "infinite values."
        )

    if np.isinf(
        X_validation.to_numpy()
    ).any():

        raise ValueError(
            "Validation feature matrix contains "
            "infinite values."
        )

    if y_train["target"].isna().any():

        raise ValueError(
            "Training target contains missing values."
        )

    if y_validation["target"].isna().any():

        raise ValueError(
            "Validation target contains missing values."
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    X_train.to_csv(
        X_TRAIN_FILE,
        index=False,
    )

    y_train.to_csv(
        Y_TRAIN_FILE,
        index=False,
    )

    X_validation.to_csv(
        X_VALIDATION_FILE,
        index=False,
    )

    y_validation.to_csv(
        Y_VALIDATION_FILE,
        index=False,
    )

    # --------------------------------------------------------
    # Feature schema
    # --------------------------------------------------------

    schema = {
        "stage": "7.4.5",
        "feature_count": len(
            feature_columns
        ),
        "feature_columns":
            feature_columns,
        "excluded_identifier_columns":
            sorted(IDENTIFIER_COLUMNS),
        "excluded_target_columns":
            sorted(TARGET_COLUMNS),
        "leakage_policy":
            "Only pre-match historical information "
            "may be used as a model feature.",
        "training_feature_file":
            str(X_TRAIN_FILE),
        "validation_feature_file":
            str(X_VALIDATION_FILE),
        "training_target_file":
            str(Y_TRAIN_FILE),
        "validation_target_file":
            str(Y_VALIDATION_FILE),
    }

    with FEATURE_SCHEMA_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            schema,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # --------------------------------------------------------
    # Dataset metadata
    # --------------------------------------------------------

    metadata = {
        "stage": "7.4.5",
        "training": {
            "records": len(X_train),
            "feature_count":
                len(feature_columns),
            "target_distribution":
                {
                    str(int(key)):
                        int(value)
                    for key, value
                    in y_train[
                        "target"
                    ].value_counts()
                    .sort_index()
                    .items()
                },
            "first_fixture_id":
                int(
                    y_train[
                        "fixture_id"
                    ].iloc[0]
                ),
            "last_fixture_id":
                int(
                    y_train[
                        "fixture_id"
                    ].iloc[-1]
                ),
        },
        "validation": {
            "records": len(X_validation),
            "feature_count":
                len(feature_columns),
            "target_distribution":
                {
                    str(int(key)):
                        int(value)
                    for key, value
                    in y_validation[
                        "target"
                    ].value_counts()
                    .sort_index()
                    .items()
                },
            "first_fixture_id":
                int(
                    y_validation[
                        "fixture_id"
                    ].iloc[0]
                ),
            "last_fixture_id":
                int(
                    y_validation[
                        "fixture_id"
                    ].iloc[-1]
                ),
        },
        "feature_count":
            len(feature_columns),
        "random_shuffle":
            False,
        "final_test_touched":
            False,
    }

    with DATASET_METADATA_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return (
        X_train,
        y_train,
        X_validation,
        y_validation,
        feature_columns,
    )