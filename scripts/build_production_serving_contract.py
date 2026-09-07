"""
FixtureIQ Stage 7.9.1
Production Serving Contract Builder.

Creates the immutable contract used by the production
prediction repository and future HTTP API layer.

This stage does not:
- load the ML model
- execute predictions
- train
- tune
- select models
- access final-test evaluation artifacts
"""

from __future__ import annotations

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

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

INFERENCE_CONTRACT_FILE = (
    MODEL_DIR
    / "production_inference_contract.json"
)

STAGE_7_8_FINAL_FILE = (
    PRODUCTION_DIR
    / "stage7_8_final_verification.json"
)

OUTPUT_FILE = (
    MODEL_DIR
    / "production_serving_contract.json"
)


EXPECTED_FEATURE_COUNT = 86
EXPECTED_MODEL_ID = "random_forest"


def load_json(path: Path) -> dict:

    if not path.exists():
        raise FileNotFoundError(
            f"Required file missing: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        payload = json.load(file)

    if not isinstance(payload, dict):
        raise RuntimeError(
            f"Expected JSON object: {path}"
        )

    return payload


def require(
    condition: bool,
    message: str,
):

    if not condition:
        raise RuntimeError(message)


def main():

    print("=" * 64)
    print("FixtureIQ Stage 7.9.1")
    print("Production Serving Contract Builder")
    print("=" * 64)

    inference_contract = load_json(
        INFERENCE_CONTRACT_FILE
    )

    stage_7_8 = load_json(
        STAGE_7_8_FINAL_FILE
    )

    print("\n1. UPSTREAM CONTRACT")

    require(
        inference_contract.get("stage")
        == "7.8.1",
        "Invalid Stage 7.8.1 inference contract.",
    )

    require(
        inference_contract.get("status")
        == "LOCKED_CONTRACT",
        "Production inference contract is not locked.",
    )

    model = inference_contract.get(
        "model",
        {},
    )

    require(
        model.get("candidate_id")
        == EXPECTED_MODEL_ID,
        "Unexpected production model.",
    )

    require(
        model.get("status")
        == "LOCKED",
        "Production model is not locked.",
    )

    feature_columns = inference_contract.get(
        "feature_columns",
        [],
    )

    require(
        len(feature_columns)
        == EXPECTED_FEATURE_COUNT,
        "Expected 86 production model features.",
    )

    print("Stage 7.8.1 contract: PASS")
    print("Model: random_forest")
    print("Model status: LOCKED")
    print("Feature count: 86")

    print("\n2. STAGE 7.8 FINAL VERIFICATION")

    require(
        stage_7_8.get("stage")
        == "7.8.5",
        "Stage 7.8 final verification missing.",
    )

    require(
        stage_7_8.get("status")
        == "PASS",
        "Stage 7.8 final verification did not PASS.",
    )

    require(
        stage_7_8.get("stage_7_8_status")
        == "COMPLETE",
        "Stage 7.8 is not COMPLETE.",
    )

    require(
        stage_7_8.get("model_id")
        == EXPECTED_MODEL_ID,
        "Stage 7.8 model ID mismatch.",
    )

    require(
        stage_7_8.get("model_status")
        == "LOCKED",
        "Stage 7.8 model is not locked.",
    )

    require(
        stage_7_8.get("feature_count")
        == EXPECTED_FEATURE_COUNT,
        "Stage 7.8 feature count mismatch.",
    )

    require(
        stage_7_8.get("final_test_status")
        == "CONSUMED",
        "Final-test lifecycle is not CONSUMED.",
    )

    require(
        stage_7_8.get(
            "final_test_evaluation_artifacts_used"
        )
        is False,
        "Stage 7.8 used forbidden final-test artifacts.",
    )

    model_sha256 = str(
        stage_7_8.get(
            "model_sha256",
            "",
        )
    ).lower()

    require(
        len(model_sha256) == 64,
        "Missing valid production model SHA256.",
    )

    print("Stage 7.8.5: PASS")
    print("Stage 7.8: COMPLETE")
    print("Final test: CONSUMED")

    print("\n3. BUILD SERVING CONTRACT")

    public_field_order = [
        "fixture_id",
        "provider_fixture_id",
        "date",
        "round",

        "home_team_id",
        "home_team_name",
        "away_team_id",
        "away_team_name",

        "predicted_target",
        "predicted_label",

        "prob_home_win",
        "prob_draw",
        "prob_away_win",

        "confidence",
    ]

    required_public_fields = [
        "fixture_id",
        "date",

        "home_team_id",
        "home_team_name",
        "away_team_id",
        "away_team_name",

        "predicted_target",
        "predicted_label",

        "prob_home_win",
        "prob_draw",
        "prob_away_win",

        "confidence",
    ]

    optional_public_fields = [
        "provider_fixture_id",
        "round",
    ]

    source_required_columns = (
        required_public_fields
        + [
            "model_id",
            "model_sha256",
            "feature_count",
        ]
    )

    contract = {

        "stage":
            "7.9.1",

        "contract_version":
            "1.0.0",

        "status":
            "LOCKED_SERVING_CONTRACT",

        "depends_on":
            {
                "stage":
                    "7.8.5",

                "required_status":
                    "PASS",

                "required_stage_7_8_status":
                    "COMPLETE",
            },

        "model":
            {
                "model_id":
                    EXPECTED_MODEL_ID,

                "status":
                    "LOCKED",

                "sha256":
                    model_sha256,

                "feature_count":
                    EXPECTED_FEATURE_COUNT,
            },

        "target_mapping":
            {
                "0":
                    "Draw",

                "1":
                    "Home Win",

                "2":
                    "Away Win",
            },

        "probability_mapping":
            {
                "0":
                    "prob_draw",

                "1":
                    "prob_home_win",

                "2":
                    "prob_away_win",
            },

        "source_artifacts":
            {
                "selected_model":
                    {
                        "path":
                            "data/processed/model/selected/"
                            "selected_model.joblib",

                        "access":
                            "HASH_ONLY",
                    },

                "stage_7_8_final_verification":
                    {
                        "path":
                            "data/processed/production/"
                            "stage7_8_final_verification.json",

                        "access":
                            "READ_ONLY",
                    },

                "production_predictions":
                    {
                        "path":
                            "data/processed/production/"
                            "production_predictions.csv",

                        "access":
                            "READ_ONLY",
                    },

                "production_prediction_metadata":
                    {
                        "path":
                            "data/processed/production/"
                            "production_prediction_metadata.json",

                        "access":
                            "READ_ONLY",
                    },

                "production_prediction_report":
                    {
                        "path":
                            "data/processed/production/"
                            "production_prediction_report.json",

                        "access":
                            "READ_ONLY",
                    },

                "production_features":
                    {
                        "path":
                            "data/processed/production/"
                            "production_features.csv",

                        "access":
                            "HASH_ONLY",
                    },

                "upcoming_fixtures":
                    {
                        "path":
                            "data/processed/production/"
                            "upcoming_fixtures.csv",

                        "access":
                            "HASH_ONLY",
                    },
            },

        "source_required_columns":
            source_required_columns,

        "public_prediction_schema":
            {
                "field_order":
                    public_field_order,

                "required_fields":
                    required_public_fields,

                "optional_fields":
                    optional_public_fields,
            },

        "serving_policy":
            {
                "mode":
                    "READ_ONLY",

                "validation":
                    "FAIL_CLOSED",

                "snapshot_requirement":
                    "VERIFIED_STAGE_7_8",

                "kickoff_rule":
                    "FIXTURE_DATE_GT_CURRENT_UTC",

                "stale_snapshot_action":
                    "NOT_READY",

                "fixture_order":
                    "DATE_ASC",

                "team_matching":
                    "CASE_INSENSITIVE_EXACT",

                "unknown_fixture_result":
                    "NONE",

                "allow_partial_stale_snapshot":
                    False,
            },

        "protection":
            {
                "model_loading_allowed":
                    False,

                "prediction_execution_allowed":
                    False,

                "provider_fetching_allowed":
                    False,

                "feature_construction_allowed":
                    False,

                "training_allowed":
                    False,

                "retraining_allowed":
                    False,

                "model_selection_allowed":
                    False,

                "hyperparameter_tuning_allowed":
                    False,

                "model_modification_allowed":
                    False,

                "final_test_evaluation_artifact_access_allowed":
                    False,
            },

        "failure_behavior":
            {
                "artifact_missing":
                    "NOT_READY",

                "artifact_hash_mismatch":
                    "NOT_READY",

                "schema_mismatch":
                    "NOT_READY",

                "probability_integrity_failure":
                    "NOT_READY",

                "model_provenance_failure":
                    "NOT_READY",

                "stage_7_8_unverified":
                    "NOT_READY",

                "snapshot_stale":
                    "NOT_READY",
            },
    }

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            contract,
            file,
            indent=2,
            sort_keys=True,
        )

    print("Serving contract created: PASS")

    print("\n4. PROTECTION")
    print("Model loaded: NO")
    print("Prediction executed: NO")
    print("Training: NO")
    print("Model selection: NO")
    print("Hyperparameter tuning: NO")
    print("Final-test evaluation artifacts read: NO")

    print("\n5. OUTPUT")
    print(OUTPUT_FILE)

    print("\n" + "=" * 64)
    print("STAGE 7.9.1 CONTRACT BUILD: PASS")
    print("=" * 64)


if __name__ == "__main__":
    main()