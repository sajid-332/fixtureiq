"""
FixtureIQ Stage 8.1.6
Final Stage 8.1 Context Contract Verification & Lock.

Independently verifies:

8.1.1 Scope & Safety Boundary
8.1.2 Trusted Input Contract
8.1.3 Canonical Team Context Schema
8.1.4 Freshness & Provenance Rules
8.1.5 Output Artifact Contract

If all checks pass:
- 8.1.6 is LOCKED
- Stage 8.1 becomes COMPLETE
- context contract becomes LOCKED_CONTEXT_CONTRACT
- verification evidence hashes are recorded

No ML model is loaded or executed.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# Paths
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

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

CONTEXT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "context"
)

CONTRACT_FILE = (
    CONTEXT_DIR
    / "stage8_context_contract.json"
)

VERIFICATION_FILE = (
    CONTEXT_DIR
    / "stage8_context_contract_verification.json"
)

SELECTED_MODEL_FILE = (
    MODEL_DIR
    / "selected"
    / "selected_model.joblib"
)

SERVING_CONTRACT_FILE = (
    MODEL_DIR
    / "production_serving_contract.json"
)

STAGE7_8_FILE = (
    PRODUCTION_DIR
    / "stage7_8_final_verification.json"
)

STAGE7_9_FILE = (
    PRODUCTION_DIR
    / "stage7_9_final_verification.json"
)

PRODUCTION_HISTORY_FILE = (
    PRODUCTION_DIR
    / "production_history.csv"
)

UPCOMING_FIXTURES_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
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


def sha256_file(
    path: Path,
) -> str:

    if not path.exists():

        raise FileNotFoundError(
            f"Required file missing: {path}"
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
        "FixtureIQ Stage 8.1.6"
    )

    print(
        "Final Stage 8.1 Context Contract Verification"
    )

    print("=" * 72)

    failures = []

    # ========================================================
    # 1. Required foundation
    # ========================================================

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    required_files = [

        CONTRACT_FILE,
        SERVING_CONTRACT_FILE,
        SELECTED_MODEL_FILE,

        STAGE7_8_FILE,
        STAGE7_9_FILE,

        PRODUCTION_HISTORY_FILE,
        UPCOMING_FIXTURES_FILE,
    ]

    for path in required_files:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        print(
            "\nSTAGE 8.1.6: FAIL"
        )

        sys.exit(1)

    contract = load_json(
        CONTRACT_FILE
    )

    stage7_8 = load_json(
        STAGE7_8_FILE
    )

    stage7_9 = load_json(
        STAGE7_9_FILE
    )

    sub_stages = contract.get(
        "sub_stages",
        {}
    )

    # ========================================================
    # 2. Stage 7 foundation
    # ========================================================

    print(
        "\n2. UPSTREAM FOUNDATION"
    )

    check(
        "Stage 7.8 PASS",
        str(
            stage7_8.get(
                "status",
                ""
            )
        )
        .upper()
        == "PASS",
        failures,
    )

    check(
        "Stage 7.9 PASS",
        str(
            stage7_9.get(
                "status",
                ""
            )
        )
        .upper()
        == "PASS",
        failures,
    )

    check(
        "Stage 7.9 COMPLETE",
        stage7_9.get(
            "stage_7_9_complete"
        )
        is True,
        failures,
    )

    check(
        "Production serving stack VERIFIED",
        stage7_9.get(
            "production_serving_stack"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 3. Previous Stage 8.1 sections
    # ========================================================

    print(
        "\n3. PREVIOUS STAGE 8.1 LOCKS"
    )

    for stage in (
        "8.1.1",
        "8.1.2",
        "8.1.3",
        "8.1.4",
        "8.1.5",
    ):

        check(
            f"{stage} LOCKED",
            sub_stages.get(
                stage
            )
            == "LOCKED",
            failures,
        )

    # ========================================================
    # 4. Scope & model safety
    # ========================================================

    print(
        "\n4. SCOPE & MODEL SAFETY"
    )

    protection = contract.get(
        "model_protection",
        {}
    )

    locked_model = contract.get(
        "locked_model",
        {}
    )

    stage7_protection = contract.get(
        "stage7_protection",
        {}
    )

    check(
        "Purpose LIVE_EPL_CONTEXT_LAYER",
        contract.get(
            "purpose"
        )
        == "LIVE_EPL_CONTEXT_LAYER",
        failures,
    )

    check(
        "Context-only true",
        contract.get(
            "context_only"
        )
        is True,
        failures,
    )

    prohibited_flags = {

        "model_mutation_allowed":
            False,

        "retraining_allowed":
            False,

        "model_selection_allowed":
            False,

        "hyperparameter_tuning_allowed":
            False,

        "feature_schema_mutation_allowed":
            False,

        "prediction_mutation_allowed":
            False,

        "final_test_reuse_allowed":
            False,

        "standings_as_model_features_allowed":
            False,

        "form_as_model_features_allowed":
            False,
    }

    for key, expected in prohibited_flags.items():

        check(
            f"{key} = false",
            protection.get(
                key
            )
            is expected,
            failures,
        )

    actual_model_sha = sha256_file(
        SELECTED_MODEL_FILE
    )

    check(
        "Locked model random_forest",
        locked_model.get(
            "model_id"
        )
        == "random_forest",
        failures,
    )

    check(
        "Feature count remains 86",
        locked_model.get(
            "feature_count"
        )
        == 86,
        failures,
    )

    check(
        "Locked model SHA matches actual",
        locked_model.get(
            "sha256"
        )
        == actual_model_sha,
        failures,
    )

    check(
        "Existing probabilities protected",
        stage7_protection.get(
            "stage8_may_change_existing_probabilities"
        )
        is False,
        failures,
    )

    check(
        "Final test remains closed",
        stage7_protection.get(
            "stage8_may_reopen_final_test"
        )
        is False,
        failures,
    )

    # ========================================================
    # 5. Trusted inputs
    # ========================================================

    print(
        "\n5. TRUSTED INPUT CONTRACT"
    )

    trusted = contract.get(
        "trusted_inputs",
        {}
    )

    history = trusted.get(
        "production_history",
        {}
    )

    fixtures = trusted.get(
        "upcoming_fixtures",
        {}
    )

    provider = trusted.get(
        "live_context_provider",
        {}
    )

    failure_policy = contract.get(
        "input_failure_policy",
        {}
    )

    check(
        "Production history READ_ONLY",
        history.get(
            "access"
        )
        == "READ_ONLY",
        failures,
    )

    check(
        "Upcoming fixtures READ_ONLY",
        fixtures.get(
            "access"
        )
        == "READ_ONLY",
        failures,
    )

    check(
        "Live provider football-data.org",
        provider.get(
            "provider"
        )
        == "football-data.org",
        failures,
    )

    check(
        "Competition code PL",
        provider.get(
            "competition_code"
        )
        == "PL",
        failures,
    )

    check(
        "Configured season 2026",
        provider.get(
            "configured_season"
        )
        == 2026,
        failures,
    )

    check(
        "Missing input FAIL_CLOSED",
        failure_policy.get(
            "missing_required_input"
        )
        == "FAIL_CLOSED",
        failures,
    )

    check(
        "Provider failure FAIL_CLOSED",
        failure_policy.get(
            "provider_failure"
        )
        == "FAIL_CLOSED",
        failures,
    )

    # ========================================================
    # 6. Canonical schema
    # ========================================================

    print(
        "\n6. CANONICAL TEAM CONTEXT SCHEMA"
    )

    schema = contract.get(
        "canonical_team_context_schema",
        {}
    )

    identity = schema.get(
        "team_identity",
        {}
    )

    standings = schema.get(
        "standings",
        {}
    )

    form = schema.get(
        "current_form",
        {}
    )

    check(
        "Expected EPL teams = 20",
        schema.get(
            "expected_current_epl_team_count"
        )
        == 20,
        failures,
    )

    check(
        "Namespace fixtureiq-team",
        identity.get(
            "namespace"
        )
        == "fixtureiq-team",
        failures,
    )

    expected_standings_fields = {

        "position",
        "played",
        "won",
        "drawn",
        "lost",
        "goals_for",
        "goals_against",
        "goal_difference",
        "points",
    }

    check(
        "Standings schema exact",
        set(
            standings.get(
                "fields",
                {}
            ).keys()
        )
        == expected_standings_fields,
        failures,
    )

    check(
        "Default form window = 5",
        form.get(
            "default_window"
        )
        == 5,
        failures,
    )

    check(
        "Form current season only",
        form.get(
            "season_scope"
        )
        == "CURRENT_PRODUCTION_SEASON_ONLY",
        failures,
    )

    check(
        "Short form window allowed",
        form.get(
            "allow_short_window"
        )
        is True,
        failures,
    )

    # ========================================================
    # 7. Freshness & provenance
    # ========================================================

    print(
        "\n7. FRESHNESS & PROVENANCE"
    )

    freshness = contract.get(
        "freshness_and_provenance",
        {}
    )

    form_policy = freshness.get(
        "form_policy",
        {}
    )

    team_context_policy = freshness.get(
        "team_context_policy",
        {}
    )

    fixture_context_policy = freshness.get(
        "fixture_context_policy",
        {}
    )

    runtime_policy = freshness.get(
        "runtime_policy",
        {}
    )

    check(
        "Freshness DEPENDENCY_BASED",
        freshness.get(
            "freshness_mode"
        )
        == "DEPENDENCY_BASED",
        failures,
    )

    check(
        "Form uses completed matches only",
        form_policy.get(
            "completed_matches_only"
        )
        is True,
        failures,
    )

    check(
        "History cutoff required",
        form_policy.get(
            "history_cutoff_required"
        )
        is True,
        failures,
    )

    check(
        "Team context requires fresh standings",
        team_context_policy.get(
            "requires_fresh_standings"
        )
        is True,
        failures,
    )

    check(
        "Team context requires fresh form",
        team_context_policy.get(
            "requires_fresh_form"
        )
        is True,
        failures,
    )

    check(
        "Fixture context requires fresh fixtures",
        fixture_context_policy.get(
            "requires_fresh_upcoming_fixtures"
        )
        is True,
        failures,
    )

    check(
        "Fixture cannot affect own form",
        fixture_context_policy.get(
            "fixture_may_affect_its_own_form"
        )
        is False,
        failures,
    )

    check(
        "Runtime FAIL_CLOSED",
        runtime_policy.get(
            "failure_mode"
        )
        == "FAIL_CLOSED",
        failures,
    )

    check(
        "Silent stale fallback prohibited",
        runtime_policy.get(
            "silent_stale_fallback_allowed"
        )
        is False,
        failures,
    )

    # ========================================================
    # 8. Stage 8.1.5 output artifact contract
    # ========================================================

    print(
        "\n8. STAGE 8.1.5 - OUTPUT ARTIFACT CONTRACT"
    )

    output_contract = contract.get(
        "output_artifact_contract",
        {}
    )

    outputs = output_contract.get(
        "outputs",
        {}
    )

    output_rules = output_contract.get(
        "rules",
        {}
    )

    pairs = output_contract.get(
        "data_report_pairs",
        []
    )

    expected_outputs = {

        "stage8_context_contract":
            (
                "data/processed/context/"
                "stage8_context_contract.json"
            ),

        "stage8_context_contract_verification":
            (
                "data/processed/context/"
                "stage8_context_contract_verification.json"
            ),

        "current_standings":
            (
                "data/processed/context/"
                "current_standings.csv"
            ),

        "standings_report":
            (
                "data/processed/context/"
                "standings_report.json"
            ),

        "current_team_form":
            (
                "data/processed/context/"
                "current_team_form.csv"
            ),

        "team_form_report":
            (
                "data/processed/context/"
                "team_form_report.json"
            ),

        "team_context":
            (
                "data/processed/context/"
                "team_context.csv"
            ),

        "team_context_report":
            (
                "data/processed/context/"
                "team_context_report.json"
            ),

        "enriched_upcoming_fixtures":
            (
                "data/processed/context/"
                "enriched_upcoming_fixtures.csv"
            ),

        "fixture_context_report":
            (
                "data/processed/context/"
                "fixture_context_report.json"
            ),

        "context_api_verification":
            (
                "data/processed/context/"
                "context_api_verification.json"
            ),

        "context_runtime_verification":
            (
                "data/processed/context/"
                "context_runtime_verification.json"
            ),

        "stage8_final_verification":
            (
                "data/processed/context/"
                "stage8_final_verification.json"
            ),
    }

    check(
        "Output root correct",
        output_contract.get(
            "output_root"
        )
        == "data/processed/context",
        failures,
    )

    check(
        "Output owner STAGE_8",
        output_contract.get(
            "owner"
        )
        == "STAGE_8",
        failures,
    )

    check(
        "Stage 7 output write prohibited",
        output_contract.get(
            "stage7_output_write_allowed"
        )
        is False,
        failures,
    )

    check(
        "Output artifact set exact",
        set(
            outputs.keys()
        )
        == set(
            expected_outputs.keys()
        ),
        failures,
    )

    for name, expected_path in expected_outputs.items():

        artifact = outputs.get(
            name,
            {}
        )

        actual_path = artifact.get(
            "path"
        )

        check(
            f"{name} path",
            actual_path
            == expected_path,
            failures,
        )

        check(
            f"{name} under context root",
            (
                isinstance(
                    actual_path,
                    str,
                )
                and
                actual_path.startswith(
                    "data/processed/context/"
                )
            ),
            failures,
        )

        check(
            f"{name} not Stage 7 output",
            (
                isinstance(
                    actual_path,
                    str,
                )
                and
                not actual_path.startswith(
                    "data/processed/production/"
                )
            ),
            failures,
        )

    declared_paths = [

        artifact.get(
            "path"
        )

        for artifact in outputs.values()
    ]

    check(
        "Output paths unique",
        (
            len(
                declared_paths
            )
            ==
            len(
                set(
                    declared_paths
                )
            )
        ),
        failures,
    )

    expected_pairs = [

        [
            "current_standings",
            "standings_report",
        ],

        [
            "current_team_form",
            "team_form_report",
        ],

        [
            "team_context",
            "team_context_report",
        ],

        [
            "enriched_upcoming_fixtures",
            "fixture_context_report",
        ],
    ]

    check(
        "Data/report pairs exact",
        pairs
        == expected_pairs,
        failures,
    )

    check(
        "Stage 7 overwrite prohibited",
        output_rules.get(
            "stage7_artifacts_may_be_overwritten"
        )
        is False,
        failures,
    )

    check(
        "Derived provenance required",
        output_rules.get(
            "derived_artifacts_require_provenance"
        )
        is True,
        failures,
    )

    check(
        "Dependency identity required",
        output_rules.get(
            "derived_artifacts_require_dependency_identity"
        )
        is True,
        failures,
    )

    check(
        "Unverified public context prohibited",
        output_rules.get(
            "public_context_must_come_from_verified_artifacts"
        )
        is True,
        failures,
    )

    check(
        "Partial unverified serving prohibited",
        output_rules.get(
            "partial_unverified_output_serving_allowed"
        )
        is False,
        failures,
    )

    check(
        "Stage 8 final evidence hashing required",
        output_rules.get(
            "stage8_final_gate_must_hash_evidence"
        )
        is True,
        failures,
    )

    check(
        "Future artifacts not required yet",
        output_rules.get(
            "future_stage_artifacts_need_not_exist_during_stage8_1"
        )
        is True,
        failures,
    )

    # ========================================================
    # 9. Stage 8.1.6 final decision
    # ========================================================

    print(
        "\n9. STAGE 8.1.6 - FINAL CONTRACT GATE"
    )

    final_pass = (
        len(
            failures
        )
        == 0
    )

    if final_pass:

        # ----------------------------------------------------
        # Lock the contract
        # ----------------------------------------------------

        final_sub_stages = dict(
            contract.get(
                "sub_stages",
                {}
            )
        )

        final_sub_stages[
            "8.1.6"
        ] = "LOCKED"

        contract[
            "sub_stages"
        ] = final_sub_stages

        contract[
            "stage_8_1_complete"
        ] = True

        contract[
            "stage_8_1_status"
        ] = "COMPLETE"

        contract[
            "contract_status"
        ] = "LOCKED_CONTEXT_CONTRACT"

        if not contract.get(
            "locked_at_utc"
        ):

            contract[
                "locked_at_utc"
            ] = datetime.now(
                timezone.utc
            ).isoformat()

        contract[
            "updated_at_utc"
        ] = datetime.now(
            timezone.utc
        ).isoformat()

        with CONTRACT_FILE.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                contract,
                file,
                indent=2,
            )

        # ----------------------------------------------------
        # Reload to verify persisted lock
        # ----------------------------------------------------

        locked_contract = load_json(
            CONTRACT_FILE
        )

        persisted_lock_ok = (

            locked_contract.get(
                "stage_8_1_complete"
            )
            is True

            and

            locked_contract.get(
                "stage_8_1_status"
            )
            == "COMPLETE"

            and

            locked_contract.get(
                "contract_status"
            )
            == "LOCKED_CONTEXT_CONTRACT"

            and

            locked_contract.get(
                "sub_stages",
                {}
            ).get(
                "8.1.6"
            )
            == "LOCKED"
        )

        check(
            "Final contract lock persisted",
            persisted_lock_ok,
            failures,
        )

        final_pass = (
            len(
                failures
            )
            == 0
        )

    # ========================================================
    # 10. Evidence hashes
    # ========================================================

    print(
        "\n10. EVIDENCE HASHES"
    )

    evidence_hashes = {}

    if CONTRACT_FILE.exists():

        evidence_hashes[
            "stage8_context_contract"
        ] = sha256_file(
            CONTRACT_FILE
        )

    evidence_hashes[
        "selected_model"
    ] = sha256_file(
        SELECTED_MODEL_FILE
    )

    evidence_hashes[
        "stage7_8_final_verification"
    ] = sha256_file(
        STAGE7_8_FILE
    )

    evidence_hashes[
        "stage7_9_final_verification"
    ] = sha256_file(
        STAGE7_9_FILE
    )

    for name, digest in evidence_hashes.items():

        print(
            f"{name}: {digest}"
        )

    # ========================================================
    # 11. Save final 8.1 verification
    # ========================================================

    print(
        "\n11. SAVE VERIFICATION"
    )

    if final_pass:

        sub_stage_results = {

            "8.1.1":
                "PASS",

            "8.1.2":
                "PASS",

            "8.1.3":
                "PASS",

            "8.1.4":
                "PASS",

            "8.1.5":
                "PASS",

            "8.1.6":
                "PASS",
        }

    else:

        sub_stage_results = {

            "8.1.1":
                (
                    "PASS"
                    if sub_stages.get(
                        "8.1.1"
                    )
                    == "LOCKED"
                    else "FAIL"
                ),

            "8.1.2":
                (
                    "PASS"
                    if sub_stages.get(
                        "8.1.2"
                    )
                    == "LOCKED"
                    else "FAIL"
                ),

            "8.1.3":
                (
                    "PASS"
                    if sub_stages.get(
                        "8.1.3"
                    )
                    == "LOCKED"
                    else "FAIL"
                ),

            "8.1.4":
                (
                    "PASS"
                    if sub_stages.get(
                        "8.1.4"
                    )
                    == "LOCKED"
                    else "FAIL"
                ),

            "8.1.5":
                (
                    "PASS"
                    if sub_stages.get(
                        "8.1.5"
                    )
                    == "LOCKED"
                    else "FAIL"
                ),

            "8.1.6":
                "FAIL",
        }

    verification = {

        "stage":
            "8.1",

        "status":
            (
                "PASS"
                if final_pass
                else "FAIL"
            ),

        "stage_8_1_complete":
            bool(
                final_pass
            ),

        "stage_8_1_status":
            (
                "COMPLETE"
                if final_pass
                else "INCOMPLETE"
            ),

        "context_contract":
            (
                "LOCKED"
                if final_pass
                else "NOT_LOCKED"
            ),

        "verified_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "sub_stages":
            sub_stage_results,

        "scope_safety_boundary":
            (
                "LOCKED"
                if final_pass
                else "NOT_VERIFIED"
            ),

        "trusted_input_contract":
            (
                "LOCKED"
                if final_pass
                else "NOT_VERIFIED"
            ),

        "canonical_team_context_schema":
            (
                "LOCKED"
                if final_pass
                else "NOT_VERIFIED"
            ),

        "freshness_provenance_policy":
            (
                "LOCKED"
                if final_pass
                else "NOT_VERIFIED"
            ),

        "output_artifact_contract":
            (
                "LOCKED"
                if final_pass
                else "NOT_VERIFIED"
            ),

        "model_protection": {

            "model_id":
                locked_model.get(
                    "model_id"
                ),

            "feature_count":
                locked_model.get(
                    "feature_count"
                ),

            "model_sha256":
                actual_model_sha,

            "model_unchanged":
                (
                    locked_model.get(
                        "sha256"
                    )
                    == actual_model_sha
                ),

            "context_only":
                contract.get(
                    "context_only"
                )
                is True,
        },

        "evidence_sha256":
            evidence_hashes,

        "failures":
            list(
                failures
            ),
    }

    CONTEXT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with VERIFICATION_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            verification,
            file,
            indent=2,
        )

    print(
        VERIFICATION_FILE
    )

    # ========================================================
    # Final
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    if final_pass:

        print(
            "STAGE 8.1.1: PASS"
        )

        print(
            "STAGE 8.1.2: PASS"
        )

        print(
            "STAGE 8.1.3: PASS"
        )

        print(
            "STAGE 8.1.4: PASS"
        )

        print(
            "STAGE 8.1.5: PASS"
        )

        print(
            "STAGE 8.1.6: PASS"
        )

        print(
            "STAGE 8.1: COMPLETE"
        )

        print(
            "STAGE 8 CONTEXT CONTRACT: LOCKED"
        )

    else:

        print(
            "STAGE 8.1.6: FAIL"
        )

        print(
            "STAGE 8.1: INCOMPLETE"
        )

        print(
            "STAGE 8 CONTEXT CONTRACT: NOT LOCKED"
        )

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
        if final_pass
        else 1
    )


if __name__ == "__main__":

    main()