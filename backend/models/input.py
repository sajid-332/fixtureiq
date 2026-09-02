"""
FixtureIQ Stage 7.5.1
Model Input & Target Contract.

Provides a single validated interface for loading the
model-ready training and validation datasets.

This module does not modify any dataset.
"""

from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

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


TARGET_MAPPING = {
    0: "draw",
    1: "home_win",
    2: "away_win",
}


def _load_csv(path: Path) -> pd.DataFrame:
    """Load a CSV and fail clearly if it is missing."""

    if not path.exists():
        raise FileNotFoundError(
            f"Required model file not found: {path}"
        )

    return pd.read_csv(path)


def _validate_numeric_features(
    dataframe: pd.DataFrame,
    name: str,
) -> None:
    """Validate a feature matrix."""

    if dataframe.empty:
        raise ValueError(
            f"{name} is empty."
        )

    non_numeric = [
        column
        for column in dataframe.columns
        if not pd.api.types.is_numeric_dtype(
            dataframe[column]
        )
    ]

    if non_numeric:
        raise ValueError(
            f"{name} contains non-numeric columns: "
            f"{non_numeric}"
        )

    if dataframe.isna().any().any():
        raise ValueError(
            f"{name} contains NaN values."
        )

    values = dataframe.to_numpy(
        dtype=float
    )

    if not np.isfinite(values).all():
        raise ValueError(
            f"{name} contains infinite values."
        )


def _validate_targets(
    dataframe: pd.DataFrame,
    name: str,
) -> None:
    """Validate the target dataframe."""

    if "target" not in dataframe.columns:
        raise ValueError(
            f"{name} does not contain 'target'."
        )

    if dataframe.empty:
        raise ValueError(
            f"{name} is empty."
        )

    if dataframe["target"].isna().any():
        raise ValueError(
            f"{name} contains missing targets."
        )

    numeric_targets = pd.to_numeric(
        dataframe["target"],
        errors="coerce",
    )

    if numeric_targets.isna().any():
        raise ValueError(
            f"{name} contains invalid targets."
        )

    invalid = set(
        numeric_targets.astype(int).unique()
    ) - set(
        TARGET_MAPPING.keys()
    )

    if invalid:
        raise ValueError(
            f"{name} contains invalid target values: "
            f"{sorted(invalid)}"
        )


def get_feature_columns() -> List[str]:
    """
    Return the authoritative model feature list
    from feature_schema.json.
    """

    if not FEATURE_SCHEMA_FILE.exists():
        raise FileNotFoundError(
            "Feature schema not found: "
            f"{FEATURE_SCHEMA_FILE}"
        )

    import json

    with FEATURE_SCHEMA_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        schema = json.load(file)

    columns = schema.get(
        "feature_columns"
    )

    if not columns:
        raise ValueError(
            "Feature schema contains no "
            "feature_columns."
        )

    return list(columns)


def load_training_data() -> Tuple[
    pd.DataFrame,
    pd.Series,
]:
    """
    Load and validate training features and targets.
    """

    X_train = _load_csv(
        X_TRAIN_FILE
    )

    y_train = _load_csv(
        Y_TRAIN_FILE
    )

    expected = get_feature_columns()

    if list(X_train.columns) != expected:
        raise ValueError(
            "Training feature columns do not "
            "match the feature schema."
        )

    _validate_numeric_features(
        X_train,
        "X_train",
    )

    _validate_targets(
        y_train,
        "y_train",
    )

    if len(X_train) != len(y_train):
        raise ValueError(
            "X_train and y_train row counts "
            "do not match."
        )

    return (
        X_train,
        y_train["target"].astype(int),
    )


def load_validation_data() -> Tuple[
    pd.DataFrame,
    pd.Series,
]:
    """
    Load and validate validation features and targets.
    """

    X_validation = _load_csv(
        X_VALIDATION_FILE
    )

    y_validation = _load_csv(
        Y_VALIDATION_FILE
    )

    expected = get_feature_columns()

    if list(X_validation.columns) != expected:
        raise ValueError(
            "Validation feature columns do not "
            "match the feature schema."
        )

    _validate_numeric_features(
        X_validation,
        "X_validation",
    )

    _validate_targets(
        y_validation,
        "y_validation",
    )

    if len(X_validation) != len(
        y_validation
    ):
        raise ValueError(
            "X_validation and y_validation row "
            "counts do not match."
        )

    return (
        X_validation,
        y_validation["target"].astype(int),
    )


def validate_model_contract() -> dict:
    """
    Validate the complete 7.5.1 contract.
    """

    X_train, y_train = (
        load_training_data()
    )

    X_validation, y_validation = (
        load_validation_data()
    )

    train_columns = list(
        X_train.columns
    )

    validation_columns = list(
        X_validation.columns
    )

    if train_columns != validation_columns:
        raise ValueError(
            "Training and validation feature "
            "columns differ."
        )

    return {
        "training_rows":
            len(X_train),

        "validation_rows":
            len(X_validation),

        "feature_count":
            len(train_columns),

        "training_shape":
            list(X_train.shape),

        "validation_shape":
            list(X_validation.shape),

        "target_mapping":
            TARGET_MAPPING,

        "feature_columns_match":
            True,

        "numeric_features":
            True,

        "valid_targets":
            True,
    }