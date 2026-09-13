"""
FixtureIQ Stage 9.1.3 + 9.1.4
Independent Schema / Freshness Contract Verification.

Verifies:
- 9.1.1 and 9.1.2 remain locked
- source artifacts remain current
- canonical base schema is exact
- final intelligence schema is exact
- prediction values remain explicitly copied
- strict fixture identity join is locked
- Stage 9 output paths are isolated
- dual-upstream freshness is locked
- temporal invalidation is inherited from Stage 8
- SHA256 provenance is mandatory
- stale fallback is forbidden
- runtime fail-closed behavior is contracted

Updates:
stage9_intelligence_contract_verification.json

9.1.5 remains PENDING.
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
# Directories / paths
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


PRODUCTION_PREDICTIONS_FILE = (
    PRODUCTION_DIR
    / "production_predictions.csv"
)

ENRICHED_FIXTURES_FILE = (
    CONTEXT_DIR
    / "enriched_upcoming_fixtures.csv"
)

STAGE8_FINAL_FILE = (
    CONTEXT_DIR
    / "stage8_final_verification.json"
)

CONTRACT_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract.json"
)

VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract_verification.json"
)


# ============================================================
# Expected Stage 9 schema
# ============================================================

SOURCE_PREDICTION_FIELDS = [

    "prob_home_win",
    "prob_draw",
    "prob_away_win",
    "predicted_label",
    "confidence",
]


PREDICTION_COPY_FIELDS = [

    "stage7_prob_home_win",
    "stage7_prob_draw",
    "stage7_prob_away_win",
    "stage7_predicted_label",
    "stage7_confidence",
]


EXPECTED_MAPPING = {

    "prob_home_win":
        "stage7_prob_home_win",

    "prob_draw":
        "stage7_prob_draw",

    "prob_away_win":
        "stage7_prob_away_win",

    "predicted_label":
        "stage7_predicted_label",

    "confidence":
        "stage7_confidence",
}


DERIVED_FIELDS = [

    "stage9_top_probability",
    "stage9_second_probability",
    "stage9_probability_margin",

    "stage9_entropy",
    "stage9_normalized_entropy",

    "stage9_confidence_band",
    "stage9_uncertainty_band",

    "stage9_league_position_gap",
    "stage9_points_gap",
    "stage9_goal_difference_gap",

    "stage9_recent_points_gap",
    "stage9_recent_goal_difference_gap",

    "stage9_venue_form_points_gap",

    "stage9_context_support_score",
    "stage9_context_alignment",

    "stage9_explanation_headline",
    "stage9_explanation_summary",
]


EXPECTED_OUTPUTS = {

    "stage9_intelligence_contract":
        "data/processed/intelligence/stage9_intelligence_contract.json",

    "stage9_intelligence_contract_verification":
        (
            "data/processed/intelligence/"
            "stage9_intelligence_contract_verification.json"
        ),

    "match_intelligence_base":
        "data/processed/intelligence/match_intelligence_base.csv",

    "match_intelligence_base_report":
        (
            "data/processed/intelligence/"
            "match_intelligence_base_report.json"
        ),

    "match_intelligence":
        "data/processed/intelligence/match_intelligence.csv",

    "match_intelligence_report":
        "data/processed/intelligence/match_intelligence_report.json",

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

        payload = json.load(file)

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


def csv_fields(
    path: Path,
) -> list[str]:

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        return list(
            reader.fieldnames
            or []
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
        "FixtureIQ Stage 9.1.3 + 9.1.4"
    )

    print(
        "Independent Schema & Freshness Verification"
    )

    print("=" * 72)

    failures = []

    # ========================================================
    # 1. Required files
    # ========================================================

    print(
        "\n1. REQUIRED FILES"
    )

    required = [

        CONTRACT_FILE,
        VERIFICATION_FILE,
        PRODUCTION_PREDICTIONS_FILE,
        ENRICHED_FIXTURES_FILE,
        STAGE8_FINAL_FILE,
    ]

    for path in required:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        sys.exit(1)

    contract = load_json(
        CONTRACT_FILE
    )

    verification = load_json(
        VERIFICATION_FILE
    )

    stage8_final = load_json(
        STAGE8_FINAL_FILE
    )

    # ========================================================
    # 2. Previous contract state
    # ========================================================

    print(
        "\n2. PREVIOUS CONTRACT PROTECTION"
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
        "Contract type unchanged",
        contract.get(
            "contract_type"
        )
        == "MATCH_INTELLIGENCE_CONTRACT",
        failures,
    )

    check(
        "Contract version = 1.1.0-partial",
        contract.get(
            "contract_version"
        )
        == "1.1.0-partial",
        failures,
    )

    check(
        "Stage 9.1 remains incomplete",
        contract.get(
            "stage_9_1_complete"
        )
        is False,
        failures,
    )

    sub_stages = contract.get(
        "sub_stages",
        {}
    )

    check(
        "9.1.1 remains PASS",
        sub_stages.get(
            "9.1.1"
        )
        == "PASS",
        failures,
    )

    check(
        "9.1.2 remains PASS",
        sub_stages.get(
            "9.1.2"
        )
        == "PASS",
        failures,
    )

    check(
        "9.1.3 PASS",
        sub_stages.get(
            "9.1.3"
        )
        == "PASS",
        failures,
    )

    check(
        "9.1.4 PASS",
        sub_stages.get(
            "9.1.4"
        )
        == "PASS",
        failures,
    )

    check(
        "9.1.5 remains PENDING",
        sub_stages.get(
            "9.1.5"
        )
        == "PENDING",
        failures,
    )

    check(
        "Original 9.1.1 verification remains PASS",
        verification.get(
            "sub_stages",
            {}
        ).get(
            "9.1.1"
        )
        == "PASS",
        failures,
    )

    check(
        "Original 9.1.2 verification remains PASS",
        verification.get(
            "sub_stages",
            {}
        ).get(
            "9.1.2"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 8 final gate remains PASS",
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
        ),
        failures,
    )

    # ========================================================
    # 3. Allowed input freshness
    # ========================================================

    print(
        "\n3. ALLOWED INPUT FRESHNESS"
    )

    allowed_inputs = (
        contract.get(
            "stage_9_1_1",
            {}
        ).get(
            "allowed_inputs",
            {}
        )
    )

    all_hashes_current = True

    for name, item in allowed_inputs.items():

        source_path = (
            BASE_DIR
            / item.get(
                "path",
                ""
            )
        )

        current = (
            source_path.exists()
            and
            item.get(
                "sha256"
            )
            ==
            sha256_file(
                source_path
            )
        )

        check(
            f"{name} hash current",
            current,
            failures,
        )

        if not current:

            all_hashes_current = False

    # ========================================================
    # 4. Canonical source schemas
    # ========================================================

    print(
        "\n4. CANONICAL SOURCE SCHEMAS"
    )

    prediction_fields = csv_fields(
        PRODUCTION_PREDICTIONS_FILE
    )

    context_fields = csv_fields(
        ENRICHED_FIXTURES_FILE
    )

    for field in SOURCE_PREDICTION_FIELDS:

        check(
            f"Prediction field {field} exists",
            field
            in prediction_fields,
            failures,
        )

    # ========================================================
    # 5. Stage 9.1.3 schema
    # ========================================================

    print(
        "\n5. STAGE 9.1.3 CANONICAL SCHEMA"
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
        "9.1.3 status PASS",
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
        "fixture_id primary key",
        schema.get(
            "fixture_primary_key"
        )
        == "fixture_id",
        failures,
    )

    check(
        "Fixture primary key unique required",
        schema.get(
            "fixture_primary_key_unique_required"
        )
        is True,
        failures,
    )

    strict_join = schema.get(
        "strict_join",
        {}
    )

    check(
        "Strict join uses fixture_id",
        strict_join.get(
            "primary_join_field"
        )
        == "fixture_id",
        failures,
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

    source_context = schema.get(
        "source_context_fields",
        {}
    )

    check(
        "Context source fields exact",
        source_context.get(
            "fields"
        )
        ==
        context_fields,
        failures,
    )

    check(
        "Context source column count exact",
        source_context.get(
            "count"
        )
        ==
        len(
            context_fields
        ),
        failures,
    )

    source_prediction = schema.get(
        "source_prediction_fields",
        {}
    )

    check(
        "Prediction source fields exact",
        source_prediction.get(
            "fields"
        )
        ==
        SOURCE_PREDICTION_FIELDS,
        failures,
    )

    check(
        "Prediction copy mapping exact",
        source_prediction.get(
            "copy_mapping"
        )
        ==
        EXPECTED_MAPPING,
        failures,
    )

    check(
        "Prediction copy fields exact",
        source_prediction.get(
            "copied_output_fields"
        )
        ==
        PREDICTION_COPY_FIELDS,
        failures,
    )

    expected_base_fields = (
        context_fields
        +
        PREDICTION_COPY_FIELDS
    )

    expected_final_fields = (
        expected_base_fields
        +
        DERIVED_FIELDS
    )

    base_schema = schema.get(
        "base_intelligence_schema",
        {}
    )

    final_schema = schema.get(
        "final_intelligence_schema",
        {}
    )

    check(
        "Base schema exact",
        base_schema.get(
            "fields"
        )
        ==
        expected_base_fields,
        failures,
    )

    check(
        "Base schema column count exact",
        base_schema.get(
            "column_count"
        )
        ==
        len(
            expected_base_fields
        ),
        failures,
    )

    check(
        "Derived field set exact",
        schema.get(
            "derived_intelligence_fields",
            {}
        ).get(
            "fields"
        )
        ==
        DERIVED_FIELDS,
        failures,
    )

    check(
        "Final schema exact",
        final_schema.get(
            "fields"
        )
        ==
        expected_final_fields,
        failures,
    )

    check(
        "Final schema column count exact",
        final_schema.get(
            "column_count"
        )
        ==
        len(
            expected_final_fields
        ),
        failures,
    )

    # ========================================================
    # 6. Semantic protections
    # ========================================================

    print(
        "\n6. SCHEMA SEMANTICS"
    )

    semantics = schema.get(
        "semantics",
        {}
    )

    prediction_semantics = semantics.get(
        "stage7_prediction_fields",
        {}
    )

    check(
        "Prediction copy mode exact",
        prediction_semantics.get(
            "copy_mode"
        )
        == "EXACT_VALUE_COPY",
        failures,
    )

    check(
        "Probability mutation prohibited",
        prediction_semantics.get(
            "probability_mutation_allowed"
        )
        is False,
        failures,
    )

    check(
        "Label mutation prohibited",
        prediction_semantics.get(
            "prediction_label_mutation_allowed"
        )
        is False,
        failures,
    )

    check(
        "Source confidence mutation prohibited",
        prediction_semantics.get(
            "source_confidence_mutation_allowed"
        )
        is False,
        failures,
    )

    bands = semantics.get(
        "bands",
        {}
    )

    check(
        "Outcome-based threshold tuning prohibited",
        bands.get(
            "outcome_based_threshold_tuning_allowed"
        )
        is False,
        failures,
    )

    alignment = semantics.get(
        "context_alignment",
        {}
    )

    check(
        "Context support score min = -5",
        alignment.get(
            "support_score_min"
        )
        == -5,
        failures,
    )

    check(
        "Context support score max = 5",
        alignment.get(
            "support_score_max"
        )
        == 5,
        failures,
    )

    check(
        "Outcome-based context rule tuning prohibited",
        alignment.get(
            "outcome_based_rule_tuning_allowed"
        )
        is False,
        failures,
    )

    explanation = semantics.get(
        "explanation",
        {}
    )

    check(
        "Explanation deterministic",
        explanation.get(
            "deterministic"
        )
        is True,
        failures,
    )

    check(
        "Explanation cannot change prediction",
        explanation.get(
            "may_change_prediction"
        )
        is False,
        failures,
    )

    check(
        "Guaranteed-outcome claims prohibited",
        explanation.get(
            "may_claim_guaranteed_outcome"
        )
        is False,
        failures,
    )

    # ========================================================
    # 7. Output contract
    # ========================================================

    print(
        "\n7. STAGE 9 OUTPUT CONTRACT"
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
        "Output set exact",
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
            f"{name} path locked",
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
        "Undeclared output prohibited",
        output_contract.get(
            "undeclared_output_allowed"
        )
        is False,
        failures,
    )

    check(
        "Stage 7 writes prohibited",
        output_contract.get(
            "stage7_output_write_allowed"
        )
        is False,
        failures,
    )

    check(
        "Stage 8 writes prohibited",
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

    # ========================================================
    # 8. Stage 9.1.4 freshness contract
    # ========================================================

    print(
        "\n8. STAGE 9.1.4 FRESHNESS CONTRACT"
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

    required_true_freshness = [

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

    for flag in required_true_freshness:

        check(
            f"{flag} = true",
            freshness.get(
                flag
            )
            is True,
            failures,
        )

    required_false_freshness = [

        "future_fixture_state_propagation_allowed",
        "stale_fallback_allowed",
        "partial_unverified_output_allowed",
        "automatic_best_effort_reconciliation_allowed",
    ]

    for flag in required_false_freshness:

        check(
            f"{flag} = false",
            freshness.get(
                flag
            )
            is False,
            failures,
        )

    # ========================================================
    # 9. Provenance
    # ========================================================

    print(
        "\n9. PROVENANCE CONTRACT"
    )

    provenance = stage_9_1_4.get(
        "provenance_contract",
        {}
    )

    check(
        "SHA256 provenance",
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
    # 10. Runtime readiness
    # ========================================================

    print(
        "\n10. RUNTIME READINESS CONTRACT"
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
        "Stale intelligence may not be served",
        runtime.get(
            "stale_intelligence_may_be_served"
        )
        is False,
        failures,
    )

    # ========================================================
    # 11. Update verification artifact
    # ========================================================

    print(
        "\n11. SAVE 9.1.3 + 9.1.4 VERIFICATION"
    )

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    if overall_pass:

        verified_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        updated_verification = dict(
            verification
        )

        sub = dict(
            updated_verification.get(
                "sub_stages",
                {}
            )
        )

        sub[
            "9.1.1"
        ] = "PASS"

        sub[
            "9.1.2"
        ] = "PASS"

        sub[
            "9.1.3"
        ] = "PASS"

        sub[
            "9.1.4"
        ] = "PASS"

        sub[
            "9.1.5"
        ] = "PENDING"

        updated_verification[
            "sub_stages"
        ] = sub

        updated_verification[
            "status"
        ] = "PARTIAL_PASS"

        updated_verification[
            "stage_9_1_complete"
        ] = False

        updated_verification[
            "stage_9_1_status"
        ] = "IN_PROGRESS"

        updated_verification[
            "contract_sha256"
        ] = sha256_file(
            CONTRACT_FILE
        )

        updated_verification[
            "canonical_intelligence_schema"
        ] = "VERIFIED"

        updated_verification[
            "freshness_and_provenance_contract"
        ] = "VERIFIED"

        updated_verification[
            "stage_9_1_3_4_verified_at_utc"
        ] = verified_at

        updated_verification[
            "schema_verification"
        ] = {

            "status":
                "VERIFIED",

            "context_source_columns":
                len(
                    context_fields
                ),

            "prediction_copy_fields":
                len(
                    PREDICTION_COPY_FIELDS
                ),

            "base_columns":
                len(
                    expected_base_fields
                ),

            "derived_fields":
                len(
                    DERIVED_FIELDS
                ),

            "final_columns":
                len(
                    expected_final_fields
                ),

            "strict_identity_join":
                True,

            "prediction_values_exact_copy":
                True,

            "probability_mutation_allowed":
                False,

            "fuzzy_join_allowed":
                False,
        }

        updated_verification[
            "freshness_verification"
        ] = {

            "status":
                "VERIFIED",

            "mode":
                (
                    "DUAL_UPSTREAM_DEPENDENCY_"
                    "PLUS_TEMPORAL_BOUNDARY"
                ),

            "all_current_input_hashes_verified":
                all_hashes_current,

            "stage7_dependency_required":
                True,

            "stage8_dependency_required":
                True,

            "temporal_boundary_required":
                True,

            "stale_fallback_allowed":
                False,

            "partial_unverified_output_allowed":
                False,

            "fail_closed":
                True,
        }

        updated_verification[
            "provenance_verification"
        ] = {

            "status":
                "VERIFIED",

            "hash_algorithm":
                "SHA256",

            "all_dependency_hashes_required":
                True,

            "filesystem_mtime_allowed":
                False,

            "fabricated_timestamp_allowed":
                False,

            "unverifiable_provenance_allowed":
                False,
        }

        updated_verification[
            "failures"
        ] = []

        save_json_atomic(
            VERIFICATION_FILE,
            updated_verification,
        )

        print(
            VERIFICATION_FILE
        )

        persisted = load_json(
            VERIFICATION_FILE
        )

        check(
            "9.1.3 PASS persisted",
            persisted.get(
                "sub_stages",
                {}
            ).get(
                "9.1.3"
            )
            == "PASS",
            failures,
        )

        check(
            "9.1.4 PASS persisted",
            persisted.get(
                "sub_stages",
                {}
            ).get(
                "9.1.4"
            )
            == "PASS",
            failures,
        )

        check(
            "9.1.5 remains PENDING",
            persisted.get(
                "sub_stages",
                {}
            ).get(
                "9.1.5"
            )
            == "PENDING",
            failures,
        )

        check(
            "Schema VERIFIED persisted",
            persisted.get(
                "canonical_intelligence_schema"
            )
            == "VERIFIED",
            failures,
        )

        check(
            "Freshness/Provenance VERIFIED persisted",
            persisted.get(
                "freshness_and_provenance_contract"
            )
            == "VERIFIED",
            failures,
        )

        overall_pass = (
            len(
                failures
            )
            == 0
        )

    # ========================================================
    # Final
    # ========================================================

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
            "CANONICAL INTELLIGENCE SCHEMA: VERIFIED"
        )

        print(
            "STAGE 9.1.4: PASS"
        )

        print(
            "FRESHNESS & PROVENANCE CONTRACT: VERIFIED"
        )

        print(
            "STAGE 9.1: IN PROGRESS"
        )

    else:

        print(
            "STAGE 9.1.3 / 9.1.4: FAIL"
        )

        print(
            "STAGE 9.1: INCOMPLETE"
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