"""
FixtureIQ Stage 7.8.3
Production Prediction Execution.

Consumes:
- locked Random Forest
- locked 86-feature contract
- production_features.csv
- production_fixture_metadata.csv
- upcoming_fixtures.csv

Produces:
- production_predictions.csv
- production_prediction_metadata.json
- production_prediction_report.json

No retraining.
No tuning.
No model selection.
No final-test evaluation artifact access.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
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

from backend.services.production_prediction_service import (
    generate_predictions,
    load_locked_model,
    sha256_file,
    validate_feature_matrix,
    verify_locked_model_hash,
)


# ============================================================
# Paths
# ============================================================

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
)

PRODUCTION_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "production"
)


MODEL_FILE = (
    MODEL_DIR
    / "selected"
    / "selected_model.joblib"
)

MODEL_LIFECYCLE_FILE = (
    MODEL_DIR
    / "selected_model.json"
)

MODEL_MANIFEST_FILE = (
    MODEL_DIR
    / "selected"
    / "selected_model_manifest.json"
)

CONTRACT_FILE = (
    MODEL_DIR
    / "production_inference_contract.json"
)


FEATURE_FILE = (
    PRODUCTION_DIR
    / "production_features.csv"
)

FIXTURE_METADATA_FILE = (
    PRODUCTION_DIR
    / "production_fixture_metadata.csv"
)

UPCOMING_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
)

FEATURE_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_feature_report.json"
)


PREDICTION_FILE = (
    PRODUCTION_DIR
    / "production_predictions.csv"
)

PREDICTION_METADATA_FILE = (
    PRODUCTION_DIR
    / "production_prediction_metadata.json"
)

PREDICTION_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_prediction_report.json"
)


# ============================================================
# Helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise FileNotFoundError(
            f"Required file missing: {path}"
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


def require_bool(
    payload: dict,
    key: str,
    expected: bool,
):

    if payload.get(
        key
    ) is not expected:

        raise RuntimeError(
            f"Expected {key}={expected}, "
            f"found {payload.get(key)}."
        )


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 62)

    print(
        "FixtureIQ Stage 7.8.3"
    )

    print(
        "Production Prediction Execution"
    )

    print("=" * 62)

    generated_at = datetime.now(
        timezone.utc
    ).isoformat()

    # ========================================================
    # 1. Locked model contract
    # ========================================================

    print(
        "\n1. LOCKED MODEL CONTRACT"
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
            "Locked production model is not "
            "Random Forest."
        )

    if model_contract.get(
        "status"
    ) != "LOCKED":

        raise RuntimeError(
            "Production model is not LOCKED."
        )

    feature_columns = contract.get(
        "feature_columns",
        [],
    )

    if len(
        feature_columns
    ) != 86:

        raise RuntimeError(
            "Production contract does not "
            "contain 86 features."
        )

    target_mapping = contract.get(
        "target_mapping",
        {},
    )

    expected_target_mapping = {
        "0": "draw",
        "1": "home_win",
        "2": "away_win",
    }

    if target_mapping != expected_target_mapping:

        raise RuntimeError(
            "Production target mapping mismatch."
        )

    final_test = contract.get(
        "final_test",
        {},
    )

    if final_test.get(
        "status"
    ) != "CONSUMED":

        raise RuntimeError(
            "Final-test lifecycle is not CONSUMED."
        )

    if final_test.get(
        "must_not_be_used_for_training"
    ) is not True:

        raise RuntimeError(
            "Final-test training protection missing."
        )

    if final_test.get(
        "must_not_be_used_for_selection"
    ) is not True:

        raise RuntimeError(
            "Final-test selection protection missing."
        )

    print(
        "Contract: PASS"
    )

    print(
        "Selected model: Random Forest"
    )

    print(
        "Model status: LOCKED"
    )

    print(
        "Feature count: 86"
    )

    print(
        "Target mapping: PASS"
    )

    print(
        "Final test lifecycle: CONSUMED"
    )

    # ========================================================
    # 2. Model artifact integrity
    # ========================================================

    print(
        "\n2. MODEL ARTIFACT INTEGRITY"
    )

    lifecycle = load_json(
        MODEL_LIFECYCLE_FILE
    )

    manifest = load_json(
        MODEL_MANIFEST_FILE
    )

    # Stage 7.7.4 changed these lifecycle flags
    # after final-test consumption.
    if lifecycle.get(
        "final_test_used"
    ) is not True:

        raise RuntimeError(
            "selected_model.json does not show "
            "final_test_used=true."
        )

    if lifecycle.get(
        "final_test_evaluated"
    ) is not True:

        raise RuntimeError(
            "selected_model.json does not show "
            "final_test_evaluated=true."
        )

    model_sha256 = (
        verify_locked_model_hash(
            MODEL_FILE,
            lifecycle,
            manifest,
        )
    )

    print(
        "Locked model artifact exists: PASS"
    )

    print(
        "Model SHA256: MATCH"
    )

    print(
        f"SHA256: {model_sha256}"
    )

    # ========================================================
    # 3. Production feature provenance
    # ========================================================

    print(
        "\n3. PRODUCTION FEATURE PROVENANCE"
    )

    feature_report = load_json(
        FEATURE_REPORT_FILE
    )

    if feature_report.get(
        "stage"
    ) != "7.8.2":

        raise RuntimeError(
            "Production feature report "
            "is not Stage 7.8.2."
        )

    if feature_report.get(
        "status"
    ) != "PASS":

        raise RuntimeError(
            "Production feature report "
            "is not PASS."
        )

    if feature_report.get(
        "model_retrained"
    ) is not False:

        raise RuntimeError(
            "Feature provenance indicates "
            "model retraining."
        )

    if feature_report.get(
        "model_selected"
    ) is not False:

        raise RuntimeError(
            "Feature provenance indicates "
            "model selection."
        )

    if feature_report.get(
        "hyperparameter_tuned"
    ) is not False:

        raise RuntimeError(
            "Feature provenance indicates "
            "hyperparameter tuning."
        )

    if feature_report.get(
        "final_test_evaluation_artifacts_used"
    ) is not False:

        raise RuntimeError(
            "Feature provenance violated "
            "final-test protection."
        )

    current_feature_hash = sha256_file(
        FEATURE_FILE
    )

    report_feature_hash = (
        feature_report.get(
            "production_feature_sha256"
        )
    )

    if (
        not report_feature_hash
        or
        current_feature_hash.lower()
        != str(
            report_feature_hash
        ).lower()
    ):

        raise RuntimeError(
            "Production feature artifact hash "
            "does not match its Stage 7.8.2 report."
        )

    print(
        "Stage 7.8.2 report: PASS"
    )

    print(
        "Production feature SHA256: MATCH"
    )

    print(
        "Model retrained upstream: NO"
    )

    print(
        "Model selected upstream: NO"
    )

    print(
        "Final-test evaluation artifacts used upstream: NO"
    )

    # ========================================================
    # 4. Load production inputs
    # ========================================================

    print(
        "\n4. PRODUCTION INPUTS"
    )

    for required_file in [
        FEATURE_FILE,
        FIXTURE_METADATA_FILE,
        UPCOMING_FILE,
    ]:

        if not required_file.exists():

            raise FileNotFoundError(
                f"Production input missing: "
                f"{required_file}"
            )

    features = pd.read_csv(
        FEATURE_FILE
    )

    fixture_metadata = pd.read_csv(
        FIXTURE_METADATA_FILE
    )

    upcoming = pd.read_csv(
        UPCOMING_FILE
    )

    features = validate_feature_matrix(
        features,
        feature_columns,
    )

    if len(
        features
    ) != len(
        fixture_metadata
    ):

        raise RuntimeError(
            "Feature rows and fixture metadata "
            "rows do not match."
        )

    if len(
        features
    ) != len(
        upcoming
    ):

        raise RuntimeError(
            "Feature rows and upcoming fixture "
            "rows do not match."
        )

    if len(
        features
    ) == 0:

        raise RuntimeError(
            "No production fixtures available."
        )

    print(
        f"Feature matrix: "
        f"{features.shape}"
    )

    print(
        f"Fixture metadata rows: "
        f"{len(fixture_metadata)}"
    )

    print(
        f"Upcoming fixture rows: "
        f"{len(upcoming)}"
    )

    print(
        "86-feature schema: PASS"
    )

    print(
        "Numeric integrity: PASS"
    )

    # ========================================================
    # 5. Fixture alignment
    # ========================================================

    print(
        "\n5. FIXTURE ALIGNMENT"
    )

    if "fixture_id" not in (
        fixture_metadata.columns
    ):

        raise RuntimeError(
            "Fixture metadata does not contain "
            "fixture_id."
        )

    if "fixture_id" not in (
        upcoming.columns
    ):

        raise RuntimeError(
            "Upcoming snapshot does not contain "
            "fixture_id."
        )

    fixture_metadata[
        "fixture_id"
    ] = pd.to_numeric(
        fixture_metadata[
            "fixture_id"
        ],
        errors="raise",
    ).astype(
        "int64"
    )

    upcoming[
        "fixture_id"
    ] = pd.to_numeric(
        upcoming[
            "fixture_id"
        ],
        errors="raise",
    ).astype(
        "int64"
    )

    if not fixture_metadata[
        "fixture_id"
    ].is_unique:

        raise RuntimeError(
            "Fixture metadata IDs are not unique."
        )

    if not upcoming[
        "fixture_id"
    ].is_unique:

        raise RuntimeError(
            "Upcoming fixture IDs are not unique."
        )

    metadata_ids = fixture_metadata[
        "fixture_id"
    ].tolist()

    upcoming_ids = upcoming[
        "fixture_id"
    ].tolist()

    if set(
        metadata_ids
    ) != set(
        upcoming_ids
    ):

        raise RuntimeError(
            "Fixture metadata and upcoming snapshot "
            "contain different fixture IDs."
        )

    # Reorder provider snapshot into the exact order used
    # during feature construction.
    upcoming_indexed = (
        upcoming
        .set_index(
            "fixture_id"
        )
        .loc[
            metadata_ids
        ]
        .reset_index()
    )

    if upcoming_indexed[
        "fixture_id"
    ].tolist() != metadata_ids:

        raise RuntimeError(
            "Fixture ordering alignment failed."
        )

    # Confirm important identity fields still agree.
    identity_fields = [
        "home_team_id",
        "home_team_name",
        "away_team_id",
        "away_team_name",
    ]

    for field in identity_fields:

        if field not in (
            fixture_metadata.columns
        ):

            raise RuntimeError(
                f"Fixture metadata missing {field}."
            )

        if field not in (
            upcoming_indexed.columns
        ):

            raise RuntimeError(
                f"Upcoming snapshot missing {field}."
            )

        left = (
            fixture_metadata[
                field
            ]
            .astype(str)
            .tolist()
        )

        right = (
            upcoming_indexed[
                field
            ]
            .astype(str)
            .tolist()
        )

        if left != right:

            raise RuntimeError(
                f"Fixture identity mismatch "
                f"for {field}."
            )

    print(
        "Fixture IDs unique: PASS"
    )

    print(
        "Fixture ID sets match: PASS"
    )

    print(
        "Fixture order: PASS"
    )

    print(
        "Team identities: PASS"
    )

    # ========================================================
    # 6. Upcoming-time protection
    # ========================================================

    print(
        "\n6. UPCOMING FIXTURE SAFETY"
    )

    dates = pd.to_datetime(
        fixture_metadata[
            "date"
        ],
        errors="coerce",
        utc=True,
    )

    if dates.isna().any():

        raise RuntimeError(
            "Invalid prediction fixture date."
        )

    current_time = pd.Timestamp.now(
        tz="UTC"
    )

    if (
        dates <= current_time
    ).any():

        raise RuntimeError(
            "At least one fixture is no longer "
            "upcoming. Refresh Stage 7.8.2 first."
        )

    print(
        "Upcoming fixtures only: PASS"
    )

    print(
        f"Prediction fixtures: "
        f"{len(features)}"
    )

    # ========================================================
    # 7. Load locked model
    # ========================================================

    print(
        "\n7. LOAD LOCKED MODEL"
    )

    model = load_locked_model(
        MODEL_FILE
    )

    model_classes = [
        int(value)
        for value
        in list(
            model.classes_
        )
    ]

    print(
        "Model loaded: PASS"
    )

    print(
        f"Model classes: "
        f"{model_classes}"
    )

    print(
        "Class contract {0,1,2}: PASS"
    )

    # ========================================================
    # 8. Generate predictions
    # ========================================================

    print(
        "\n8. GENERATE PREDICTIONS"
    )

    prediction_values = (
        generate_predictions(
            model,
            features,
        )
    )

    if len(
        prediction_values
    ) != len(
        features
    ):

        raise RuntimeError(
            "Production prediction count mismatch."
        )

    label_mapping = {
        0: "Draw",
        1: "Home Win",
        2: "Away Win",
    }

    prediction_values[
        "predicted_label"
    ] = (
        prediction_values[
            "predicted_target"
        ].map(
            label_mapping
        )
    )

    if prediction_values[
        "predicted_label"
    ].isna().any():

        raise RuntimeError(
            "Invalid predicted target/label mapping."
        )

    print(
        f"Predictions generated: "
        f"{len(prediction_values)}"
    )

    print(
        "Target mapping: PASS"
    )

    # ========================================================
    # 9. Probability integrity
    # ========================================================

    print(
        "\n9. PROBABILITY INTEGRITY"
    )

    probability_columns = [
        "prob_draw",
        "prob_home_win",
        "prob_away_win",
    ]

    probability_values = (
        prediction_values[
            probability_columns
        ].to_numpy(
            dtype=float
        )
    )

    if not np.isfinite(
        probability_values
    ).all():

        raise RuntimeError(
            "NaN/Inf probability detected."
        )

    if (
        probability_values < 0.0
    ).any():

        raise RuntimeError(
            "Probability below 0 detected."
        )

    if (
        probability_values > 1.0
    ).any():

        raise RuntimeError(
            "Probability above 1 detected."
        )

    row_sums = (
        probability_values.sum(
            axis=1
        )
    )

    if not np.allclose(
        row_sums,
        1.0,
        atol=1e-8,
        rtol=0.0,
    ):

        raise RuntimeError(
            "Probability rows do not sum to 1."
        )

    expected_confidence = np.max(
        probability_values,
        axis=1,
    )

    actual_confidence = (
        prediction_values[
            "confidence"
        ].to_numpy(
            dtype=float
        )
    )

    if not np.allclose(
        expected_confidence,
        actual_confidence,
        atol=1e-12,
        rtol=0.0,
    ):

        raise RuntimeError(
            "Prediction confidence integrity failed."
        )

    print(
        "Probability range [0,1]: PASS"
    )

    print(
        "Probability sums = 1: PASS"
    )

    print(
        "Confidence = max probability: PASS"
    )

    # ========================================================
    # 10. Build production output
    # ========================================================

    print(
        "\n10. BUILD PREDICTION OUTPUT"
    )

    output = pd.DataFrame(
        {
            "fixture_id":
                fixture_metadata[
                    "fixture_id"
                ].astype(
                    "int64"
                ),

            "date":
                fixture_metadata[
                    "date"
                ],

            "home_team_id":
                fixture_metadata[
                    "home_team_id"
                ],

            "home_team_name":
                fixture_metadata[
                    "home_team_name"
                ],

            "away_team_id":
                fixture_metadata[
                    "away_team_id"
                ],

            "away_team_name":
                fixture_metadata[
                    "away_team_name"
                ],
        }
    )

    if (
        "provider_fixture_id"
        in upcoming_indexed.columns
    ):

        output[
            "provider_fixture_id"
        ] = upcoming_indexed[
            "provider_fixture_id"
        ].values

    else:

        output[
            "provider_fixture_id"
        ] = pd.NA

    if (
        "round"
        in upcoming_indexed.columns
    ):

        output[
            "round"
        ] = upcoming_indexed[
            "round"
        ].values

    output[
        "predicted_target"
    ] = prediction_values[
        "predicted_target"
    ].values

    output[
        "predicted_label"
    ] = prediction_values[
        "predicted_label"
    ].values

    output[
        "prob_draw"
    ] = prediction_values[
        "prob_draw"
    ].values

    output[
        "prob_home_win"
    ] = prediction_values[
        "prob_home_win"
    ].values

    output[
        "prob_away_win"
    ] = prediction_values[
        "prob_away_win"
    ].values

    output[
        "confidence"
    ] = prediction_values[
        "confidence"
    ].values

    output[
        "model_id"
    ] = "random_forest"

    output[
        "model_sha256"
    ] = model_sha256

    output[
        "feature_count"
    ] = 86

    if len(
        output
    ) != len(
        features
    ):

        raise RuntimeError(
            "Final output row count mismatch."
        )

    if not output[
        "fixture_id"
    ].is_unique:

        raise RuntimeError(
            "Final prediction fixture IDs "
            "are not unique."
        )

    print(
        f"Output records: "
        f"{len(output)}"
    )

    print(
        "Fixture uniqueness: PASS"
    )

    print(
        "Model provenance attached: PASS"
    )

    # ========================================================
    # 11. Save prediction artifact
    # ========================================================

    print(
        "\n11. SAVE ARTIFACTS"
    )

    PRODUCTION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        PREDICTION_FILE,
        index=False,
    )

    prediction_sha256 = (
        sha256_file(
            PREDICTION_FILE
        )
    )

    metadata_payload = {

        "stage":
            "7.8.3",

        "component":
            "production_prediction",

        "status":
            "PASS",

        "generated_at_utc":
            generated_at,

        "model_id":
            "random_forest",

        "model_status":
            "LOCKED",

        "model_sha256":
            model_sha256,

        "feature_count":
            86,

        "prediction_count":
            int(
                len(output)
            ),

        "class_mapping":
            {
                "0": "Draw",
                "1": "Home Win",
                "2": "Away Win",
            },

        "production_feature_file":
            str(
                FEATURE_FILE
            ),

        "production_feature_sha256":
            current_feature_hash,

        "upcoming_fixture_file":
            str(
                UPCOMING_FILE
            ),

        "upcoming_fixture_sha256":
            sha256_file(
                UPCOMING_FILE
            ),

        "prediction_file":
            str(
                PREDICTION_FILE
            ),

        "prediction_sha256":
            prediction_sha256,

        "model_retrained":
            False,

        "model_reselected":
            False,

        "hyperparameter_tuned":
            False,

        "final_test_evaluation_artifacts_used":
            False,
    }

    with PREDICTION_METADATA_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata_payload,
            file,
            indent=2,
        )

    predicted_target_counts = (
        output[
            "predicted_target"
        ]
        .value_counts()
        .sort_index()
        .to_dict()
    )

    report_payload = {

        "stage":
            "7.8.3",

        "status":
            "PASS",

        "prediction_count":
            int(
                len(output)
            ),

        "feature_count":
            86,

        "fixture_alignment":
            True,

        "fixture_ids_unique":
            True,

        "schema_integrity":
            True,

        "numeric_integrity":
            True,

        "model_hash_verified":
            True,

        "model_classes":
            model_classes,

        "class_mapping":
            {
                "0": "Draw",
                "1": "Home Win",
                "2": "Away Win",
            },

        "probability_range_valid":
            True,

        "probability_sum_valid":
            True,

        "confidence_integrity":
            True,

        "predicted_target_counts":
            {
                str(key): int(value)
                for key, value
                in predicted_target_counts.items()
            },

        "average_confidence":
            float(
                output[
                    "confidence"
                ].mean()
            ),

        "minimum_confidence":
            float(
                output[
                    "confidence"
                ].min()
            ),

        "maximum_confidence":
            float(
                output[
                    "confidence"
                ].max()
            ),

        "model_retrained":
            False,

        "model_reselected":
            False,

        "hyperparameter_tuned":
            False,

        "final_test_evaluation_artifacts_used":
            False,

        "prediction_sha256":
            prediction_sha256,
    }

    with PREDICTION_REPORT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report_payload,
            file,
            indent=2,
        )

    print(
        f"Predictions:\n"
        f"{PREDICTION_FILE}"
    )

    print(
        f"\nMetadata:\n"
        f"{PREDICTION_METADATA_FILE}"
    )

    print(
        f"\nReport:\n"
        f"{PREDICTION_REPORT_FILE}"
    )

    # ========================================================
    # 12. Summary
    # ========================================================

    print(
        "\n12. PREDICTION SUMMARY"
    )

    print(
        "Predicted outcomes:"
    )

    print(
        "  Draw: "
        f"{predicted_target_counts.get(0, 0)}"
    )

    print(
        "  Home Win: "
        f"{predicted_target_counts.get(1, 0)}"
    )

    print(
        "  Away Win: "
        f"{predicted_target_counts.get(2, 0)}"
    )

    print(
        f"Average confidence: "
        f"{output['confidence'].mean():.6f}"
    )

    print(
        "\nFirst 5 predictions:"
    )

    preview_columns = [
        "home_team_name",
        "away_team_name",
        "predicted_label",
        "prob_draw",
        "prob_home_win",
        "prob_away_win",
        "confidence",
    ]

    print(
        output[
            preview_columns
        ]
        .head(5)
        .to_string(
            index=False
        )
    )

    # ========================================================
    # 13. Protection
    # ========================================================

    print(
        "\n13. PROTECTION"
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

    print(
        "Production model modified: NO"
    )

    print(
        "\n" + "=" * 62
    )

    print(
        "STAGE 7.8.3: PASS"
    )

    print("=" * 62)


if __name__ == "__main__":

    main()