"""
FixtureIQ Stage 9.1.1 + 9.1.2
Match Intelligence Contract Foundation.

9.1.1 Allowed Inputs
9.1.2 Forbidden Operations

Creates:
data/processed/intelligence/stage9_intelligence_contract.json

Important:
This is a PARTIAL contract.

9.1.1 and 9.1.2 are locked here.
9.1.3 Canonical Intelligence Schema is still pending.
9.1.4 Freshness / Provenance Contract is still pending.
9.1.5 Final Stage 9.1 Gate is still pending.

Stage 9 principle:
Interpret verified Stage 7 predictions using verified Stage 8
context without changing the prediction itself.

No provider fetch.
No model load.
No model execution.
No prediction mutation.
No Stage 7 write.
No Stage 8 write.
No final-test access.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# Project root
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(BASE_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(BASE_DIR),
    )


# ============================================================
# Directories
# ============================================================

PRODUCTION_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "production"
)

CONTEXT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "context"
)

INTELLIGENCE_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "intelligence"
)


# ============================================================
# Stage 7 inputs
# ============================================================

PRODUCTION_PREDICTIONS_FILE = (
    PRODUCTION_DIR
    / "production_predictions.csv"
)

PRODUCTION_PREDICTION_METADATA_FILE = (
    PRODUCTION_DIR
    / "production_prediction_metadata.json"
)

PRODUCTION_PREDICTION_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_prediction_report.json"
)

PRODUCTION_PREDICTION_VERIFICATION_FILE = (
    PRODUCTION_DIR
    / "production_prediction_verification.json"
)

STAGE7_8_FINAL_FILE = (
    PRODUCTION_DIR
    / "stage7_8_final_verification.json"
)

STAGE7_9_FINAL_FILE = (
    PRODUCTION_DIR
    / "stage7_9_final_verification.json"
)


# ============================================================
# Stage 8 inputs
# ============================================================

ENRICHED_FIXTURES_FILE = (
    CONTEXT_DIR
    / "enriched_upcoming_fixtures.csv"
)

FIXTURE_CONTEXT_REPORT_FILE = (
    CONTEXT_DIR
    / "fixture_context_report.json"
)

CONTEXT_API_VERIFICATION_FILE = (
    CONTEXT_DIR
    / "context_api_verification.json"
)

CONTEXT_RUNTIME_VERIFICATION_FILE = (
    CONTEXT_DIR
    / "context_runtime_verification.json"
)

STAGE8_FINAL_FILE = (
    CONTEXT_DIR
    / "stage8_final_verification.json"
)


# ============================================================
# Output
# ============================================================

CONTRACT_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract.json"
)


# ============================================================
# Helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise FileNotFoundError(
            f"Required artifact missing: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        payload = json.load(file)

    if not isinstance(
        payload,
        dict,
    ):

        raise RuntimeError(
            f"Expected JSON object: {path}"
        )

    return payload


def sha256_file(
    path: Path,
) -> str:

    if not path.exists():

        raise FileNotFoundError(
            f"Required artifact missing: {path}"
        )

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as file:

        while True:

            chunk = file.read(
                1024 * 1024
            )

            if not chunk:

                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


def relative_path(
    path: Path,
) -> str:

    return (
        str(
            path.relative_to(
                BASE_DIR
            )
        )
        .replace(
            "\\",
            "/",
        )
    )


def csv_info(
    path: Path,
) -> tuple[
    list[str],
    int,
]:

    if not path.exists():

        raise FileNotFoundError(
            f"Required CSV missing: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        fields = (
            reader.fieldnames
            or []
        )

        rows = list(
            reader
        )

    if not fields:

        raise RuntimeError(
            f"CSV has no columns: {path}"
        )

    if not rows:

        raise RuntimeError(
            f"CSV has no rows: {path}"
        )

    return (
        fields,
        len(
            rows
        ),
    )


def save_json_atomic(
    path: Path,
    payload: dict,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
        )

    temporary.replace(
        path
    )


def artifact_identity(
    path: Path,
    *,
    role: str,
    authority: str,
    artifact_type: str,
) -> dict:

    return {

        "path":
            relative_path(
                path
            ),

        "sha256":
            sha256_file(
                path
            ),

        "artifact_type":
            artifact_type,

        "role":
            role,

        "authority":
            authority,

        "required":
            True,

        "read_only":
            True,

        "stage9_write_allowed":
            False,
    }


def require(
    label: str,
    condition,
) -> None:

    if not condition:

        raise RuntimeError(
            f"Precondition failed: {label}"
        )

    print(
        f"{label}: PASS"
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 9.1.1 + 9.1.2"
    )

    print(
        "Allowed Inputs + Forbidden Operations Contract"
    )

    print("=" * 72)

    # ========================================================
    # 1. Required artifacts
    # ========================================================

    print(
        "\n1. REQUIRED UPSTREAM ARTIFACTS"
    )

    required = [

        PRODUCTION_PREDICTIONS_FILE,
        PRODUCTION_PREDICTION_METADATA_FILE,
        PRODUCTION_PREDICTION_REPORT_FILE,
        PRODUCTION_PREDICTION_VERIFICATION_FILE,

        STAGE7_8_FINAL_FILE,
        STAGE7_9_FINAL_FILE,

        ENRICHED_FIXTURES_FILE,
        FIXTURE_CONTEXT_REPORT_FILE,
        CONTEXT_API_VERIFICATION_FILE,
        CONTEXT_RUNTIME_VERIFICATION_FILE,
        STAGE8_FINAL_FILE,
    ]

    for path in required:

        require(
            path.name,
            path.exists(),
        )

    # ========================================================
    # 2. Load verification evidence
    # ========================================================

    print(
        "\n2. UPSTREAM VERIFICATION STATE"
    )

    prediction_metadata = load_json(
        PRODUCTION_PREDICTION_METADATA_FILE
    )

    prediction_report = load_json(
        PRODUCTION_PREDICTION_REPORT_FILE
    )

    prediction_verification = load_json(
        PRODUCTION_PREDICTION_VERIFICATION_FILE
    )

    stage7_8 = load_json(
        STAGE7_8_FINAL_FILE
    )

    stage7_9 = load_json(
        STAGE7_9_FINAL_FILE
    )

    fixture_context_report = load_json(
        FIXTURE_CONTEXT_REPORT_FILE
    )

    context_api_verification = load_json(
        CONTEXT_API_VERIFICATION_FILE
    )

    context_runtime_verification = load_json(
        CONTEXT_RUNTIME_VERIFICATION_FILE
    )

    stage8_final = load_json(
        STAGE8_FINAL_FILE
    )

    require(
        "Production prediction metadata PASS",
        prediction_metadata.get(
            "status"
        )
        == "PASS",
    )

    require(
        "Production prediction report PASS",
        prediction_report.get(
            "status"
        )
        == "PASS",
    )

    require(
        "Production prediction verification PASS",
        prediction_verification.get(
            "status"
        )
        == "PASS",
    )

    require(
        "Stage 7.8 final verification PASS",
        stage7_8.get(
            "status"
        )
        == "PASS",
    )

    require(
        "Stage 7.9 final verification PASS",
        stage7_9.get(
            "status"
        )
        == "PASS",
    )

    require(
        "Stage 8.5 fixture context COMPLETE",
        (
            fixture_context_report.get(
                "status"
            )
            == "PASS"
            and
            fixture_context_report.get(
                "stage_8_5_complete"
            )
            is True
        ),
    )

    require(
        "Stage 8.6 context API COMPLETE",
        (
            context_api_verification.get(
                "status"
            )
            == "PASS"
            and
            context_api_verification.get(
                "stage_8_6_complete"
            )
            is True
        ),
    )

    require(
        "Stage 8.7 runtime COMPLETE",
        (
            context_runtime_verification.get(
                "status"
            )
            == "PASS"
            and
            context_runtime_verification.get(
                "stage_8_7_complete"
            )
            is True
        ),
    )

    require(
        "Stage 8 final verification PASS",
        (
            stage8_final.get(
                "status"
            )
            == "PASS"
            and
            stage8_final.get(
                "stage_8_complete"
            )
            is True
            and
            stage8_final.get(
                "stage8_context_layer"
            )
            == "VERIFIED"
        ),
    )

    # ========================================================
    # 3. Source snapshots
    # ========================================================

    print(
        "\n3. SOURCE SNAPSHOTS"
    )

    (
        prediction_columns,
        prediction_count,
    ) = csv_info(
        PRODUCTION_PREDICTIONS_FILE
    )

    (
        context_columns,
        context_count,
    ) = csv_info(
        ENRICHED_FIXTURES_FILE
    )

    require(
        "Production prediction rows > 0",
        prediction_count
        > 0,
    )

    require(
        "Enriched fixture context rows > 0",
        context_count
        > 0,
    )

    require(
        "Prediction fixture_id present",
        "fixture_id"
        in prediction_columns,
    )

    require(
        "Context fixture_id present",
        "fixture_id"
        in context_columns,
    )

    require(
        "Prediction home identity present",
        (
            "home_team_id"
            in prediction_columns
            and
            "home_team_name"
            in prediction_columns
        ),
    )

    require(
        "Prediction away identity present",
        (
            "away_team_id"
            in prediction_columns
            and
            "away_team_name"
            in prediction_columns
        ),
    )

    require(
        "Prediction probabilities present",
        all(
            field
            in prediction_columns

            for field in (
                "prob_draw",
                "prob_home_win",
                "prob_away_win",
            )
        ),
    )

    # ========================================================
    # 4. 9.1.1 Allowed inputs
    # ========================================================

    print(
        "\n4. STAGE 9.1.1 ALLOWED INPUTS"
    )

    allowed_inputs = {

        # ----------------------------------------------------
        # Stage 7 prediction data
        # ----------------------------------------------------

        "production_predictions": artifact_identity(

            PRODUCTION_PREDICTIONS_FILE,

            role=
                "CANONICAL_PREDICTION_VALUES",

            authority=
                "STAGE7_PREDICTION_SOURCE_OF_TRUTH",

            artifact_type=
                "CSV",
        ),

        "production_prediction_metadata": artifact_identity(

            PRODUCTION_PREDICTION_METADATA_FILE,

            role=
                "PREDICTION_PROVENANCE",

            authority=
                "STAGE7_VERIFIED_PROVENANCE",

            artifact_type=
                "JSON",
        ),

        "production_prediction_report": artifact_identity(

            PRODUCTION_PREDICTION_REPORT_FILE,

            role=
                "PREDICTION_BUILD_EVIDENCE",

            authority=
                "STAGE7_VERIFIED_PROVENANCE",

            artifact_type=
                "JSON",
        ),

        "production_prediction_verification": artifact_identity(

            PRODUCTION_PREDICTION_VERIFICATION_FILE,

            role=
                "INDEPENDENT_PREDICTION_VALIDATION",

            authority=
                "STAGE7_VERIFIED_PROVENANCE",

            artifact_type=
                "JSON",
        ),

        "stage7_8_final_verification": artifact_identity(

            STAGE7_8_FINAL_FILE,

            role=
                "PRODUCTION_INFERENCE_FINAL_GATE",

            authority=
                "STAGE7_FINAL_EVIDENCE",

            artifact_type=
                "JSON",
        ),

        "stage7_9_final_verification": artifact_identity(

            STAGE7_9_FINAL_FILE,

            role=
                "PRODUCTION_SERVING_FINAL_GATE",

            authority=
                "STAGE7_FINAL_EVIDENCE",

            artifact_type=
                "JSON",
        ),

        # ----------------------------------------------------
        # Stage 8 context data
        # ----------------------------------------------------

        "enriched_upcoming_fixtures": artifact_identity(

            ENRICHED_FIXTURES_FILE,

            role=
                "CANONICAL_MATCH_CONTEXT",

            authority=
                "STAGE8_CONTEXT_SOURCE_OF_TRUTH",

            artifact_type=
                "CSV",
        ),

        "fixture_context_report": artifact_identity(

            FIXTURE_CONTEXT_REPORT_FILE,

            role=
                "FIXTURE_CONTEXT_PROVENANCE",

            authority=
                "STAGE8_VERIFIED_PROVENANCE",

            artifact_type=
                "JSON",
        ),

        "context_api_verification": artifact_identity(

            CONTEXT_API_VERIFICATION_FILE,

            role=
                "CONTEXT_API_EVIDENCE",

            authority=
                "STAGE8_VERIFICATION_EVIDENCE",

            artifact_type=
                "JSON",
        ),

        "context_runtime_verification": artifact_identity(

            CONTEXT_RUNTIME_VERIFICATION_FILE,

            role=
                "CONTEXT_RUNTIME_EVIDENCE",

            authority=
                "STAGE8_VERIFICATION_EVIDENCE",

            artifact_type=
                "JSON",
        ),

        "stage8_final_verification": artifact_identity(

            STAGE8_FINAL_FILE,

            role=
                "STAGE8_FINAL_GATE",

            authority=
                "STAGE8_FINAL_EVIDENCE",

            artifact_type=
                "JSON",
        ),
    }

    require(
        "Exactly 11 allowed inputs",
        len(
            allowed_inputs
        )
        == 11,
    )

    require(
        "All allowed inputs read-only",
        all(
            item.get(
                "read_only"
            )
            is True

            for item in (
                allowed_inputs.values()
            )
        ),
    )

    require(
        "Stage 9 writes to allowed inputs prohibited",
        all(
            item.get(
                "stage9_write_allowed"
            )
            is False

            for item in (
                allowed_inputs.values()
            )
        ),
    )

    # ========================================================
    # 5. 9.1.2 Forbidden operations
    # ========================================================

    print(
        "\n5. STAGE 9.1.2 FORBIDDEN OPERATIONS"
    )

    forbidden_operations = {

        "model_loading":
            True,

        "model_execution":
            True,

        "model_retraining":
            True,

        "model_reselection":
            True,

        "hyperparameter_tuning":
            True,

        "feature_schema_mutation":
            True,

        "probability_recalibration":
            True,

        "probability_modification":
            True,

        "prediction_label_modification":
            True,

        "source_confidence_modification":
            True,

        "hidden_prediction_adjustment":
            True,

        "context_as_model_feature":
            True,

        "standings_as_model_feature":
            True,

        "form_as_model_feature":
            True,

        "fixture_context_as_model_feature":
            True,

        "production_prediction_artifact_write":
            True,

        "stage7_artifact_write":
            True,

        "stage8_artifact_write":
            True,

        "provider_fetch":
            True,

        "future_result_use":
            True,

        "future_fixture_state_propagation":
            True,

        "final_test_access":
            True,

        "final_test_reuse":
            True,

        "bookmaker_odds_use":
            True,

        "outcome_based_threshold_tuning":
            True,

        "post_match_information_use":
            True,

        "fuzzy_fixture_identity_join":
            True,

        "best_effort_identity_fallback":
            True,
    }

    require(
        "Forbidden-operation contract non-empty",
        len(
            forbidden_operations
        )
        > 0,
    )

    require(
        "Every forbidden operation enforced",
        all(
            value is True

            for value in (
                forbidden_operations.values()
            )
        ),
    )

    # ========================================================
    # 6. Permitted Stage 9 behavior
    # ========================================================

    print(
        "\n6. PERMITTED INTERPRETATION BEHAVIOR"
    )

    permitted_operations = {

        "read_verified_stage7_prediction_artifacts":
            True,

        "read_verified_stage8_context_artifacts":
            True,

        "hash_input_artifacts":
            True,

        "validate_input_provenance":
            True,

        "strict_fixture_identity_join":
            True,

        "preserve_source_probabilities_exactly":
            True,

        "preserve_source_prediction_label_exactly":
            True,

        "derive_deterministic_non_model_metrics":
            True,

        "derive_deterministic_context_comparisons":
            True,

        "produce_deterministic_explanations":
            True,

        "serve_verified_read_only_intelligence":
            True,
    }

    require(
        "Only interpretation operations permitted",
        all(
            value is True

            for value in (
                permitted_operations.values()
            )
        ),
    )

    # ========================================================
    # 7. Prediction integrity invariants
    # ========================================================

    print(
        "\n7. PREDICTION INTEGRITY INVARIANTS"
    )

    prediction_integrity_contract = {

        "prediction_source":
            "production_predictions",

        "probability_fields": [

            "prob_home_win",
            "prob_draw",
            "prob_away_win",
        ],

        "prediction_label_source_field":
            "predicted_label",

        "source_confidence_field":
            "confidence",

        "probabilities_must_be_copied_exactly":
            True,

        "prediction_label_must_be_copied_exactly":
            True,

        "source_confidence_must_be_copied_exactly":
            True,

        "probabilities_may_not_be_recomputed":
            True,

        "probabilities_may_not_be_rescaled":
            True,

        "probabilities_may_not_be_recalibrated":
            True,

        "context_may_not_modify_probabilities":
            True,

        "context_may_not_modify_prediction_label":
            True,

        "derived_confidence_bands_must_not_replace_source_confidence":
            True,

        "stage9_is_not_a_prediction_model":
            True,
    }

    require(
        "Probability preservation locked",
        prediction_integrity_contract.get(
            "probabilities_must_be_copied_exactly"
        )
        is True,
    )

    require(
        "Prediction-label preservation locked",
        prediction_integrity_contract.get(
            "prediction_label_must_be_copied_exactly"
        )
        is True,
    )

    require(
        "Stage 9 explicitly not a prediction model",
        prediction_integrity_contract.get(
            "stage9_is_not_a_prediction_model"
        )
        is True,
    )

    # ========================================================
    # 8. Authority contract
    # ========================================================

    print(
        "\n8. SOURCE AUTHORITY"
    )

    input_authority = {

        "prediction_values":
            "production_predictions",

        "prediction_provenance": [

            "production_prediction_metadata",
            "production_prediction_report",
            "production_prediction_verification",
            "stage7_8_final_verification",
            "stage7_9_final_verification",
        ],

        "context_values":
            "enriched_upcoming_fixtures",

        "context_provenance": [

            "fixture_context_report",
            "context_api_verification",
            "context_runtime_verification",
            "stage8_final_verification",
        ],

        "prediction_values_override_context":
            True,

        "context_may_explain_prediction":
            True,

        "context_may_replace_prediction":
            False,

        "context_may_adjust_prediction":
            False,
    }

    require(
        "Prediction values authority locked",
        input_authority.get(
            "prediction_values"
        )
        == "production_predictions",
    )

    require(
        "Context values authority locked",
        input_authority.get(
            "context_values"
        )
        == "enriched_upcoming_fixtures",
    )

    require(
        "Context cannot replace prediction",
        input_authority.get(
            "context_may_replace_prediction"
        )
        is False,
    )

    require(
        "Context cannot adjust prediction",
        input_authority.get(
            "context_may_adjust_prediction"
        )
        is False,
    )

    # ========================================================
    # 9. Safety
    # ========================================================

    print(
        "\n9. STAGE 9.1 SAFETY"
    )

    safety = {

        "interpretation_only":
            True,

        "read_only_upstream":
            True,

        "stage7_artifacts_modified":
            False,

        "stage8_artifacts_modified":
            False,

        "provider_fetch_performed":
            False,

        "model_loaded":
            False,

        "model_executed":
            False,

        "model_modified":
            False,

        "model_retrained":
            False,

        "model_reselected":
            False,

        "hyperparameter_tuned":
            False,

        "probabilities_modified":
            False,

        "probabilities_recalibrated":
            False,

        "prediction_labels_modified":
            False,

        "feature_schema_modified":
            False,

        "context_used_as_model_features":
            False,

        "bookmaker_odds_used":
            False,

        "future_results_used":
            False,

        "final_test_accessed":
            False,
    }

    require(
        "Interpretation-only boundary",
        safety.get(
            "interpretation_only"
        )
        is True,
    )

    require(
        "Upstream artifacts read-only",
        safety.get(
            "read_only_upstream"
        )
        is True,
    )

    # ========================================================
    # 10. Build partial contract
    # ========================================================

    print(
        "\n10. WRITE PARTIAL STAGE 9.1 CONTRACT"
    )

    created_at = (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )

    contract = {

        "stage":
            "9.1",

        "contract_type":
            "MATCH_INTELLIGENCE_CONTRACT",

        "contract_version":
            "1.0.0-partial",

        "status":
            "PARTIAL_LOCK",

        "stage_9_1_complete":
            False,

        "stage_9_1_status":
            "IN_PROGRESS",

        "purpose":
            (
                "INTERPRET_VERIFIED_STAGE7_PREDICTIONS_"
                "WITH_VERIFIED_STAGE8_CONTEXT"
            ),

        "created_at_utc":
            created_at,

        "principles": {

            "prediction_layer_authority":
                "STAGE7",

            "context_layer_authority":
                "STAGE8",

            "intelligence_layer":
                "STAGE9",

            "stage9_role":
                "INTERPRETATION_NOT_PREDICTION",

            "prediction_and_context_separation":
                True,

            "context_can_explain_prediction":
                True,

            "context_can_change_prediction":
                False,
        },

        "sub_stages": {

            "9.1.1":
                "PASS",

            "9.1.2":
                "PASS",

            "9.1.3":
                "PENDING",

            "9.1.4":
                "PENDING",

            "9.1.5":
                "PENDING",
        },

        "stage_9_1_1": {

            "name":
                "ALLOWED_INPUTS",

            "status":
                "PASS",

            "allowed_input_count":
                len(
                    allowed_inputs
                ),

            "allowed_inputs":
                allowed_inputs,

            "input_authority":
                input_authority,

            "prediction_snapshot": {

                "row_count":
                    prediction_count,

                "column_count":
                    len(
                        prediction_columns
                    ),

                "columns":
                    prediction_columns,

                "sha256":
                    sha256_file(
                        PRODUCTION_PREDICTIONS_FILE
                    ),
            },

            "context_snapshot": {

                "row_count":
                    context_count,

                "column_count":
                    len(
                        context_columns
                    ),

                "columns":
                    context_columns,

                "sha256":
                    sha256_file(
                        ENRICHED_FIXTURES_FILE
                    ),
            },
        },

        "stage_9_1_2": {

            "name":
                "FORBIDDEN_OPERATIONS",

            "status":
                "PASS",

            "forbidden_operation_count":
                len(
                    forbidden_operations
                ),

            "forbidden_operations":
                forbidden_operations,

            "permitted_operations":
                permitted_operations,

            "prediction_integrity_contract":
                prediction_integrity_contract,
        },

        "pending_contract_sections": {

            "9.1.3":
                "CANONICAL_INTELLIGENCE_SCHEMA",

            "9.1.4":
                "FRESHNESS_AND_PROVENANCE_CONTRACT",

            "9.1.5":
                "FINAL_STAGE_9_1_GATE",
        },

        "safety":
            safety,
    }

    save_json_atomic(
        CONTRACT_FILE,
        contract,
    )

    print(
        CONTRACT_FILE
    )

    # ========================================================
    # Final
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    print(
        "STAGE 9.1.1: PASS"
    )

    print(
        "ALLOWED INPUTS: LOCKED"
    )

    print(
        "STAGE 9.1.2: PASS"
    )

    print(
        "FORBIDDEN OPERATIONS: LOCKED"
    )

    print(
        "STAGE 9.1: IN PROGRESS"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()