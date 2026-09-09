"""
FixtureIQ Stage 8.1 Contract Verification

Verifies:

8.1.1 - Scope & Safety Boundary
8.1.2 - Trusted Input Contract
8.1.3 - Canonical Team Context Schema
8.1.4 - Freshness & Provenance Rules

Stage 8.1 remains IN PROGRESS until 8.1.5 and 8.1.6 pass.
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

OUTPUT_FILE = (
    CONTEXT_DIR
    / "stage8_context_contract_verification.json"
)

SERVING_CONTRACT_FILE = (
    MODEL_DIR
    / "production_serving_contract.json"
)

SELECTED_MODEL_FILE = (
    MODEL_DIR
    / "selected"
    / "selected_model.joblib"
)

STAGE7_8_FILE = (
    PRODUCTION_DIR
    / "stage7_8_final_verification.json"
)

STAGE7_9_FILE = (
    PRODUCTION_DIR
    / "stage7_9_final_verification.json"
)

HISTORY_FILE = (
    PRODUCTION_DIR
    / "production_history.csv"
)

FIXTURES_FILE = (
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
        "FixtureIQ Stage 8.1 Verification"
    )

    print(
        "8.1.1 + 8.1.2 + 8.1.3 + 8.1.4"
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
        SERVING_CONTRACT_FILE,
        SELECTED_MODEL_FILE,
        STAGE7_8_FILE,
        STAGE7_9_FILE,
        HISTORY_FILE,
        FIXTURES_FILE,
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

    stage7_8 = load_json(
        STAGE7_8_FILE
    )

    stage7_9 = load_json(
        STAGE7_9_FILE
    )

    # ========================================================
    # 2. Upstream foundation
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
        ).upper()
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
        ).upper()
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
        "Production serving VERIFIED",
        stage7_9.get(
            "production_serving_stack"
        )
        == "VERIFIED",
        failures,
    )

    # ========================================================
    # 3. 8.1.1 Scope + safety
    # ========================================================

    print(
        "\n3. STAGE 8.1.1 - SCOPE & SAFETY"
    )

    sub_stages = contract.get(
        "sub_stages",
        {}
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
        "8.1.1 marked LOCKED",
        sub_stages.get(
            "8.1.1"
        )
        == "LOCKED",
        failures,
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
        "Context-only = true",
        contract.get(
            "context_only"
        )
        is True,
        failures,
    )

    check(
        "Model mutation prohibited",
        protection.get(
            "model_mutation_allowed"
        )
        is False,
        failures,
    )

    check(
        "Retraining prohibited",
        protection.get(
            "retraining_allowed"
        )
        is False,
        failures,
    )

    check(
        "Model selection prohibited",
        protection.get(
            "model_selection_allowed"
        )
        is False,
        failures,
    )

    check(
        "Hyperparameter tuning prohibited",
        protection.get(
            "hyperparameter_tuning_allowed"
        )
        is False,
        failures,
    )

    check(
        "Feature schema mutation prohibited",
        protection.get(
            "feature_schema_mutation_allowed"
        )
        is False,
        failures,
    )

    check(
        "Prediction mutation prohibited",
        protection.get(
            "prediction_mutation_allowed"
        )
        is False,
        failures,
    )

    check(
        "Final-test reuse prohibited",
        protection.get(
            "final_test_reuse_allowed"
        )
        is False,
        failures,
    )

    check(
        "Standings cannot become model features",
        protection.get(
            "standings_as_model_features_allowed"
        )
        is False,
        failures,
    )

    check(
        "Form cannot become model features",
        protection.get(
            "form_as_model_features_allowed"
        )
        is False,
        failures,
    )

    actual_model_sha = sha256_file(
        SELECTED_MODEL_FILE
    )

    check(
        "Locked model ID random_forest",
        locked_model.get(
            "model_id"
        )
        == "random_forest",
        failures,
    )

    check(
        "Locked feature count = 86",
        locked_model.get(
            "feature_count"
        )
        == 86,
        failures,
    )

    check(
        "Locked model SHA matches actual model",
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
        "Final test cannot be reopened",
        stage7_protection.get(
            "stage8_may_reopen_final_test"
        )
        is False,
        failures,
    )

    # ========================================================
    # 4. 8.1.2 Trusted inputs
    # ========================================================

    print(
        "\n4. STAGE 8.1.2 - TRUSTED INPUTS"
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

    temporal = contract.get(
        "temporal_input_boundary",
        {}
    )

    check(
        "8.1.2 marked LOCKED",
        sub_stages.get(
            "8.1.2"
        )
        == "LOCKED",
        failures,
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
        "Season 2026",
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

    check(
        "Upcoming matches cannot affect form",
        temporal.get(
            "upcoming_matches_may_affect_form"
        )
        is False,
        failures,
    )

    check(
        "Future results prohibited",
        temporal.get(
            "future_results_allowed"
        )
        is False,
        failures,
    )

    # ========================================================
    # 5. 8.1.3 Canonical schema
    # ========================================================

    print(
        "\n5. STAGE 8.1.3 - CANONICAL SCHEMA"
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
        "8.1.3 marked LOCKED",
        sub_stages.get(
            "8.1.3"
        )
        == "LOCKED",
        failures,
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

    expected_standings = {
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
        == expected_standings,
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
        "Current-season form only",
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
    # 6. 8.1.4 Freshness + provenance
    # ========================================================

    print(
        "\n6. STAGE 8.1.4 - FRESHNESS & PROVENANCE"
    )

    freshness = contract.get(
        "freshness_and_provenance",
        {}
    )

    standings_policy = freshness.get(
        "standings_policy",
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

    dependencies = freshness.get(
        "dependency_invalidation",
        {}
    )

    runtime = freshness.get(
        "runtime_policy",
        {}
    )

    temporal_safety = freshness.get(
        "temporal_safety",
        {}
    )

    check(
        "8.1.4 marked LOCKED",
        sub_stages.get(
            "8.1.4"
        )
        == "LOCKED",
        failures,
    )

    check(
        "Freshness mode DEPENDENCY_BASED",
        freshness.get(
            "freshness_mode"
        )
        == "DEPENDENCY_BASED",
        failures,
    )

    check(
        "No arbitrary TTL source-of-truth",
        freshness.get(
            "arbitrary_fixed_ttl_is_source_of_truth"
        )
        is False,
        failures,
    )

    provenance_fields = set(
        freshness.get(
            "required_provenance_fields",
            []
        )
    )

    check(
        "Core provenance fields declared",
        {
            "generated_at_utc",
            "source_as_of_utc",
            "provider",
            "competition",
            "season",
        }.issubset(
            provenance_fields
        ),
        failures,
    )

    check(
        "Standings provider locked",
        standings_policy.get(
            "provider"
        )
        == "football-data.org",
        failures,
    )

    check(
        "Standings competition PL",
        standings_policy.get(
            "competition_code"
        )
        == "PL",
        failures,
    )

    check(
        "Standings season 2026",
        standings_policy.get(
            "season"
        )
        == 2026,
        failures,
    )

    check(
        "Form completed matches only",
        form_policy.get(
            "completed_matches_only"
        )
        is True,
        failures,
    )

    check(
        "Form current season only",
        form_policy.get(
            "current_season_only"
        )
        is True,
        failures,
    )

    check(
        "Form history cutoff required",
        form_policy.get(
            "history_cutoff_required"
        )
        is True,
        failures,
    )

    check(
        "Future form data prohibited",
        form_policy.get(
            "future_match_allowed"
        )
        is False,
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
        "Fixture context requires fresh team context",
        fixture_context_policy.get(
            "requires_fresh_team_context"
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
        "History change invalidates form",
        "CURRENT_TEAM_FORM"
        in dependencies.get(
            "production_history_changed",
            []
        ),
        failures,
    )

    check(
        "Standings change invalidates team context",
        "TEAM_CONTEXT"
        in dependencies.get(
            "standings_changed",
            []
        ),
        failures,
    )

    check(
        "Fixtures change invalidates enrichment",
        "ENRICHED_UPCOMING_FIXTURES"
        in dependencies.get(
            "upcoming_fixtures_changed",
            []
        ),
        failures,
    )

    check(
        "Missing dependency -> NOT_READY",
        runtime.get(
            "missing_required_dependency"
        )
        == "NOT_READY",
        failures,
    )

    check(
        "Stale dependency -> NOT_READY",
        runtime.get(
            "stale_required_dependency"
        )
        == "NOT_READY",
        failures,
    )

    check(
        "Invalid provenance -> NOT_READY",
        runtime.get(
            "invalid_provenance"
        )
        == "NOT_READY",
        failures,
    )

    check(
        "Partial unverified serving prohibited",
        runtime.get(
            "partial_unverified_context_serving_allowed"
        )
        is False,
        failures,
    )

    check(
        "Silent stale fallback prohibited",
        runtime.get(
            "silent_stale_fallback_allowed"
        )
        is False,
        failures,
    )

    check(
        "Runtime failure mode FAIL_CLOSED",
        runtime.get(
            "failure_mode"
        )
        == "FAIL_CLOSED",
        failures,
    )

    check(
        "Upcoming fixture cannot be history",
        temporal_safety.get(
            "upcoming_fixture_use_as_history_allowed"
        )
        is False,
        failures,
    )

    check(
        "Future results prohibited",
        temporal_safety.get(
            "future_result_use_allowed"
        )
        is False,
        failures,
    )

    # ========================================================
    # 7. Final decision
    # ========================================================

    print(
        "\n7. SAVE VERIFICATION"
    )

    overall_pass = (
        len(
            failures
        )
        == 0
    )

    report = {

        "stage":
            "8.1",

        "status":
            (
                "PARTIAL_PASS"
                if overall_pass
                else "FAIL"
            ),

        "stage_8_1_complete":
            False,

        "verified_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "sub_stages": {

            "8.1.1":
                (
                    "PASS"
                    if overall_pass
                    else "FAIL"
                ),

            "8.1.2":
                (
                    "PASS"
                    if overall_pass
                    else "FAIL"
                ),

            "8.1.3":
                (
                    "PASS"
                    if overall_pass
                    else "FAIL"
                ),

            "8.1.4":
                (
                    "PASS"
                    if overall_pass
                    else "FAIL"
                ),
        },

        "scope_safety_boundary":
            (
                "LOCKED"
                if overall_pass
                else "NOT_LOCKED"
            ),

        "trusted_input_contract":
            (
                "LOCKED"
                if overall_pass
                else "NOT_LOCKED"
            ),

        "canonical_team_context_schema":
            (
                "LOCKED"
                if overall_pass
                else "NOT_LOCKED"
            ),

        "freshness_provenance_policy":
            (
                "LOCKED"
                if overall_pass
                else "NOT_LOCKED"
            ),

        "failures":
            failures,
    }

    CONTEXT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
        )

    print(
        OUTPUT_FILE
    )

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

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
            "SCOPE & SAFETY BOUNDARY: LOCKED"
        )

        print(
            "FRESHNESS & PROVENANCE POLICY: LOCKED"
        )

        print(
            "STAGE 8.1: IN PROGRESS"
        )

    else:

        print(
            "STAGE 8.1: FAIL"
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
        if overall_pass
        else 1
    )


if __name__ == "__main__":

    main()