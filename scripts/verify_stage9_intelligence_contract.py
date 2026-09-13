"""
FixtureIQ Stage 9.1.1 + 9.1.2
Independent Match Intelligence Contract Verification.

Verifies:
- Stage 7 and Stage 8 final gates remain verified
- allowed Stage 9 inputs are exact
- every allowed input is read-only
- input artifact hashes are current
- prediction values have one authoritative source
- context values have one authoritative source
- model operations are forbidden
- probability mutation is forbidden
- context-as-model-feature use is forbidden
- final-test use is forbidden
- odds use is forbidden
- Stage 7 / Stage 8 writes are forbidden
- Stage 9 is interpretation-only

Creates:
data/processed/intelligence/
stage9_intelligence_contract_verification.json

9.1.3 through 9.1.5 remain pending.
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
# Source artifacts
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
# Stage 9 files
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
# Contract expectations
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


EXPECTED_FORBIDDEN_OPERATIONS = {

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
        "FixtureIQ Stage 9.1.1 + 9.1.2"
    )

    print(
        "Independent Intelligence Contract Verification"
    )

    print("=" * 72)

    failures = []

    # ========================================================
    # 1. Required artifacts
    # ========================================================

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    required = list(
        EXPECTED_ALLOWED_INPUTS.values()
    )

    required.append(
        CONTRACT_FILE
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
    # 2. Upstream final gates
    # ========================================================

    print(
        "\n2. UPSTREAM FINAL GATES"
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

    contract = load_json(
        CONTRACT_FILE
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
        == "MATCH_INTELLIGENCE_CONTRACT",
        failures,
    )

    check(
        "Contract status PARTIAL_LOCK",
        contract.get(
            "status"
        )
        == "PARTIAL_LOCK",
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

    check(
        "Stage 9.1 status IN_PROGRESS",
        contract.get(
            "stage_9_1_status"
        )
        == "IN_PROGRESS",
        failures,
    )

    sub_stages = contract.get(
        "sub_stages",
        {}
    )

    check(
        "9.1.1 PASS",
        sub_stages.get(
            "9.1.1"
        )
        == "PASS",
        failures,
    )

    check(
        "9.1.2 PASS",
        sub_stages.get(
            "9.1.2"
        )
        == "PASS",
        failures,
    )

    check(
        "9.1.3 PENDING",
        sub_stages.get(
            "9.1.3"
        )
        == "PENDING",
        failures,
    )

    check(
        "9.1.4 PENDING",
        sub_stages.get(
            "9.1.4"
        )
        == "PENDING",
        failures,
    )

    check(
        "9.1.5 PENDING",
        sub_stages.get(
            "9.1.5"
        )
        == "PENDING",
        failures,
    )

    # ========================================================
    # 4. Stage 9 principles
    # ========================================================

    print(
        "\n4. MATCH INTELLIGENCE PRINCIPLES"
    )

    principles = contract.get(
        "principles",
        {}
    )

    check(
        "Stage 7 is prediction authority",
        principles.get(
            "prediction_layer_authority"
        )
        == "STAGE7",
        failures,
    )

    check(
        "Stage 8 is context authority",
        principles.get(
            "context_layer_authority"
        )
        == "STAGE8",
        failures,
    )

    check(
        "Stage 9 role = interpretation",
        principles.get(
            "stage9_role"
        )
        == "INTERPRETATION_NOT_PREDICTION",
        failures,
    )

    check(
        "Prediction/context separation required",
        principles.get(
            "prediction_and_context_separation"
        )
        is True,
        failures,
    )

    check(
        "Context can explain prediction",
        principles.get(
            "context_can_explain_prediction"
        )
        is True,
        failures,
    )

    check(
        "Context cannot change prediction",
        principles.get(
            "context_can_change_prediction"
        )
        is False,
        failures,
    )

    # ========================================================
    # 5. Stage 9.1.1 allowed input set
    # ========================================================

    print(
        "\n5. STAGE 9.1.1 ALLOWED INPUT SET"
    )

    stage_9_1_1 = contract.get(
        "stage_9_1_1",
        {}
    )

    allowed_inputs = stage_9_1_1.get(
        "allowed_inputs",
        {}
    )

    check(
        "9.1.1 status PASS",
        stage_9_1_1.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Exactly 11 allowed input keys",
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
        input_name,
        expected_path,
    ) in EXPECTED_ALLOWED_INPUTS.items():

        item = allowed_inputs.get(
            input_name,
            {}
        )

        check(
            f"{input_name} path exact",
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
            f"{input_name} SHA current",
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
            f"{input_name} required",
            item.get(
                "required"
            )
            is True,
            failures,
        )

        check(
            f"{input_name} read-only",
            item.get(
                "read_only"
            )
            is True,
            failures,
        )

        check(
            f"{input_name} Stage 9 write prohibited",
            item.get(
                "stage9_write_allowed"
            )
            is False,
            failures,
        )

    # ========================================================
    # 6. Source authority
    # ========================================================

    print(
        "\n6. SOURCE AUTHORITY"
    )

    authority = stage_9_1_1.get(
        "input_authority",
        {}
    )

    check(
        "Prediction source of truth exact",
        authority.get(
            "prediction_values"
        )
        == "production_predictions",
        failures,
    )

    check(
        "Context source of truth exact",
        authority.get(
            "context_values"
        )
        == "enriched_upcoming_fixtures",
        failures,
    )

    check(
        "Prediction values override context",
        authority.get(
            "prediction_values_override_context"
        )
        is True,
        failures,
    )

    check(
        "Context may explain prediction",
        authority.get(
            "context_may_explain_prediction"
        )
        is True,
        failures,
    )

    check(
        "Context may not replace prediction",
        authority.get(
            "context_may_replace_prediction"
        )
        is False,
        failures,
    )

    check(
        "Context may not adjust prediction",
        authority.get(
            "context_may_adjust_prediction"
        )
        is False,
        failures,
    )

    # ========================================================
    # 7. Disallowed hidden inputs
    # ========================================================

    print(
        "\n7. HIDDEN INPUT EXCLUSION"
    )

    serialized_allowed_inputs = json.dumps(
        allowed_inputs
    ).lower()

    check(
        "Selected model not an operational input",
        "selected_model.joblib"
        not in serialized_allowed_inputs,
        failures,
    )

    check(
        "Production feature matrix not an intelligence input",
        "production_features.csv"
        not in serialized_allowed_inputs,
        failures,
    )

    check(
        "Training matrix not an intelligence input",
        "x_train.csv"
        not in serialized_allowed_inputs,
        failures,
    )

    check(
        "Final-test artifacts not allowed inputs",
        "final_test"
        not in serialized_allowed_inputs,
        failures,
    )

    check(
        "Bookmaker odds not allowed inputs",
        "odds"
        not in serialized_allowed_inputs,
        failures,
    )

    # ========================================================
    # 8. Stage 9.1.2 forbidden operations
    # ========================================================

    print(
        "\n8. STAGE 9.1.2 FORBIDDEN OPERATIONS"
    )

    stage_9_1_2 = contract.get(
        "stage_9_1_2",
        {}
    )

    forbidden = stage_9_1_2.get(
        "forbidden_operations",
        {}
    )

    check(
        "9.1.2 status PASS",
        stage_9_1_2.get(
            "status"
        )
        == "PASS",
        failures,
    )

    check(
        "Forbidden operation set exact",
        set(
            forbidden.keys()
        )
        ==
        EXPECTED_FORBIDDEN_OPERATIONS,
        failures,
    )

    check(
        "All forbidden operations enforced",
        all(
            forbidden.get(
                key
            )
            is True

            for key in (
                EXPECTED_FORBIDDEN_OPERATIONS
            )
        ),
        failures,
    )

    # ========================================================
    # 9. Critical protection checks
    # ========================================================

    print(
        "\n9. CRITICAL PROTECTION CHECKS"
    )

    critical_forbidden = [

        "model_loading",
        "model_execution",
        "model_retraining",
        "model_reselection",
        "hyperparameter_tuning",

        "probability_recalibration",
        "probability_modification",
        "prediction_label_modification",
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
        "final_test_access",
        "final_test_reuse",

        "bookmaker_odds_use",

        "outcome_based_threshold_tuning",

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
    # 10. Prediction integrity contract
    # ========================================================

    print(
        "\n10. PREDICTION INTEGRITY CONTRACT"
    )

    integrity = stage_9_1_2.get(
        "prediction_integrity_contract",
        {}
    )

    check(
        "Prediction source exact",
        integrity.get(
            "prediction_source"
        )
        == "production_predictions",
        failures,
    )

    check(
        "Probability fields exact",
        integrity.get(
            "probability_fields"
        )
        ==
        [
            "prob_home_win",
            "prob_draw",
            "prob_away_win",
        ],
        failures,
    )

    check(
        "Prediction label field exact",
        integrity.get(
            "prediction_label_source_field"
        )
        == "predicted_label",
        failures,
    )

    check(
        "Source confidence field exact",
        integrity.get(
            "source_confidence_field"
        )
        == "confidence",
        failures,
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
    # 11. Safety boundary
    # ========================================================

    print(
        "\n11. STAGE 9.1 SAFETY BOUNDARY"
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

    expected_false_safety = [

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

    for flag in expected_false_safety:

        check(
            f"{flag} = false",
            safety.get(
                flag
            )
            is False,
            failures,
        )

    # ========================================================
    # 12. Final decision
    # ========================================================

    print(
        "\n12. STAGE 9.1.1 + 9.1.2 DECISION"
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

        verification = {

            "stage":
                "9.1",

            "status":
                "PARTIAL_PASS",

            "stage_9_1_complete":
                False,

            "stage_9_1_status":
                "IN_PROGRESS",

            "verified_at_utc":
                verified_at,

            "contract_sha256":
                sha256_file(
                    CONTRACT_FILE
                ),

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

            "allowed_inputs":
                "VERIFIED",

            "forbidden_operations":
                "VERIFIED",

            "verification": {

                "allowed_input_set_exact":
                    True,

                "all_input_hashes_current":
                    True,

                "all_inputs_read_only":
                    True,

                "stage9_upstream_writes_prohibited":
                    True,

                "prediction_authority_verified":
                    True,

                "context_authority_verified":
                    True,

                "hidden_input_exclusion_verified":
                    True,

                "model_operations_forbidden":
                    True,

                "prediction_mutation_forbidden":
                    True,

                "context_as_model_feature_forbidden":
                    True,

                "final_test_access_forbidden":
                    True,

                "bookmaker_odds_forbidden":
                    True,

                "future_results_forbidden":
                    True,

                "outcome_based_threshold_tuning_forbidden":
                    True,

                "fuzzy_identity_join_forbidden":
                    True,

                "prediction_integrity_contract_verified":
                    True,

                "interpretation_only_boundary_verified":
                    True,
            },

            "safety": {

                "read_only":
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

                "predictions_modified":
                    False,

                "stage7_artifacts_modified":
                    False,

                "stage8_artifacts_modified":
                    False,

                "final_test_accessed":
                    False,
            },

            "failures":
                [],
        }

        save_json_atomic(
            VERIFICATION_FILE,
            verification,
        )

        print(
            VERIFICATION_FILE
        )

        persisted = load_json(
            VERIFICATION_FILE
        )

        check(
            "Verification PARTIAL_PASS persisted",
            persisted.get(
                "status"
            )
            == "PARTIAL_PASS",
            failures,
        )

        check(
            "9.1.1 PASS persisted",
            persisted.get(
                "sub_stages",
                {}
            ).get(
                "9.1.1"
            )
            == "PASS",
            failures,
        )

        check(
            "9.1.2 PASS persisted",
            persisted.get(
                "sub_stages",
                {}
            ).get(
                "9.1.2"
            )
            == "PASS",
            failures,
        )

        check(
            "9.1.3 remains PENDING",
            persisted.get(
                "sub_stages",
                {}
            ).get(
                "9.1.3"
            )
            == "PENDING",
            failures,
        )

        overall_pass = (
            len(
                failures
            )
            == 0
        )

    # ========================================================
    # Final output
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 9.1.1: PASS"
        )

        print(
            "ALLOWED INPUTS: VERIFIED"
        )

        print(
            "STAGE 9.1.2: PASS"
        )

        print(
            "FORBIDDEN OPERATIONS: VERIFIED"
        )

        print(
            "STAGE 9.1: IN PROGRESS"
        )

    else:

        print(
            "STAGE 9.1.1 / 9.1.2: FAIL"
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