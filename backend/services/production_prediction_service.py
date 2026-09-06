"""
FixtureIQ Stage 7.8.3
Production Prediction Service.

Responsibilities:
- Verify the locked production model artifact.
- Validate the exact 86-feature production matrix.
- Generate Draw / Home Win / Away Win probabilities.
- Validate probability and prediction integrity.

This service NEVER:
- trains a model
- tunes a model
- selects a model
- reads final-test evaluation artifacts
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


EXPECTED_CLASSES = [
    0,  # Draw
    1,  # Home Win
    2,  # Away Win
]

EXPECTED_FEATURE_COUNT = 86


# ============================================================
# File hashing
# ============================================================

def sha256_file(
    path: Path,
) -> str:
    """
    Calculate SHA256 for an artifact.
    """

    if not path.exists():

        raise FileNotFoundError(
            f"File not found: {path}"
        )

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


# ============================================================
# Metadata hash discovery
# ============================================================

def collect_declared_sha256(
    payload,
) -> set[str]:
    """
    Recursively collect SHA256 values declared in
    model lifecycle / manifest JSON structures.

    This avoids depending on one particular JSON key name.
    """

    hashes = set()

    sha_pattern = re.compile(
        r"^[0-9a-fA-F]{64}$"
    )

    def walk(
        value,
        key_path: str = "",
    ):

        if isinstance(
            value,
            dict,
        ):

            for key, child in value.items():

                next_path = (
                    f"{key_path}.{key}"
                    if key_path
                    else str(key)
                )

                walk(
                    child,
                    next_path,
                )

        elif isinstance(
            value,
            list,
        ):

            for child in value:

                walk(
                    child,
                    key_path,
                )

        elif isinstance(
            value,
            str,
        ):

            if (
                "sha256" in key_path.lower()
                and
                sha_pattern.fullmatch(
                    value.strip()
                )
            ):

                hashes.add(
                    value.strip().lower()
                )

    walk(
        payload
    )

    return hashes


def verify_locked_model_hash(
    model_path: Path,
    lifecycle: dict,
    manifest: dict,
) -> str:
    """
    Verify that the production model artifact is exactly
    the artifact declared by the Stage 7.7 lock/package.
    """

    actual_hash = sha256_file(
        model_path
    ).lower()

    declared_hashes = set()

    declared_hashes.update(
        collect_declared_sha256(
            lifecycle
        )
    )

    declared_hashes.update(
        collect_declared_sha256(
            manifest
        )
    )

    if not declared_hashes:

        raise RuntimeError(
            "No declared model SHA256 values were found "
            "in the lock/manifest metadata."
        )

    if actual_hash not in declared_hashes:

        raise RuntimeError(
            "Locked production model SHA256 mismatch.\n"
            f"Actual: {actual_hash}"
        )

    return actual_hash


# ============================================================
# Model loading
# ============================================================

def load_locked_model(
    model_path: Path,
):
    """
    Load the frozen production model without performing
    any fitting or training operation.
    """

    if not model_path.exists():

        raise FileNotFoundError(
            f"Locked model not found: "
            f"{model_path}"
        )

    model = joblib.load(
        model_path
    )

    if not hasattr(
        model,
        "predict",
    ):

        raise RuntimeError(
            "Production model has no predict() method."
        )

    if not hasattr(
        model,
        "predict_proba",
    ):

        raise RuntimeError(
            "Production model has no "
            "predict_proba() method."
        )

    if not hasattr(
        model,
        "classes_",
    ):

        raise RuntimeError(
            "Production model has no classes_ attribute."
        )

    model_classes = [
        int(value)
        for value in list(
            model.classes_
        )
    ]

    if set(
        model_classes
    ) != set(
        EXPECTED_CLASSES
    ):

        raise RuntimeError(
            "Unexpected production model classes: "
            f"{model_classes}"
        )

    return model


# ============================================================
# Feature validation
# ============================================================

def validate_feature_matrix(
    features: pd.DataFrame,
    canonical_columns: list[str],
) -> pd.DataFrame:
    """
    Validate the production matrix against the exact
    locked training feature contract.
    """

    if features.empty:

        raise ValueError(
            "Production feature matrix is empty."
        )

    if len(
        canonical_columns
    ) != EXPECTED_FEATURE_COUNT:

        raise ValueError(
            "Canonical production schema does not "
            "contain 86 features."
        )

    if features.shape[
        1
    ] != EXPECTED_FEATURE_COUNT:

        raise ValueError(
            "Production matrix contains "
            f"{features.shape[1]} features; "
            "expected 86."
        )

    if list(
        features.columns
    ) != list(
        canonical_columns
    ):

        raise ValueError(
            "Production feature order does not "
            "match the locked model contract."
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

        raise ValueError(
            "Prohibited columns found in "
            "production matrix: "
            f"{sorted(leaked)}"
        )

    numeric = features.copy()

    for column in numeric.columns:

        numeric[column] = pd.to_numeric(
            numeric[column],
            errors="raise",
        )

    values = numeric.to_numpy(
        dtype=float
    )

    if not np.isfinite(
        values
    ).all():

        raise ValueError(
            "Production feature matrix contains "
            "NaN or infinite values."
        )

    return numeric


# ============================================================
# Prediction
# ============================================================

def generate_predictions(
    model,
    features: pd.DataFrame,
) -> pd.DataFrame:
    """
    Generate canonical 3-class probabilities.

    Canonical class mapping:
        0 = Draw
        1 = Home Win
        2 = Away Win
    """

    probabilities = model.predict_proba(
        features
    )

    probabilities = np.asarray(
        probabilities,
        dtype=float,
    )

    if probabilities.ndim != 2:

        raise RuntimeError(
            "predict_proba() returned an invalid shape."
        )

    if probabilities.shape[
        0
    ] != len(
        features
    ):

        raise RuntimeError(
            "Probability row count does not match "
            "production feature count."
        )

    if probabilities.shape[
        1
    ] != 3:

        raise RuntimeError(
            "Expected 3 probability columns, "
            f"found {probabilities.shape[1]}."
        )

    model_classes = [
        int(value)
        for value in list(
            model.classes_
        )
    ]

    class_index = {
        class_value: index
        for index, class_value
        in enumerate(
            model_classes
        )
    }

    # Reorder probabilities into FixtureIQ's canonical
    # target order regardless of model.classes_ ordering.
    canonical_probabilities = np.column_stack(
        [
            probabilities[
                :,
                class_index[0],
            ],
            probabilities[
                :,
                class_index[1],
            ],
            probabilities[
                :,
                class_index[2],
            ],
        ]
    )

    # --------------------------------------------------------
    # Probability integrity
    # --------------------------------------------------------

    if not np.isfinite(
        canonical_probabilities
    ).all():

        raise RuntimeError(
            "Model generated NaN or infinite probabilities."
        )

    if (
        canonical_probabilities
        < 0.0
    ).any():

        raise RuntimeError(
            "Negative probability detected."
        )

    if (
        canonical_probabilities
        > 1.0
    ).any():

        raise RuntimeError(
            "Probability greater than 1 detected."
        )

    probability_sums = (
        canonical_probabilities.sum(
            axis=1
        )
    )

    if not np.allclose(
        probability_sums,
        1.0,
        atol=1e-8,
        rtol=0.0,
    ):

        raise RuntimeError(
            "Probability rows do not sum to 1."
        )

    # --------------------------------------------------------
    # Prediction target
    # --------------------------------------------------------

    predicted_from_probability = np.argmax(
        canonical_probabilities,
        axis=1,
    ).astype(int)

    model_prediction = np.asarray(
        model.predict(
            features
        ),
        dtype=int,
    )

    if model_prediction.shape[
        0
    ] != len(
        features
    ):

        raise RuntimeError(
            "Model prediction count mismatch."
        )

    if not np.array_equal(
        model_prediction,
        predicted_from_probability,
    ):

        raise RuntimeError(
            "model.predict() does not match "
            "the maximum predict_proba() class."
        )

    confidence = np.max(
        canonical_probabilities,
        axis=1,
    )

    result = pd.DataFrame(
        {
            "predicted_target":
                predicted_from_probability,

            "prob_draw":
                canonical_probabilities[
                    :,
                    0,
                ],

            "prob_home_win":
                canonical_probabilities[
                    :,
                    1,
                ],

            "prob_away_win":
                canonical_probabilities[
                    :,
                    2,
                ],

            "confidence":
                confidence,
        }
    )

    return result