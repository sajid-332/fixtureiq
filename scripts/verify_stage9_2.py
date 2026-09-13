"""
FixtureIQ Stage 9.2.5
Final Prediction + Context Join Gate.

Verifies:

9.2.1 Prediction Source Gate
9.2.2 Fixture Identity Reconciliation
9.2.3 Strict Prediction-Context Join
9.2.4 Independent Join Validation
9.2.5 Final Stage 9.2 Gate

Promotes:

data/processed/intelligence/
    match_intelligence_base_report.json

Does NOT rebuild or modify:
- Stage 7 artifacts
- Stage 8 artifacts
- Stage 9.1 contract
- match_intelligence_base.csv
- model files
- prediction probabilities

Stage 9 remains interpretation-only.
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
# FixtureIQ imports
# ============================================================

from backend.services.fixture_context_service import (
    FixtureContextService,
)

from backend.services.match_intelligence_base_validator import (
    MatchIntelligenceBaseValidator,
)

from backend.services.prediction_context_join_service import (
    PredictionContextJoinService,
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
# Stage 9.1
# ============================================================

CONTRACT_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract.json"
)

CONTRACT_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract_verification.json"
)


# ============================================================
# Stage 9.2
# ============================================================

BASE_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base.csv"
)

REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base_report.json"
)


# ============================================================
# Stage 7
# ============================================================

PREDICTIONS_FILE = (
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

PREDICTION_VERIFICATION_FILE = (
    PRODUCTION_DIR
    / "production_prediction_verification.json"
)

STAGE7_8_FILE = (
    PRODUCTION_DIR
    / "stage7_8_final_verification.json"
)

STAGE7_9_FILE = (
    PRODUCTION_DIR
    / "stage7_9_final_verification.json"
)


# ============================================================
# Stage 8
# ============================================================

CONTEXT_FILE = (
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
# Expected allowed inputs
# ============================================================

EXPECTED_ALLOWED_INPUTS = {

    "production_predictions":
        PREDICTIONS_FILE,

    "production_prediction_metadata":
        PREDICTION_METADATA_FILE,

    "production_prediction_report":
        PREDICTION_REPORT_FILE,

    "production_prediction_verification":
        PREDICTION_VERIFICATION_FILE,

    "stage7_8_final_verification":
        STAGE7_8_FILE,

    "stage7_9_final_verification":
        STAGE7_9_FILE,

    "enriched_upcoming_fixtures":
        CONTEXT_FILE,

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
        "FixtureIQ Stage 9.2.5"
    )

    print(
        "FINAL PREDICTION + CONTEXT JOIN GATE"
    )

    print("=" * 72)

    failures = []

    # ========================================================
    # 1. Required artifacts
    # ========================================================

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    required = [

        CONTRACT_FILE,
        CONTRACT_VERIFICATION_FILE,

        BASE_FILE,
        REPORT_FILE,

        PREDICTIONS_FILE,
        PREDICTION_METADATA_FILE,
        PREDICTION_REPORT_FILE,
        PREDICTION_VERIFICATION_FILE,

        STAGE7_8_FILE,
        STAGE7_9_FILE,

        CONTEXT_FILE,
        FIXTURE_CONTEXT_REPORT_FILE,
        CONTEXT_API_VERIFICATION_FILE,
        CONTEXT_RUNTIME_VERIFICATION_FILE,
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

    # ========================================================
    # Protected identities
    # ========================================================

    protected_before = {

        relative_path(
            path
        ):
            sha256_file(
                path
            )

        for path in required
    }

    # Report is intentionally promoted by this gate,
    # therefore exclude it from immutable checks later.

    protected_before.pop(
        relative_path(
            REPORT_FILE
        )
    )

    base_sha_before = sha256_file(
        BASE_FILE
    )

    # ========================================================
    # Load evidence
    # ========================================================

    contract = load_json(
        CONTRACT_FILE
    )

    contract_verification = load_json(
        CONTRACT_VERIFICATION_FILE
    )

    report = load_json(
        REPORT_FILE
    )

    stage7_8 = load_json(
        STAGE7_8_FILE
    )

    stage7_9 = load_json(
        STAGE7_9_FILE
    )

    stage8_final = load_json(
        STAGE8_FINAL_FILE
    )

    # ========================================================
    # Idempotent completion support
    # ========================================================

    already_complete = (

        report.get(
            "status"
        )
        == "PASS"

        and

        report.get(
            "stage_9_2_complete"
        )
        is True

        and

        report.get(
            "stage_9_2_status"
        )
        == "COMPLETE"

        and

        report.get(
            "sub_stages",
            {}
        ).get(
            "9.2.5"
        )
        == "PASS"

        and

        report.get(
            "prediction_context_join_layer"
        )
        == "VERIFIED"
    )

    if already_complete:

        print(
            "\nStage 9.2 is already complete."
        )

        print(
            "Running integrity verification only."
        )

    # ========================================================
    # 2. Stage 9.1 foundation
    # ========================================================

    print(
        "\n2. LOCKED STAGE 9.1 FOUNDATION"
    )

    check(
        "Stage 9.1 contract LOCKED",
        contract.get(
            "status"
        )
        ==
        "LOCKED_MATCH_INTELLIGENCE_CONTRACT",
        failures,
    )

    check(
        "Stage 9.1 COMPLETE",
        (
            contract.get(
                "stage_9_1_complete"
            )
            is True

            and

            contract.get(
                "stage_9_1_status"
            )
            == "COMPLETE"
        ),
        failures,
    )

    check(
        "Stage 9.1 verification PASS",
        contract_verification.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 9.1 verification COMPLETE",
        contract_verification.get(
            "stage_9_1_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 9.1 contract SHA current",
        contract_verification.get(
            "contract_sha256"
        )
        ==
        sha256_file(
            CONTRACT_FILE
        ),
        failures,
    )

    check(
        "Stage 9 ready for 9.2",
        contract_verification.get(
            "final_gate",
            {}
        ).get(
            "stage9_ready_for_9_2"
        )
        is True,
        failures,
    )

    # ========================================================
    # 3. Stage 7 / Stage 8 gates
    # ========================================================

    print(
        "\n3. UPSTREAM FINAL GATES"
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
    # 4. Current Stage 8 runtime readiness
    # ========================================================

    print(
        "\n4. CURRENT STAGE 8 CONTEXT READINESS"
    )

    fixture_context_service = (
        FixtureContextService()
    )

    fixture_context_status = (
        fixture_context_service
        .get_status()
    )

    if (
        fixture_context_status.get(
            "status"
        )
        != "READY"
    ):

        print(
            "Fixture context reason:",
            fixture_context_status.get(
                "reason"
            ),
        )

    check(
        "Fixture context service READY",
        fixture_context_status.get(
            "status"
        )
        == "READY",
        failures,
    )

    # ========================================================
    # 5. Prior Stage 9.2 substages
    # ========================================================

    print(
        "\n5. STAGE 9.2 SUB-STAGE EVIDENCE"
    )

    report_sub_stages = (
        report.get(
            "sub_stages",
            {}
        )
    )

    for substage in (

        "9.2.1",
        "9.2.2",
        "9.2.3",
        "9.2.4",
    ):

        check(
            f"{substage} PASS",
            report_sub_stages.get(
                substage
            )
            == "PASS",
            failures,
        )

    if not already_complete:

        check(
            "9.2.5 PENDING before promotion",
            report_sub_stages.get(
                "9.2.5"
            )
            == "PENDING",
            failures,
        )

    check(
        "Prediction Source Gate VERIFIED",
        report.get(
            "prediction_source_gate"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Fixture Identity Reconciliation VERIFIED",
        report.get(
            "fixture_identity_reconciliation"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Strict Prediction-Context Join VERIFIED",
        report.get(
            "strict_prediction_context_join"
        )
        == "VERIFIED",
        failures,
    )

    check(
        "Independent Join Validation VERIFIED",
        report.get(
            "independent_join_validation"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 6. Allowed dependency identity
    # ========================================================

    print(
        "\n6. LOCKED DEPENDENCY IDENTITY"
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

    check(
        "Allowed input set exact",
        set(
            allowed_inputs.keys()
        )
        ==
        set(
            EXPECTED_ALLOWED_INPUTS.keys()
        ),
        failures,
    )

    for name, expected_path in (
        EXPECTED_ALLOWED_INPUTS.items()
    ):

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
            f"{name} snapshot hash policy",
            item.get(
                "dependency_hash_policy"
            )
            ==
            "CAPTURE_AT_DOWNSTREAM_BUILD",
            failures,
        )

        check(
            f"{name} permanent runtime hash pin disabled",
            item.get(
                "contract_runtime_hash_pin"
            )
            is False,
            failures,
        )

        check(
            f"{name} downstream snapshot hash required",
            item.get(
                "downstream_snapshot_hash_required"
            )
            is True,
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
    # 7. Re-run Stage 9.2.1
    # ========================================================

    print(
        "\n7. REVERIFY PREDICTION SOURCE GATE"
    )

    join_service = (
        PredictionContextJoinService()
    )

    try:

        source_gate = (
            join_service
            .validate_prediction_source()
        )

        source_gate_ok = (
            source_gate.get(
                "status"
            )
            == "PASS"
        )

    except Exception as exc:

        print(
            "Prediction source gate error:",
            exc,
        )

        source_gate = {}
        source_gate_ok = False

    check(
        "Prediction source gate PASS",
        source_gate_ok,
        failures,
    )

    if source_gate_ok:

        source_flags = [

            "fixture_id_unique",
            "required_schema_present",
            "identity_complete",
            "probabilities_valid",
            "probabilities_sum_to_one",
            "prediction_labels_present",
            "confidence_valid",
            "stage7_8_verified",
            "stage7_9_verified",
            "stage8_final_verified",
            "locked_dependency_hashes_current",
        ]

        for flag in source_flags:

            check(
                f"{flag} = true",
                source_gate.get(
                    flag
                )
                is True,
                failures,
            )

    # ========================================================
    # 8. Re-run Stage 9.2.2
    # ========================================================

    print(
        "\n8. REVERIFY FIXTURE IDENTITY"
    )

    try:

        identity = (
            join_service
            .reconcile_fixture_identity()
        )

        identity_ok = (
            identity.get(
                "status"
            )
            == "PASS"
        )

    except Exception as exc:

        print(
            "Fixture identity error:",
            exc,
        )

        identity = {}
        identity_ok = False

    check(
        "Fixture identity reconciliation PASS",
        identity_ok,
        failures,
    )

    if identity_ok:

        identity_flags = [

            "fixture_sets_exact",
            "fixture_id_unique_prediction",
            "fixture_id_unique_context",
            "fixture_id_exact_match",
            "home_team_id_exact_match",
            "home_team_name_exact_match",
            "away_team_id_exact_match",
            "away_team_name_exact_match",
            "season_exact_match_if_shared",
        ]

        for flag in identity_flags:

            check(
                f"{flag} = true",
                identity.get(
                    flag
                )
                is True,
                failures,
            )

        check(
            "No unmatched predictions",
            identity.get(
                "unmatched_prediction_count"
            )
            == 0,
            failures,
        )

        check(
            "No unmatched context fixtures",
            identity.get(
                "unmatched_context_count"
            )
            == 0,
            failures,
        )

        check(
            "No identity mismatches",
            identity.get(
                "identity_mismatch_count"
            )
            == 0,
            failures,
        )

        check(
            "No fuzzy matching",
            identity.get(
                "fuzzy_matching_used"
            )
            is False,
            failures,
        )

        check(
            "No best-effort fallback",
            identity.get(
                "best_effort_fallback_used"
            )
            is False,
            failures,
        )

    # ========================================================
    # 9. Re-run Stage 9.2.4 independent validator
    # ========================================================

    print(
        "\n9. REVERIFY CANONICAL BASE ARTIFACT"
    )

    validator = (
        MatchIntelligenceBaseValidator()
    )

    try:

        independent = (
            validator.validate()
        )

        independent_ok = (
            independent.get(
                "status"
            )
            == "PASS"
        )

    except Exception as exc:

        print(
            "Independent validation error:",
            exc,
        )

        independent = {}
        independent_ok = False

    check(
        "Independent join validation PASS",
        independent_ok,
        failures,
    )

    if independent_ok:

        independent_flags = [

            "fixture_sets_exact",
            "output_fixture_ids_unique",
            "source_order_preserved",
            "schema_exact",
            "strict_identity_exact",
            "context_values_exact",
            "prediction_values_exact",
            "probabilities_exact",
            "prediction_labels_exact",
            "source_confidence_exact",
            "exact_independent_reconstruction",
            "dependency_identity_current",
            "provenance_verified",
        ]

        for flag in independent_flags:

            check(
                f"{flag} = true",
                independent.get(
                    flag
                )
                is True,
                failures,
            )

    # ========================================================
    # 10. Base artifact identity
    # ========================================================

    print(
        "\n10. BASE ARTIFACT IDENTITY"
    )

    base_artifact = report.get(
        "base_artifact",
        {}
    )

    check(
        "Base artifact path exact",
        base_artifact.get(
            "path"
        )
        ==
        relative_path(
            BASE_FILE
        ),
        failures,
    )

    check(
        "Base artifact SHA current",
        base_artifact.get(
            "sha256"
        )
        ==
        sha256_file(
            BASE_FILE
        ),
        failures,
    )

    if independent_ok:

        check(
            "Base fixture count current",
            base_artifact.get(
                "fixture_count"
            )
            ==
            independent.get(
                "fixture_count"
            ),
            failures,
        )

        check(
            "Base column count current",
            base_artifact.get(
                "column_count"
            )
            ==
            independent.get(
                "column_count"
            ),
            failures,
        )

    check(
        "Base context preservation recorded",
        base_artifact.get(
            "context_values_copied_exactly"
        )
        is True,
        failures,
    )

    check(
        "Base prediction preservation recorded",
        base_artifact.get(
            "prediction_values_copied_exactly"
        )
        is True,
        failures,
    )

    # ========================================================
    # 11. Report dependency chain
    # ========================================================

    print(
        "\n11. REPORT DEPENDENCY CHAIN"
    )

    dependency_identity = report.get(
        "dependency_identity",
        {}
    )

    check(
        "Report Stage 9.1 contract SHA current",
        dependency_identity.get(
            "stage9_intelligence_contract",
            {}
        ).get(
            "sha256"
        )
        ==
        sha256_file(
            CONTRACT_FILE
        ),
        failures,
    )

    check(
        "Report Stage 9.1 verification SHA current",
        dependency_identity.get(
            "stage9_intelligence_contract_verification",
            {}
        ).get(
            "sha256"
        )
        ==
        sha256_file(
            CONTRACT_VERIFICATION_FILE
        ),
        failures,
    )

    for name, expected_path in (
        EXPECTED_ALLOWED_INPUTS.items()
    ):

        check(
            f"Report dependency {name} current",
            dependency_identity.get(
                name,
                {}
            ).get(
                "sha256"
            )
            ==
            sha256_file(
                expected_path
            ),
            failures,
        )

    # ========================================================
    # 12. Provenance
    # ========================================================

    print(
        "\n12. PROVENANCE"
    )

    provenance = report.get(
        "provenance",
        {}
    )

    check(
        "Provenance SHA256",
        provenance.get(
            "hash_algorithm"
        )
        == "SHA256",
        failures,
    )

    check(
        "Prediction source path exact",
        provenance.get(
            "prediction_source"
        )
        ==
        relative_path(
            PREDICTIONS_FILE
        ),
        failures,
    )

    check(
        "Context source path exact",
        provenance.get(
            "context_source"
        )
        ==
        relative_path(
            CONTEXT_FILE
        ),
        failures,
    )

    check(
        "Prediction source SHA exact",
        provenance.get(
            "prediction_sha256"
        )
        ==
        sha256_file(
            PREDICTIONS_FILE
        ),
        failures,
    )

    check(
        "Context source SHA exact",
        provenance.get(
            "context_sha256"
        )
        ==
        sha256_file(
            CONTEXT_FILE
        ),
        failures,
    )

    check(
        "Base output SHA exact",
        provenance.get(
            "base_output_sha256"
        )
        ==
        sha256_file(
            BASE_FILE
        ),
        failures,
    )

    check(
        "Fixture identity provenance EXACT",
        provenance.get(
            "fixture_identity_validation"
        )
        == "EXACT",
        failures,
    )

    check(
        "Prediction value preservation EXACT",
        provenance.get(
            "prediction_value_preservation"
        )
        == "EXACT",
        failures,
    )

    check(
        "Context value preservation EXACT",
        provenance.get(
            "context_value_preservation"
        )
        == "EXACT",
        failures,
    )

    # ========================================================
    # 13. Negative-test evidence
    # ========================================================

    print(
        "\n13. NEGATIVE TEST EVIDENCE"
    )

    negative_tests = report.get(
        "negative_tests",
        {}
    )

    check(
        "Prediction dependency mutation rejected",
        negative_tests.get(
            "prediction_dependency_mutation_rejected"
        )
        is True,
        failures,
    )

    check(
        "Identity mismatch rejected",
        negative_tests.get(
            "identity_mismatch_rejected"
        )
        is True,
        failures,
    )

    check(
        "Unmatched fixture rejected",
        negative_tests.get(
            "unmatched_fixture_rejected"
        )
        is True,
        failures,
    )

    independent_evidence = report.get(
        "independent_validation",
        {}
    )

    check(
        "Tampered base rejected",
        independent_evidence.get(
            "tampered_base_rejected"
        )
        is True,
        failures,
    )

    # ========================================================
    # 14. Safety
    # ========================================================

    print(
        "\n14. STAGE 9.2 SAFETY"
    )

    safety = report.get(
        "safety",
        {}
    )

    check(
        "Upstream remains read-only",
        safety.get(
            "read_only_upstream"
        )
        is True,
        failures,
    )

    check(
        "Stage 9 remains interpretation-only",
        safety.get(
            "interpretation_only"
        )
        is True,
        failures,
    )

    false_safety_flags = [

        "provider_fetch_performed",
        "model_loaded",
        "model_executed",
        "model_modified",
        "probabilities_modified",
        "probabilities_recalibrated",
        "prediction_labels_modified",
        "source_confidence_modified",
        "stage7_artifacts_modified",
        "stage8_artifacts_modified",
        "fuzzy_matching_used",
        "best_effort_identity_fallback_used",
        "future_results_used",
        "final_test_accessed",
        "base_artifact_modified_by_validator",
        "builder_reused_for_validation",
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

    check(
        "Independent validator recorded",
        safety.get(
            "independent_validator"
        )
        is True,
        failures,
    )

    # ========================================================
    # 15. Locked Stage 9.1 safety contract
    # ========================================================

    print(
        "\n15. LOCKED CONTRACT SAFETY"
    )

    integrity = (
        contract.get(
            "stage_9_1_2",
            {}
        ).get(
            "prediction_integrity_contract",
            {}
        )
    )

    check(
        "Probabilities exact-copy contract",
        integrity.get(
            "probabilities_must_be_copied_exactly"
        )
        is True,
        failures,
    )

    check(
        "Prediction label exact-copy contract",
        integrity.get(
            "prediction_label_must_be_copied_exactly"
        )
        is True,
        failures,
    )

    check(
        "Source confidence exact-copy contract",
        integrity.get(
            "source_confidence_must_be_copied_exactly"
        )
        is True,
        failures,
    )

    check(
        "Stage 9 is not prediction model",
        integrity.get(
            "stage9_is_not_a_prediction_model"
        )
        is True,
        failures,
    )

    # ========================================================
    # 16. Pre-promotion artifact protection
    # ========================================================

    print(
        "\n16. PRE-PROMOTION WRITE PROTECTION"
    )

    check(
        "Base CSV unchanged during final verification",
        sha256_file(
            BASE_FILE
        )
        ==
        base_sha_before,
        failures,
    )

    for path in required:

        if path == REPORT_FILE:

            continue

        key = relative_path(
            path
        )

        check(
            f"{path.name} unchanged",
            sha256_file(
                path
            )
            ==
            protected_before[
                key
            ],
            failures,
        )

    # ========================================================
    # 17. Final promotion
    # ========================================================

    print(
        "\n17. STAGE 9.2.5 FINAL PROMOTION"
    )

    pre_promotion_pass = (
        len(
            failures
        )
        == 0
    )

    if (
        pre_promotion_pass
        and
        not already_complete
    ):

        verified_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        final_report = load_json(
            REPORT_FILE
        )

        final_sub_stages = dict(
            final_report.get(
                "sub_stages",
                {}
            )
        )

        final_sub_stages[
            "9.2.1"
        ] = "PASS"

        final_sub_stages[
            "9.2.2"
        ] = "PASS"

        final_sub_stages[
            "9.2.3"
        ] = "PASS"

        final_sub_stages[
            "9.2.4"
        ] = "PASS"

        final_sub_stages[
            "9.2.5"
        ] = "PASS"

        final_report[
            "sub_stages"
        ] = final_sub_stages

        final_report[
            "status"
        ] = "PASS"

        final_report[
            "stage_9_2_complete"
        ] = True

        final_report[
            "stage_9_2_status"
        ] = "COMPLETE"

        final_report[
            "prediction_context_join_layer"
        ] = "VERIFIED"

        final_report[
            "stage_9_2_completed_at_utc"
        ] = verified_at

        final_report[
            "final_gate"
        ] = {

            "stage":
                "9.2.5",

            "status":
                "PASS",

            "verified_at_utc":
                verified_at,

            "prediction_source_gate_verified":
                True,

            "fixture_identity_reconciliation_verified":
                True,

            "strict_prediction_context_join_verified":
                True,

            "independent_join_validation_verified":
                True,

            "fixture_context_runtime_ready":
                True,

            "fixture_sets_exact":
                True,

            "fixture_identity_exact":
                True,

            "base_schema_exact":
                True,

            "context_values_preserved_exactly":
                True,

            "prediction_values_preserved_exactly":
                True,

            "probabilities_preserved_exactly":
                True,

            "prediction_labels_preserved_exactly":
                True,

            "source_confidence_preserved_exactly":
                True,

            "source_order_preserved":
                True,

            "dependency_identity_current":
                True,

            "provenance_verified":
                True,

            "negative_tests_verified":
                True,

            "upstream_write_protection_verified":
                True,

            "stage9_contract_unchanged":
                True,

            "base_artifact_unchanged_by_final_gate":
                True,

            "model_not_loaded":
                True,

            "model_not_executed":
                True,

            "probability_mutation":
                False,

            "context_as_model_features":
                False,

            "final_test_accessed":
                False,

            "fail_closed":
                True,

            "stage9_ready_for_9_3":
                True,
        }

        final_report[
            "failures"
        ] = []

        save_json_atomic(
            REPORT_FILE,
            final_report,
        )

        print(
            REPORT_FILE
        )

    # ========================================================
    # 18. Persisted final state
    # ========================================================

    print(
        "\n18. PERSISTED FINAL STATE"
    )

    persisted = load_json(
        REPORT_FILE
    )

    check(
        "Stage 9.2 status PASS persisted",
        persisted.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 9.2 COMPLETE persisted",
        (
            persisted.get(
                "stage_9_2_complete"
            )
            is True

            and

            persisted.get(
                "stage_9_2_status"
            )
            == "COMPLETE"
        ),
        failures,
    )

    check(
        "Prediction-Context Join Layer VERIFIED",
        persisted.get(
            "prediction_context_join_layer"
        )
        == "VERIFIED",
        failures,
    )

    for substage in (

        "9.2.1",
        "9.2.2",
        "9.2.3",
        "9.2.4",
        "9.2.5",
    ):

        check(
            f"{substage} PASS persisted",
            persisted.get(
                "sub_stages",
                {}
            ).get(
                substage
            )
            == "PASS",
            failures,
        )

    final_gate = persisted.get(
        "final_gate",
        {}
    )

    check(
        "Final gate PASS persisted",
        final_gate.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Stage 9 ready for 9.3 persisted",
        final_gate.get(
            "stage9_ready_for_9_3"
        )
        is True,
        failures,
    )

    check(
        "Exact prediction preservation persisted",
        (
            final_gate.get(
                "probabilities_preserved_exactly"
            )
            is True

            and

            final_gate.get(
                "prediction_labels_preserved_exactly"
            )
            is True

            and

            final_gate.get(
                "source_confidence_preserved_exactly"
            )
            is True
        ),
        failures,
    )

    # ========================================================
    # 19. Post-promotion protection
    # ========================================================

    print(
        "\n19. POST-PROMOTION WRITE PROTECTION"
    )

    check(
        "Base CSV unchanged after promotion",
        sha256_file(
            BASE_FILE
        )
        ==
        base_sha_before,
        failures,
    )

    for path in required:

        if path == REPORT_FILE:

            continue

        key = relative_path(
            path
        )

        check(
            f"{path.name} still unchanged",
            sha256_file(
                path
            )
            ==
            protected_before[
                key
            ],
            failures,
        )

    # ========================================================
    # 20. Final smoke validation
    # ========================================================

    print(
        "\n20. FINAL INDEPENDENT SMOKE VALIDATION"
    )

    try:

        post_validation = (
            MatchIntelligenceBaseValidator()
            .validate()
        )

        post_validation_ok = (
            post_validation.get(
                "status"
            )
            == "PASS"
        )

    except Exception as exc:

        print(
            "Post-promotion validation error:",
            exc,
        )

        post_validation_ok = False

    check(
        "Independent validator remains PASS after promotion",
        post_validation_ok,
        failures,
    )

    # ========================================================
    # Final output
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
            "STAGE 9.2.1: PASS"
        )

        print(
            "STAGE 9.2.2: PASS"
        )

        print(
            "STAGE 9.2.3: PASS"
        )

        print(
            "STAGE 9.2.4: PASS"
        )

        print(
            "STAGE 9.2.5: PASS"
        )

        print()

        print(
            "STAGE 9.2: COMPLETE"
        )

        print(
            "PREDICTION-CONTEXT JOIN LAYER: VERIFIED"
        )

        print(
            "STAGE 9 READY FOR 9.3"
        )

    else:

        print(
            "STAGE 9.2.5: FAIL"
        )

        print(
            "STAGE 9.2: INCOMPLETE"
        )

        print(
            "PREDICTION-CONTEXT JOIN LAYER: NOT VERIFIED"
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