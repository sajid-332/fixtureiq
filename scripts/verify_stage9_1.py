"""
FixtureIQ Stage 9.1.5
Final Stage 9.1 Match Intelligence Contract Gate.

Verifies and permanently promotes:

9.1.1 Allowed Inputs
9.1.2 Forbidden Operations
9.1.3 Canonical Intelligence Schema
9.1.4 Freshness & Provenance Contract
9.1.5 Final Stage 9.1 Gate

Updates only:

data/processed/intelligence/
    stage9_intelligence_contract.json
    stage9_intelligence_contract_verification.json

Safety:
- no provider fetch
- no model loading
- no model execution
- no prediction generation
- no probability mutation
- no Stage 7 writes
- no Stage 8 writes
- no final-test access
"""

from __future__ import annotations

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
# Stage 7 artifacts
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
# Stage 8 artifacts
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
# Stage 9.1 artifacts
# ============================================================

CONTRACT_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract.json"
)

VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract_verification.json"
)


# ============================================================
# Expected allowed inputs
# ============================================================

EXPECTED_ALLOWED_INPUTS = {

    "production_predictions":
        PRODUCTION_PREDICTIONS_FILE,

    "production_prediction_metadata":
        PRODUCTION_PREDICTION_METADATA_FILE,

    "production_prediction_report":
        PRODUCTION_PREDICTION_REPORT_FILE,

    "production_prediction_verification":
        PRODUCTION_PREDICTION_VERIFICATION_FILE,

    "stage7_8_final_verification":
        STAGE7_8_FINAL_FILE,

    "stage7_9_final_verification":
        STAGE7_9_FINAL_FILE,

    "enriched_upcoming_fixtures":
        ENRICHED_FIXTURES_FILE,

    "fixture_context_report":
        FIXTURE_CONTEXT_REPORT_FILE,

    "context_api_verification":
        CONTEXT_API_VERIFICATION_FILE,

    "context_runtime_verification":
        CONTEXT_RUNTIME_VERIFICATION_FILE,

    "stage8_final_verification":
        STAGE8_FINAL_FILE,
}


# ============================================================
# Expected Stage 9 outputs
# ============================================================

EXPECTED_OUTPUTS = {

    "stage9_intelligence_contract":
        (
            "data/processed/intelligence/"
            "stage9_intelligence_contract.json"
        ),

    "stage9_intelligence_contract_verification":
        (
            "data/processed/intelligence/"
            "stage9_intelligence_contract_verification.json"
        ),

    "match_intelligence_base":
        (
            "data/processed/intelligence/"
            "match_intelligence_base.csv"
        ),

    "match_intelligence_base_report":
        (
            "data/processed/intelligence/"
            "match_intelligence_base_report.json"
        ),

    "match_intelligence":
        (
            "data/processed/intelligence/"
            "match_intelligence.csv"
        ),

    "match_intelligence_report":
        (
            "data/processed/intelligence/"
            "match_intelligence_report.json"
        ),

    "intelligence_api_verification":
        (
            "data/processed/intelligence/"
            "intelligence_api_verification.json"
        ),

    "intelligence_runtime_verification":
        (
            "data/processed/intelligence/"
            "intelligence_runtime_verification.json"
        ),

    "stage9_final_verification":
        (
            "data/processed/intelligence/"
            "stage9_final_verification.json"
        ),
}


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

        payload = json.load(
            file
        )

    if not isinstance(
        payload,
        dict,
    ):

        raise RuntimeError(
            f"Expected JSON object: {path}"
        )

    return payload


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


def check(
    label: str,
    condition,
    failures: list[str],
) -> bool:

    passed = bool(
        condition
    )

    print(
        f"{label}: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    if not passed:

        failures.append(
            label
        )

    return passed


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 9.1.5"
    )

    print(
        "FINAL MATCH INTELLIGENCE CONTRACT GATE"
    )

    print("=" * 72)

    failures = []

    # ========================================================
    # 1. Required files
    # ========================================================

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    required = (

        list(
            EXPECTED_ALLOWED_INPUTS.values()
        )
        +
        [
            CONTRACT_FILE,
            VERIFICATION_FILE,
        ]
    )

    for path in required:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        sys.exit(1)

    # ========================================================
    # Protect upstream identities
    # ========================================================

    upstream_before = {

        name:
            sha256_file(
                path
            )

        for name, path in (
            EXPECTED_ALLOWED_INPUTS.items()
        )
    }

    # ========================================================
    # Load files
    # ========================================================

    contract = load_json(
        CONTRACT_FILE
    )

    verification = load_json(
        VERIFICATION_FILE
    )

    stage7_8 = load_json(
        STAGE7_8_FINAL_FILE
    )

    stage7_9 = load_json(
        STAGE7_9_FINAL_FILE
    )

    stage8_final = load_json(
        STAGE8_FINAL_FILE
    )

    # ========================================================
    # Idempotent already-complete path
    # ========================================================

    already_complete = (

        contract.get(
            "stage_9_1_complete"
        )
        is True

        and

        contract.get(
            "stage_9_1_status"
        )
        == "COMPLETE"

        and

        contract.get(
            "status"
        )
        ==
        "LOCKED_MATCH_INTELLIGENCE_CONTRACT"

        and

        contract.get(
            "sub_stages",
            {}
        ).get(
            "9.1.5"
        )
        == "PASS"

        and

        verification.get(
            "status"
        )
        == "PASS"

        and

        verification.get(
            "stage_9_1_complete"
        )
        is True
    )

    if already_complete:

        print(
            "\nStage 9.1 is already locked."
        )

        print(
            "Running integrity verification only."
        )

    # ========================================================
    # 2. Upstream gates
    # ========================================================

    print(
        "\n2. UPSTREAM FINAL GATES"
    )

    check(
        "Stage 7.8 PASS",
        stage7_8.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 7.9 PASS",
        stage7_9.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 8 final PASS",
        stage8_final.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 8 COMPLETE",
        stage8_final.get(
            "stage_8_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 8 Context Layer VERIFIED",
        stage8_final.get(
            "stage8_context_layer"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 3. Contract identity
    # ========================================================

    print(
        "\n3. CONTRACT IDENTITY"
    )

    check(
        "Contract stage = 9.1",
        contract.get(
            "stage"
        )
        == "9.1",
        failures,
    )

    check(
        "Contract type correct",
        contract.get(
            "contract_type"
        )
        ==
        "MATCH_INTELLIGENCE_CONTRACT",
        failures,
    )

    check(
        "Stage 9 role = interpretation",
        contract.get(
            "principles",
            {}
        ).get(
            "stage9_role"
        )
        ==
        "INTERPRETATION_NOT_PREDICTION",
        failures,
    )

    check(
        "Prediction authority = Stage 7",
        contract.get(
            "principles",
            {}
        ).get(
            "prediction_layer_authority"
        )
        == "STAGE7",
        failures,
    )

    check(
        "Context authority = Stage 8",
        contract.get(
            "principles",
            {}
        ).get(
            "context_layer_authority"
        )
        == "STAGE8",
        failures,
    )

    check(
        "Context cannot change prediction",
        contract.get(
            "principles",
            {}
        ).get(
            "context_can_change_prediction"
        )
        is False,
        failures,
    )

    # ========================================================
    # 4. Prior substages
    # ========================================================

    print(
        "\n4. PREVIOUS STAGE 9.1 SUB-STAGES"
    )

    contract_sub_stages = (
        contract.get(
            "sub_stages",
            {}
        )
    )

    verification_sub_stages = (
        verification.get(
            "sub_stages",
            {}
        )
    )

    for substage in (

        "9.1.1",
        "9.1.2",
        "9.1.3",
        "9.1.4",
    ):

        check(
            f"Contract {substage} PASS",
            contract_sub_stages.get(
                substage
            )
            == "PASS",
            failures,
        )

        check(
            f"Verification {substage} PASS",
            verification_sub_stages.get(
                substage
            )
            == "PASS",
            failures,
        )

    if not already_complete:

        check(
            "9.1.5 still PENDING before promotion",
            contract_sub_stages.get(
                "9.1.5"
            )
            == "PENDING",
            failures,
        )

    # ========================================================
    # 5. Verification evidence
    # ========================================================

    print(
        "\n5. EXISTING VERIFICATION EVIDENCE"
    )

    check(
        "Allowed inputs VERIFIED",
        verification.get(
            "allowed_inputs"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Forbidden operations VERIFIED",
        verification.get(
            "forbidden_operations"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Canonical intelligence schema VERIFIED",
        verification.get(
            "canonical_intelligence_schema"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Freshness & provenance contract VERIFIED",
        verification.get(
            "freshness_and_provenance_contract"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 6. Allowed input set / freshness
    # ========================================================

    print(
        "\n6. ALLOWED INPUT INTEGRITY"
    )

    stage_9_1_1 = contract.get(
        "stage_9_1_1",
        {}
    )

    allowed_inputs = (
        stage_9_1_1.get(
            "allowed_inputs",
            {}
        )
    )

    check(
        "Exactly 11 allowed inputs",
        set(
            allowed_inputs.keys()
        )
        ==
        set(
            EXPECTED_ALLOWED_INPUTS.keys()
        ),
        failures,
    )

    for (
        name,
        expected_path,
    ) in EXPECTED_ALLOWED_INPUTS.items():

        item = allowed_inputs.get(
            name,
            {}
        )

        check(
            f"{name} path exact",
            item.get(
                "path"
            )
            ==
            relative_path(
                expected_path
            ),
            failures,
        )

        check(
            f"{name} SHA current",
            item.get(
                "sha256"
            )
            ==
            sha256_file(
                expected_path
            ),
            failures,
        )

        check(
            f"{name} read-only",
            item.get(
                "read_only"
            )
            is True,
            failures,
        )

        check(
            f"{name} Stage 9 write prohibited",
            item.get(
                "stage9_write_allowed"
            )
            is False,
            failures,
        )

    # ========================================================
    # 7. Prediction integrity
    # ========================================================

    print(
        "\n7. PREDICTION INTEGRITY"
    )

    stage_9_1_2 = contract.get(
        "stage_9_1_2",
        {}
    )

    integrity = stage_9_1_2.get(
        "prediction_integrity_contract",
        {}
    )

    integrity_true_flags = [

        "probabilities_must_be_copied_exactly",
        "prediction_label_must_be_copied_exactly",
        "source_confidence_must_be_copied_exactly",
        "probabilities_may_not_be_recomputed",
        "probabilities_may_not_be_rescaled",
        "probabilities_may_not_be_recalibrated",
        "context_may_not_modify_probabilities",
        "context_may_not_modify_prediction_label",
        "derived_confidence_bands_must_not_replace_source_confidence",
        "stage9_is_not_a_prediction_model",
    ]

    for flag in integrity_true_flags:

        check(
            f"{flag} = true",
            integrity.get(
                flag
            )
            is True,
            failures,
        )

    # ========================================================
    # 8. Forbidden operations
    # ========================================================

    print(
        "\n8. FORBIDDEN OPERATION BOUNDARY"
    )

    forbidden = stage_9_1_2.get(
        "forbidden_operations",
        {}
    )

    critical_forbidden = [

        "model_loading",
        "model_execution",
        "model_retraining",
        "model_reselection",
        "hyperparameter_tuning",

        "feature_schema_mutation",

        "probability_recalibration",
        "probability_modification",
        "prediction_label_modification",
        "source_confidence_modification",
        "hidden_prediction_adjustment",

        "context_as_model_feature",
        "standings_as_model_feature",
        "form_as_model_feature",
        "fixture_context_as_model_feature",

        "production_prediction_artifact_write",
        "stage7_artifact_write",
        "stage8_artifact_write",

        "provider_fetch",

        "future_result_use",
        "future_fixture_state_propagation",

        "final_test_access",
        "final_test_reuse",

        "bookmaker_odds_use",

        "outcome_based_threshold_tuning",
        "post_match_information_use",

        "fuzzy_fixture_identity_join",
        "best_effort_identity_fallback",
    ]

    for operation in critical_forbidden:

        check(
            f"{operation} FORBIDDEN",
            forbidden.get(
                operation
            )
            is True,
            failures,
        )

    # ========================================================
    # 9. Canonical schema
    # ========================================================

    print(
        "\n9. CANONICAL INTELLIGENCE SCHEMA"
    )

    stage_9_1_3 = contract.get(
        "stage_9_1_3",
        {}
    )

    schema = stage_9_1_3.get(
        "canonical_schema",
        {}
    )

    check(
        "9.1.3 schema status PASS",
        stage_9_1_3.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Schema version = 1.0.0",
        schema.get(
            "schema_version"
        )
        == "1.0.0",
        failures,
    )

    check(
        "Fixture primary key = fixture_id",
        schema.get(
            "fixture_primary_key"
        )
        == "fixture_id",
        failures,
    )

    strict_join = schema.get(
        "strict_join",
        {}
    )

    strict_true_flags = [

        "fixture_id_exact_match_required",
        "home_team_id_exact_match_required",
        "home_team_name_exact_match_required",
        "away_team_id_exact_match_required",
        "away_team_name_exact_match_required",
    ]

    for flag in strict_true_flags:

        check(
            f"{flag} = true",
            strict_join.get(
                flag
            )
            is True,
            failures,
        )

    strict_false_flags = [

        "fuzzy_matching_allowed",
        "best_effort_fallback_allowed",
        "unmatched_prediction_allowed",
        "unmatched_context_allowed",
        "duplicate_fixture_id_allowed",
    ]

    for flag in strict_false_flags:

        check(
            f"{flag} = false",
            strict_join.get(
                flag
            )
            is False,
            failures,
        )

    prediction_schema = schema.get(
        "source_prediction_fields",
        {}
    )

    check(
        "Prediction source = production_predictions",
        prediction_schema.get(
            "source"
        )
        == "production_predictions",
        failures,
    )

    check(
        "Prediction values preserved exactly",
        prediction_schema.get(
            "preserve_values_exactly"
        )
        is True,
        failures,
    )

    context_schema = schema.get(
        "source_context_fields",
        {}
    )

    check(
        "Context source = enriched_upcoming_fixtures",
        context_schema.get(
            "source"
        )
        == "enriched_upcoming_fixtures",
        failures,
    )

    check(
        "Context fields preserved exactly",
        context_schema.get(
            "preserve_exactly"
        )
        is True,
        failures,
    )

    # ========================================================
    # 10. Output contract
    # ========================================================

    print(
        "\n10. OUTPUT ARTIFACT CONTRACT"
    )

    output_contract = stage_9_1_3.get(
        "output_artifact_contract",
        {}
    )

    outputs = output_contract.get(
        "outputs",
        {}
    )

    check(
        "Declared output set exact",
        set(
            outputs.keys()
        )
        ==
        set(
            EXPECTED_OUTPUTS.keys()
        ),
        failures,
    )

    for name, expected_path in EXPECTED_OUTPUTS.items():

        check(
            f"{name} path exact",
            outputs.get(
                name,
                {}
            ).get(
                "path"
            )
            ==
            expected_path,
            failures,
        )

    check(
        "Undeclared outputs prohibited",
        output_contract.get(
            "undeclared_output_allowed"
        )
        is False,
        failures,
    )

    check(
        "Stage 7 output writes prohibited",
        output_contract.get(
            "stage7_output_write_allowed"
        )
        is False,
        failures,
    )

    check(
        "Stage 8 output writes prohibited",
        output_contract.get(
            "stage8_output_write_allowed"
        )
        is False,
        failures,
    )

    check(
        "Production prediction writes prohibited",
        output_contract.get(
            "production_prediction_write_allowed"
        )
        is False,
        failures,
    )

    check(
        "Context writes prohibited",
        output_contract.get(
            "context_artifact_write_allowed"
        )
        is False,
        failures,
    )

    # ========================================================
    # 11. Freshness contract
    # ========================================================

    print(
        "\n11. FRESHNESS CONTRACT"
    )

    stage_9_1_4 = contract.get(
        "stage_9_1_4",
        {}
    )

    freshness = stage_9_1_4.get(
        "freshness_contract",
        {}
    )

    check(
        "9.1.4 status PASS",
        stage_9_1_4.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Freshness mode exact",
        freshness.get(
            "mode"
        )
        ==
        "DUAL_UPSTREAM_DEPENDENCY_PLUS_TEMPORAL_BOUNDARY",
        failures,
    )

    freshness_true_flags = [

        "any_allowed_input_hash_change_invalidates_intelligence",
        "prediction_artifact_change_invalidates_intelligence",
        "prediction_metadata_change_invalidates_intelligence",
        "prediction_report_change_invalidates_intelligence",
        "prediction_verification_change_invalidates_intelligence",
        "stage7_final_gate_change_invalidates_intelligence",

        "fixture_context_change_invalidates_intelligence",
        "fixture_context_report_change_invalidates_intelligence",
        "context_api_verification_change_invalidates_intelligence",
        "context_runtime_verification_change_invalidates_intelligence",
        "stage8_final_gate_change_invalidates_intelligence",

        "prediction_context_fixture_set_mismatch_invalidates_intelligence",
        "identity_mismatch_invalidates_intelligence",
        "duplicate_fixture_identity_invalidates_intelligence",

        "upstream_stage7_verification_required",
        "upstream_stage8_verification_required",

        "inherit_stage8_temporal_boundary",
        "fixture_kickoff_reached_invalidates_intelligence",

        "rebuild_required_after_dependency_change",
        "runtime_revalidation_required",
        "fail_closed",
    ]

    for flag in freshness_true_flags:

        check(
            f"{flag} = true",
            freshness.get(
                flag
            )
            is True,
            failures,
        )

    freshness_false_flags = [

        "future_fixture_state_propagation_allowed",
        "stale_fallback_allowed",
        "partial_unverified_output_allowed",
        "automatic_best_effort_reconciliation_allowed",
    ]

    for flag in freshness_false_flags:

        check(
            f"{flag} = false",
            freshness.get(
                flag
            )
            is False,
            failures,
        )

    # ========================================================
    # 12. Provenance contract
    # ========================================================

    print(
        "\n12. PROVENANCE CONTRACT"
    )

    provenance = stage_9_1_4.get(
        "provenance_contract",
        {}
    )

    check(
        "Provenance uses SHA256",
        provenance.get(
            "content_hash_algorithm"
        )
        == "SHA256",
        failures,
    )

    provenance_true_flags = [

        "dependency_hash_required",
        "all_direct_dependency_hashes_required",
        "source_paths_required",
        "generated_at_utc_required",
        "timezone_aware_timestamps_required",
        "prediction_source_identity_required",
        "context_source_identity_required",
        "stage7_verification_identity_required",
        "stage8_verification_identity_required",
        "fixture_identity_validation_required",
        "fixture_count_reconciliation_required",
        "prediction_value_equality_evidence_required",
        "prediction_label_equality_evidence_required",
        "source_confidence_equality_evidence_required",
        "context_value_preservation_evidence_required",
    ]

    for flag in provenance_true_flags:

        check(
            f"{flag} = true",
            provenance.get(
                flag
            )
            is True,
            failures,
        )

    provenance_false_flags = [

        "filesystem_mtime_as_provenance_allowed",
        "fabricated_source_timestamp_allowed",
        "provider_timestamp_fabrication_allowed",
        "unverifiable_provenance_allowed",
    ]

    for flag in provenance_false_flags:

        check(
            f"{flag} = false",
            provenance.get(
                flag
            )
            is False,
            failures,
        )

    # ========================================================
    # 13. Runtime readiness contract
    # ========================================================

    print(
        "\n13. RUNTIME READINESS CONTRACT"
    )

    runtime = stage_9_1_4.get(
        "runtime_readiness_contract",
        {}
    )

    check(
        "READY state exact",
        runtime.get(
            "ready_state"
        )
        == "READY",
        failures,
    )

    check(
        "NOT_READY state exact",
        runtime.get(
            "not_ready_state"
        )
        == "NOT_READY",
        failures,
    )

    check(
        "Healthy HTTP = 200",
        runtime.get(
            "healthy_http_status"
        )
        == 200,
        failures,
    )

    check(
        "Stale HTTP = 503",
        runtime.get(
            "stale_http_status"
        )
        == 503,
        failures,
    )

    check(
        "Unknown resource HTTP = 404",
        runtime.get(
            "unknown_resource_http_status"
        )
        == 404,
        failures,
    )

    check(
        "Write method HTTP = 405",
        runtime.get(
            "write_method_http_status"
        )
        == 405,
        failures,
    )

    runtime_true_flags = [

        "stage7_prediction_source_must_be_current",
        "stage8_context_source_must_be_current",
        "stage8_temporal_boundary_must_be_valid",
        "dependency_hashes_rechecked_at_runtime",
        "upstream_readiness_rechecked_at_runtime",
        "runtime_recovery_without_restart_required",
        "http_no_store_required",
        "fail_closed",
    ]

    for flag in runtime_true_flags:

        check(
            f"{flag} = true",
            runtime.get(
                flag
            )
            is True,
            failures,
        )

    check(
        "Stale intelligence serving prohibited",
        runtime.get(
            "stale_intelligence_may_be_served"
        )
        is False,
        failures,
    )

    # ========================================================
    # 14. Contract safety
    # ========================================================

    print(
        "\n14. SAFETY BOUNDARY"
    )

    safety = contract.get(
        "safety",
        {}
    )

    check(
        "Interpretation-only",
        safety.get(
            "interpretation_only"
        )
        is True,
        failures,
    )

    check(
        "Upstream read-only",
        safety.get(
            "read_only_upstream"
        )
        is True,
        failures,
    )

    false_safety_flags = [

        "stage7_artifacts_modified",
        "stage8_artifacts_modified",
        "provider_fetch_performed",
        "model_loaded",
        "model_executed",
        "model_modified",
        "model_retrained",
        "model_reselected",
        "hyperparameter_tuned",
        "probabilities_modified",
        "probabilities_recalibrated",
        "prediction_labels_modified",
        "feature_schema_modified",
        "context_used_as_model_features",
        "bookmaker_odds_used",
        "future_results_used",
        "final_test_accessed",
    ]

    for flag in false_safety_flags:

        check(
            f"{flag} = false",
            safety.get(
                flag
            )
            is False,
            failures,
        )

    # ========================================================
    # 15. Pre-promotion decision
    # ========================================================

    print(
        "\n15. STAGE 9.1.5 PRE-PROMOTION DECISION"
    )

    pre_promotion_pass = (
        len(
            failures
        )
        == 0
    )

    # ========================================================
    # 16. Promote contract
    # ========================================================

    if (
        pre_promotion_pass
        and
        not already_complete
    ):

        print(
            "\n16. PROMOTE MATCH INTELLIGENCE CONTRACT"
        )

        locked_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        final_contract = dict(
            contract
        )

        final_contract[
            "contract_version"
        ] = "1.2.0"

        final_contract[
            "status"
        ] = (
            "LOCKED_MATCH_INTELLIGENCE_CONTRACT"
        )

        final_contract[
            "stage_9_1_complete"
        ] = True

        final_contract[
            "stage_9_1_status"
        ] = "COMPLETE"

        final_contract[
            "locked_at_utc"
        ] = locked_at

        final_sub_stages = dict(
            final_contract.get(
                "sub_stages",
                {}
            )
        )

        final_sub_stages[
            "9.1.1"
        ] = "PASS"

        final_sub_stages[
            "9.1.2"
        ] = "PASS"

        final_sub_stages[
            "9.1.3"
        ] = "PASS"

        final_sub_stages[
            "9.1.4"
        ] = "PASS"

        final_sub_stages[
            "9.1.5"
        ] = "PASS"

        final_contract[
            "sub_stages"
        ] = final_sub_stages

        final_contract[
            "pending_contract_sections"
        ] = {}

        final_contract[
            "final_gate"
        ] = {

            "stage":
                "9.1.5",

            "status":
                "PASS",

            "locked_at_utc":
                locked_at,

            "allowed_inputs_verified":
                True,

            "forbidden_operations_verified":
                True,

            "canonical_schema_verified":
                True,

            "strict_fixture_identity_verified":
                True,

            "prediction_integrity_verified":
                True,

            "freshness_contract_verified":
                True,

            "provenance_contract_verified":
                True,

            "runtime_readiness_contract_verified":
                True,

            "output_contract_verified":
                True,

            "stage7_write_protection_verified":
                True,

            "stage8_write_protection_verified":
                True,

            "probability_mutation_prohibited":
                True,

            "context_as_model_feature_prohibited":
                True,

            "final_test_access_prohibited":
                True,

            "bookmaker_odds_prohibited":
                True,

            "fail_closed":
                True,

            "match_intelligence_contract_locked":
                True,
        }

        save_json_atomic(
            CONTRACT_FILE,
            final_contract,
        )

        final_contract_sha = (
            sha256_file(
                CONTRACT_FILE
            )
        )

        final_verification = dict(
            verification
        )

        final_verification[
            "status"
        ] = "PASS"

        final_verification[
            "stage_9_1_complete"
        ] = True

        final_verification[
            "stage_9_1_status"
        ] = "COMPLETE"

        final_verification[
            "match_intelligence_contract"
        ] = "VERIFIED"

        final_verification[
            "contract_status"
        ] = (
            "LOCKED_MATCH_INTELLIGENCE_CONTRACT"
        )

        final_verification[
            "contract_version"
        ] = "1.2.0"

        final_verification[
            "contract_sha256"
        ] = final_contract_sha

        final_verification[
            "verified_at_utc"
        ] = locked_at

        final_verification_sub_stages = dict(
            final_verification.get(
                "sub_stages",
                {}
            )
        )

        final_verification_sub_stages[
            "9.1.1"
        ] = "PASS"

        final_verification_sub_stages[
            "9.1.2"
        ] = "PASS"

        final_verification_sub_stages[
            "9.1.3"
        ] = "PASS"

        final_verification_sub_stages[
            "9.1.4"
        ] = "PASS"

        final_verification_sub_stages[
            "9.1.5"
        ] = "PASS"

        final_verification[
            "sub_stages"
        ] = (
            final_verification_sub_stages
        )

        final_verification[
            "final_gate"
        ] = {

            "stage":
                "9.1.5",

            "status":
                "PASS",

            "verified_at_utc":
                locked_at,

            "all_stage_9_1_substages_pass":
                True,

            "allowed_input_hashes_current":
                True,

            "upstream_stage7_verified":
                True,

            "upstream_stage8_verified":
                True,

            "prediction_authority_locked":
                True,

            "context_authority_locked":
                True,

            "prediction_integrity_locked":
                True,

            "strict_identity_join_locked":
                True,

            "canonical_schema_locked":
                True,

            "output_contract_locked":
                True,

            "freshness_contract_locked":
                True,

            "provenance_contract_locked":
                True,

            "runtime_contract_locked":
                True,

            "fail_closed":
                True,

            "stage9_ready_for_9_2":
                True,
        }

        final_verification[
            "safety"
        ] = {

            "read_only_upstream":
                True,

            "interpretation_only":
                True,

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

            "source_confidence_modified":
                False,

            "feature_schema_modified":
                False,

            "context_used_as_model_features":
                False,

            "stage7_artifacts_modified":
                False,

            "stage8_artifacts_modified":
                False,

            "bookmaker_odds_used":
                False,

            "future_results_used":
                False,

            "final_test_accessed":
                False,
        }

        final_verification[
            "failures"
        ] = []

        save_json_atomic(
            VERIFICATION_FILE,
            final_verification,
        )

        print(
            CONTRACT_FILE
        )

        print(
            VERIFICATION_FILE
        )

    # ========================================================
    # 17. Persisted final-state verification
    # ========================================================

    print(
        "\n17. PERSISTED FINAL STATE"
    )

    persisted_contract = load_json(
        CONTRACT_FILE
    )

    persisted_verification = load_json(
        VERIFICATION_FILE
    )

    check(
        "Contract status LOCKED",
        persisted_contract.get(
            "status"
        )
        ==
        "LOCKED_MATCH_INTELLIGENCE_CONTRACT",
        failures,
    )

    check(
        "Contract version = 1.2.0",
        persisted_contract.get(
            "contract_version"
        )
        == "1.2.0",
        failures,
    )

    check(
        "Stage 9.1 COMPLETE persisted",
        persisted_contract.get(
            "stage_9_1_complete"
        )
        is True
        and
        persisted_contract.get(
            "stage_9_1_status"
        )
        == "COMPLETE",
        failures,
    )

    for substage in (

        "9.1.1",
        "9.1.2",
        "9.1.3",
        "9.1.4",
        "9.1.5",
    ):

        check(
            f"{substage} PASS persisted in contract",
            persisted_contract.get(
                "sub_stages",
                {}
            ).get(
                substage
            )
            == "PASS",
            failures,
        )

        check(
            f"{substage} PASS persisted in verification",
            persisted_verification.get(
                "sub_stages",
                {}
            ).get(
                substage
            )
            == "PASS",
            failures,
        )

    check(
        "No pending contract sections",
        persisted_contract.get(
            "pending_contract_sections"
        )
        == {},
        failures,
    )

    check(
        "Contract final gate PASS",
        persisted_contract.get(
            "final_gate",
            {}
        ).get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Verification status PASS",
        persisted_verification.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Verification Stage 9.1 COMPLETE",
        (
            persisted_verification.get(
                "stage_9_1_complete"
            )
            is True
            and
            persisted_verification.get(
                "stage_9_1_status"
            )
            == "COMPLETE"
        ),
        failures,
    )

    check(
        "Match Intelligence Contract VERIFIED",
        persisted_verification.get(
            "match_intelligence_contract"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Verification final gate PASS",
        persisted_verification.get(
            "final_gate",
            {}
        ).get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 9 ready for 9.2",
        persisted_verification.get(
            "final_gate",
            {}
        ).get(
            "stage9_ready_for_9_2"
        )
        is True,
        failures,
    )

    check(
        "Verification references current final contract SHA",
        persisted_verification.get(
            "contract_sha256"
        )
        ==
        sha256_file(
            CONTRACT_FILE
        ),
        failures,
    )

    # ========================================================
    # 18. Upstream write protection
    # ========================================================

    print(
        "\n18. UPSTREAM WRITE PROTECTION"
    )

    for name, path in EXPECTED_ALLOWED_INPUTS.items():

        check(
            f"{name} unchanged during final gate",
            sha256_file(
                path
            )
            ==
            upstream_before[
                name
            ],
            failures,
        )

    # ========================================================
    # Final decision
    # ========================================================

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 9.1.1: PASS"
        )

        print(
            "STAGE 9.1.2: PASS"
        )

        print(
            "STAGE 9.1.3: PASS"
        )

        print(
            "STAGE 9.1.4: PASS"
        )

        print(
            "STAGE 9.1.5: PASS"
        )

        print()

        print(
            "STAGE 9.1: COMPLETE"
        )

        print(
            "MATCH INTELLIGENCE CONTRACT: LOCKED"
        )

        print(
            "STAGE 9 READY FOR 9.2"
        )

    else:

        print(
            "STAGE 9.1.5: FAIL"
        )

        print(
            "STAGE 9.1: INCOMPLETE"
        )

        print(
            "MATCH INTELLIGENCE CONTRACT: NOT LOCKED"
        )

        if failures:

            print(
                "\nFailures:"
            )

            for failure in failures:

                print(
                    f"  - {failure}"
                )

    print("=" * 72)

    sys.exit(
        0
        if overall_pass
        else 1
    )


if __name__ == "__main__":

    main()