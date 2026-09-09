"""
FixtureIQ Stage 8.1 Contract Builder

Implements and preserves:

8.1.1 - Scope & Safety Boundary
8.1.2 - Trusted Input Contract
8.1.3 - Canonical Team Context Schema
8.1.4 - Freshness & Provenance Rules

Stage 8 remains a context-only layer.

This builder does NOT:
- train
- retrain
- tune
- select models
- modify the locked model
- modify the 86-feature schema
- run inference
- alter Stage 7 production predictions
- access final-test evaluation data
- fetch provider data
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# Project paths
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


SERVING_CONTRACT_FILE = (
    MODEL_DIR
    / "production_serving_contract.json"
)

SELECTED_MODEL_FILE = (
    MODEL_DIR
    / "selected"
    / "selected_model.joblib"
)

STAGE7_8_VERIFICATION_FILE = (
    PRODUCTION_DIR
    / "stage7_8_final_verification.json"
)

STAGE7_9_VERIFICATION_FILE = (
    PRODUCTION_DIR
    / "stage7_9_final_verification.json"
)

PRODUCTION_HISTORY_FILE = (
    PRODUCTION_DIR
    / "production_history.csv"
)

PRODUCTION_HISTORY_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_history_report.json"
)

UPCOMING_FIXTURES_FILE = (
    PRODUCTION_DIR
    / "upcoming_fixtures.csv"
)

FIXTURE_FETCH_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_fixture_fetch_report.json"
)

OUTPUT_FILE = (
    CONTEXT_DIR
    / "stage8_context_contract.json"
)


# ============================================================
# Helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise FileNotFoundError(
            f"Required JSON artifact missing: {path}"
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


def csv_observation(
    path: Path,
) -> dict:

    if not path.exists():

        raise FileNotFoundError(
            f"Required CSV artifact missing: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.reader(
            file
        )

        try:

            header = next(
                reader
            )

        except StopIteration:

            raise RuntimeError(
                f"CSV is empty: {path}"
            )

        row_count = sum(
            1
            for _ in reader
        )

    if row_count <= 0:

        raise RuntimeError(
            f"CSV contains no data rows: {path}"
        )

    return {

        "path":
            relative_path(
                path
            ),

        "exists":
            True,

        "row_count_at_contract_build":
            int(
                row_count
            ),

        "columns_at_contract_build":
            list(
                header
            ),

        "snapshot_observation_only":
            True,
    }


def stage_passed(
    payload: dict,
    *,
    complete_key=None,
    status_key=None,
) -> bool:

    if (
        str(
            payload.get(
                "status",
                ""
            )
        )
        .strip()
        .upper()
        != "PASS"
    ):

        return False

    if (
        complete_key
        and
        complete_key in payload
        and
        payload.get(
            complete_key
        )
        is not True
    ):

        return False

    if (
        status_key
        and
        status_key in payload
        and
        str(
            payload.get(
                status_key,
                ""
            )
        )
        .strip()
        .upper()
        != "COMPLETE"
    ):

        return False

    return True


def find_model_block(
    payload,
):

    if isinstance(
        payload,
        dict,
    ):

        model_id = payload.get(
            "model_id"
        )

        if (
            str(
                model_id
            )
            .strip()
            .lower()
            == "random_forest"
        ):

            return payload

        for value in payload.values():

            found = find_model_block(
                value
            )

            if found is not None:

                return found

    elif isinstance(
        payload,
        list,
    ):

        for item in payload:

            found = find_model_block(
                item
            )

            if found is not None:

                return found

    return None


def extract_model_sha(
    model_block: dict,
) -> str | None:

    candidate_keys = [
        "sha256",
        "model_sha256",
        "model_sha",
        "locked_model_sha256",
    ]

    for key in candidate_keys:

        value = model_block.get(
            key
        )

        if (
            isinstance(
                value,
                str,
            )
            and
            len(
                value.strip()
            )
            == 64
        ):

            return value.strip().lower()

    return None


def extract_feature_count(
    model_block: dict,
):

    for key in [
        "feature_count",
        "n_features",
        "number_of_features",
    ]:

        if key in model_block:

            try:

                return int(
                    model_block[
                        key
                    ]
                )

            except (
                TypeError,
                ValueError,
            ):

                pass

    return None


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 8.1 Contract Builder"
    )

    print(
        "8.1.1 + 8.1.2 + 8.1.3 + 8.1.4"
    )

    print("=" * 72)

    CONTEXT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # 1. Upstream foundation
    # ========================================================

    print(
        "\n1. UPSTREAM FOUNDATION"
    )

    stage7_8 = load_json(
        STAGE7_8_VERIFICATION_FILE
    )

    stage7_9 = load_json(
        STAGE7_9_VERIFICATION_FILE
    )

    serving_contract = load_json(
        SERVING_CONTRACT_FILE
    )

    stage7_8_ok = stage_passed(
        stage7_8,
        complete_key="stage_7_8_complete",
        status_key="stage_7_8_status",
    )

    stage7_9_ok = stage_passed(
        stage7_9,
        complete_key="stage_7_9_complete",
        status_key="stage_7_9_status",
    )

    serving_verified = (
        str(
            stage7_9.get(
                "production_serving_stack",
                ""
            )
        )
        .strip()
        .upper()
        == "VERIFIED"
    )

    print(
        "Stage 7.8 verified: "
        f"{'PASS' if stage7_8_ok else 'FAIL'}"
    )

    print(
        "Stage 7.9 complete: "
        f"{'PASS' if stage7_9_ok else 'FAIL'}"
    )

    print(
        "Production serving verified: "
        f"{'PASS' if serving_verified else 'FAIL'}"
    )

    if not (
        stage7_8_ok
        and
        stage7_9_ok
        and
        serving_verified
    ):

        raise RuntimeError(
            (
                "Stage 8 contract cannot be built "
                "because Stage 7 is not fully verified."
            )
        )

    # ========================================================
    # 2. Locked model identity
    # ========================================================

    print(
        "\n2. LOCKED MODEL IDENTITY"
    )

    model_block = find_model_block(
        serving_contract
    )

    if model_block is None:

        raise RuntimeError(
            (
                "Could not locate locked random_forest "
                "model identity in production_serving_contract.json"
            )
        )

    contract_model_sha = extract_model_sha(
        model_block
    )

    contract_feature_count = extract_feature_count(
        model_block
    )

    actual_model_sha = sha256_file(
        SELECTED_MODEL_FILE
    )

    if contract_model_sha is None:

        raise RuntimeError(
            (
                "Could not read model SHA256 from "
                "production serving contract."
            )
        )

    if contract_feature_count is None:

        raise RuntimeError(
            (
                "Could not read feature_count from "
                "production serving contract."
            )
        )

    if (
        actual_model_sha
        != contract_model_sha
    ):

        raise RuntimeError(
            (
                "Locked model SHA mismatch. "
                "Stage 8 contract build aborted."
            )
        )

    if (
        contract_feature_count
        != 86
    ):

        raise RuntimeError(
            (
                "Expected locked model feature_count=86."
            )
        )

    print(
        "Model ID: random_forest"
    )

    print(
        "Feature count: 86"
    )

    print(
        f"Model SHA256: {actual_model_sha}"
    )

    print(
        "Locked model integrity: PASS"
    )

    # ========================================================
    # 3. Operational inputs
    # ========================================================

    print(
        "\n3. TRUSTED OPERATIONAL INPUTS"
    )

    history_observation = csv_observation(
        PRODUCTION_HISTORY_FILE
    )

    fixtures_observation = csv_observation(
        UPCOMING_FIXTURES_FILE
    )

    load_json(
        PRODUCTION_HISTORY_REPORT_FILE
    )

    load_json(
        FIXTURE_FETCH_REPORT_FILE
    )

    print(
        "Production history: PASS "
        f"({history_observation['row_count_at_contract_build']} rows)"
    )

    print(
        "Upcoming fixtures: PASS "
        f"({fixtures_observation['row_count_at_contract_build']} rows)"
    )

    # ========================================================
    # 4. Existing contract
    # ========================================================

    if OUTPUT_FILE.exists():

        contract = load_json(
            OUTPUT_FILE
        )

    else:

        contract = {}

    contract[
        "stage"
    ] = "8.1"

    contract[
        "contract_version"
    ] = "1.0.0"

    contract[
        "contract_type"
    ] = "STAGE8_CONTEXT_CONTRACT"

    contract[
        "purpose"
    ] = "LIVE_EPL_CONTEXT_LAYER"

    contract[
        "updated_at_utc"
    ] = datetime.now(
        timezone.utc
    ).isoformat()

    contract[
        "stage_8_1_complete"
    ] = False

    sub_stages = dict(
        contract.get(
            "sub_stages",
            {}
        )
    )

    sub_stages[
        "8.1.1"
    ] = "LOCKED"

    sub_stages[
        "8.1.2"
    ] = "LOCKED"

    sub_stages[
        "8.1.3"
    ] = "LOCKED"

    sub_stages[
        "8.1.4"
    ] = "LOCKED"

    contract[
        "sub_stages"
    ] = sub_stages

    # ========================================================
    # 5. Stage 8.1.1 Scope + safety boundary
    # ========================================================

    contract[
        "context_only"
    ] = True

    contract[
        "scope"
    ] = {

        "live_epl_standings":
            True,

        "current_team_form":
            True,

        "team_context_snapshot":
            True,

        "fixture_context_enrichment":
            True,

        "context_rest_api":
            True,

        "model_development":
            False,
    }

    contract[
        "allowed_operations"
    ] = [
        "READ_VERIFIED_STAGE7_ARTIFACTS",
        "READ_PRODUCTION_HISTORY",
        "READ_UPCOMING_FIXTURES",
        "READ_LOCKED_MODEL_IDENTITY",
        "FETCH_LIVE_EPL_CONTEXT",
        "DERIVE_CURRENT_TEAM_FORM",
        "BUILD_STAGE8_CONTEXT_ARTIFACTS",
        "SERVE_CONTEXT_READ_ONLY",
    ]

    contract[
        "model_protection"
    ] = {

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

    contract[
        "locked_model"
    ] = {

        "model_id":
            "random_forest",

        "model_status":
            "LOCKED",

        "feature_count":
            86,

        "sha256":
            actual_model_sha,

        "source_contract":
            relative_path(
                SERVING_CONTRACT_FILE
            ),

        "model_path":
            relative_path(
                SELECTED_MODEL_FILE
            ),

        "mutation_allowed":
            False,
    }

    contract[
        "stage7_protection"
    ] = {

        "production_predictions_read_only":
            True,

        "production_features_read_only":
            True,

        "selected_model_read_only":
            True,

        "stage7_verification_artifacts_read_only":
            True,

        "stage8_may_change_existing_probabilities":
            False,

        "stage8_may_change_feature_count":
            False,

        "stage8_may_reopen_final_test":
            False,
    }

    # ========================================================
    # 6. Stage 8.1.2 Trusted inputs
    # ========================================================

    contract[
        "trusted_inputs"
    ] = {

        "upstream_verification": {

            "stage7_8": {

                "path":
                    relative_path(
                        STAGE7_8_VERIFICATION_FILE
                    ),

                "required_status":
                    "PASS",

                "required_completion":
                    "COMPLETE",

                "access":
                    "READ_ONLY",
            },

            "stage7_9": {

                "path":
                    relative_path(
                        STAGE7_9_VERIFICATION_FILE
                    ),

                "required_status":
                    "PASS",

                "required_completion":
                    "COMPLETE",

                "required_serving_stack":
                    "VERIFIED",

                "access":
                    "READ_ONLY",
            },
        },

        "production_history": {

            "owner":
                "STAGE_7",

            "purpose":
                (
                    "Verified completed-match history "
                    "used for Stage 8 current form."
                ),

            "data_path":
                relative_path(
                    PRODUCTION_HISTORY_FILE
                ),

            "report_path":
                relative_path(
                    PRODUCTION_HISTORY_REPORT_FILE
                ),

            "access":
                "READ_ONLY",

            "required":
                True,

            "dynamic_operational_input":
                True,

            "freeze_snapshot_hash":
                False,

            "observation":
                history_observation,
        },

        "upcoming_fixtures": {

            "owner":
                "STAGE_7",

            "purpose":
                (
                    "Verified future fixtures that receive "
                    "Stage 8 context enrichment."
                ),

            "data_path":
                relative_path(
                    UPCOMING_FIXTURES_FILE
                ),

            "report_path":
                relative_path(
                    FIXTURE_FETCH_REPORT_FILE
                ),

            "access":
                "READ_ONLY",

            "required":
                True,

            "dynamic_operational_input":
                True,

            "freeze_snapshot_hash":
                False,

            "observation":
                fixtures_observation,
        },

        "live_context_provider": {

            "owner":
                "EXTERNAL_PROVIDER",

            "provider":
                "football-data.org",

            "role":
                "PRIMARY_LIVE_CONTEXT_PROVIDER",

            "competition":
                "Premier League",

            "competition_code":
                "PL",

            "configured_season":
                2026,

            "stage8_usage": [
                "LIVE_STANDINGS",
                "LIVE_COMPETITION_CONTEXT",
            ],

            "write_access_to_stage7_artifacts":
                False,

            "required_for_live_standings":
                True,
        },

        "api_football": {

            "provider":
                "API-Football",

            "role":
                "HISTORICAL_LEGACY_SOURCE",

            "primary_live_stage8_provider":
                False,
        },
    }

    contract[
        "input_ownership_policy"
    ] = {

        "stage7_artifacts":
            "READ_ONLY",

        "external_provider_response":
            "VALIDATE_BEFORE_STAGE8_USE",

        "stage8_derived_artifacts":
            "STAGE8_OWNED",

        "stage8_may_overwrite_stage7_artifacts":
            False,
    }

    contract[
        "trust_hierarchy"
    ] = [
        "VERIFIED_STAGE7_STATE",
        "FIXTUREIQ_NORMALIZED_PRODUCTION_HISTORY",
        "FOOTBALL_DATA_ORG_LIVE_CONTEXT",
        "STAGE8_DERIVED_CONTEXT",
    ]

    contract[
        "input_failure_policy"
    ] = {

        "missing_required_input":
            "FAIL_CLOSED",

        "invalid_required_input":
            "FAIL_CLOSED",

        "upstream_verification_failure":
            "FAIL_CLOSED",

        "provider_failure":
            "FAIL_CLOSED",

        "silent_fallback_to_unverified_source":
            False,
    }

    contract[
        "temporal_input_boundary"
    ] = {

        "completed_matches_may_affect_form":
            True,

        "upcoming_matches_may_affect_form":
            False,

        "upcoming_matches_receive_context":
            True,

        "future_results_allowed":
            False,

        "current_form_source":
            "VERIFIED_COMPLETED_MATCHES_ONLY",

        "anti_leakage_rule":
            (
                "A match may affect form only after it is "
                "completed and present in verified "
                "production history."
            ),
    }

    # ========================================================
    # 7. Stage 8.1.3 Canonical schema
    # ========================================================

    contract[
        "canonical_team_context_schema"
    ] = {

        "schema_version":
            "1.0.0",

        "expected_current_epl_team_count":
            20,

        "team_identity": {

            "namespace":
                "fixtureiq-team",

            "provider_ids_are_internal_ids":
                False,

            "fields": {

                "team_id": {

                    "type":
                        "string",

                    "required":
                        True,

                    "nullable":
                        False,
                },

                "team_name": {

                    "type":
                        "string",

                    "required":
                        True,

                    "nullable":
                        False,
                },
            },
        },

        "standings": {

            "fields": {

                "position":
                    {
                        "type": "integer",
                        "required": True,
                        "minimum": 1,
                        "maximum": 20,
                    },

                "played":
                    {
                        "type": "integer",
                        "required": True,
                        "minimum": 0,
                    },

                "won":
                    {
                        "type": "integer",
                        "required": True,
                        "minimum": 0,
                    },

                "drawn":
                    {
                        "type": "integer",
                        "required": True,
                        "minimum": 0,
                    },

                "lost":
                    {
                        "type": "integer",
                        "required": True,
                        "minimum": 0,
                    },

                "goals_for":
                    {
                        "type": "integer",
                        "required": True,
                        "minimum": 0,
                    },

                "goals_against":
                    {
                        "type": "integer",
                        "required": True,
                        "minimum": 0,
                    },

                "goal_difference":
                    {
                        "type": "integer",
                        "required": True,
                    },

                "points":
                    {
                        "type": "integer",
                        "required": True,
                        "minimum": 0,
                    },
            },

            "invariants": [
                "played == won + drawn + lost",
                "goal_difference == goals_for - goals_against",
                "points == (3 * won) + drawn",
                "position values are unique within one standings snapshot",
                "team_id values are unique within one standings snapshot",
            ],
        },

        "current_form": {

            "default_window":
                5,

            "season_scope":
                "CURRENT_PRODUCTION_SEASON_ONLY",

            "allow_short_window":
                True,

            "result_symbols":
                [
                    "W",
                    "D",
                    "L",
                ],

            "result_order":
                "OLDEST_TO_NEWEST",

            "most_recent_result_position":
                "RIGHTMOST",

            "fields": {

                "form_matches_available":
                    {
                        "type": "integer",
                        "required": True,
                        "minimum": 0,
                        "maximum": 5,
                    },

                "recent_results":
                    {
                        "type": "string",
                        "required": True,
                    },

                "recent_points":
                    {
                        "type": "integer",
                        "required": True,
                        "minimum": 0,
                        "maximum": 15,
                    },

                "recent_wins":
                    {
                        "type": "integer",
                        "required": True,
                        "minimum": 0,
                        "maximum": 5,
                    },

                "recent_draws":
                    {
                        "type": "integer",
                        "required": True,
                        "minimum": 0,
                        "maximum": 5,
                    },

                "recent_losses":
                    {
                        "type": "integer",
                        "required": True,
                        "minimum": 0,
                        "maximum": 5,
                    },

                "recent_goals_for":
                    {
                        "type": "integer",
                        "required": True,
                        "minimum": 0,
                    },

                "recent_goals_against":
                    {
                        "type": "integer",
                        "required": True,
                        "minimum": 0,
                    },

                "recent_goal_difference":
                    {
                        "type": "integer",
                        "required": True,
                    },
            },

            "invariants": [
                (
                    "form_matches_available == "
                    "recent_wins + recent_draws + recent_losses"
                ),
                (
                    "recent_points == "
                    "(3 * recent_wins) + recent_draws"
                ),
                (
                    "recent_goal_difference == "
                    "recent_goals_for - recent_goals_against"
                ),
                (
                    "length(recent_results) == "
                    "form_matches_available"
                ),
                "all recent_results symbols are one of W/D/L",
            ],
        },

        "venue_form": {

            "enabled":
                True,

            "window":
                5,

            "allow_short_window":
                True,
        },

        "schema_policy": {

            "provider_team_id_allowed_as_internal_team_id":
                False,

            "unknown_team_allowed":
                False,

            "duplicate_team_allowed":
                False,

            "fabricate_missing_form_matches":
                False,

            "future_match_data_allowed":
                False,

            "standings_or_form_are_model_features":
                False,
        },
    }

    # ========================================================
    # 8. Stage 8.1.4 Freshness + provenance
    # ========================================================

    contract[
        "freshness_and_provenance"
    ] = {

        "policy_version":
            "1.0.0",

        "freshness_mode":
            "DEPENDENCY_BASED",

        "arbitrary_fixed_ttl_is_source_of_truth":
            False,

        "required_provenance_fields": [
            "generated_at_utc",
            "source_as_of_utc",
            "provider",
            "competition",
            "season",
        ],

        "history_provenance_fields": [
            "history_cutoff_utc",
            "production_history_source",
        ],

        "fixture_provenance_fields": [
            "fixture_snapshot_as_of_utc",
            "upcoming_fixture_source",
        ],

        "standings_policy": {

            "provider":
                "football-data.org",

            "competition_code":
                "PL",

            "season":
                2026,

            "must_record_generated_at_utc":
                True,

            "must_record_source_as_of_utc":
                True,

            "must_record_dependency_identity":
                True,

            "stale_if_required_provider_snapshot_invalid":
                True,
        },

        "form_policy": {

            "source":
                "production_history.csv",

            "completed_matches_only":
                True,

            "current_season_only":
                True,

            "default_window":
                5,

            "history_cutoff_required":
                True,

            "history_cutoff_definition":
                (
                    "Latest completed match included "
                    "in the form snapshot."
                ),

            "future_match_allowed":
                False,

            "upcoming_fixture_allowed_to_affect_form":
                False,
        },

        "team_context_policy": {

            "requires_fresh_standings":
                True,

            "requires_fresh_form":
                True,

            "stale_if_standings_stale":
                True,

            "stale_if_form_stale":
                True,
        },

        "fixture_context_policy": {

            "requires_fresh_team_context":
                True,

            "requires_fresh_upcoming_fixtures":
                True,

            "upcoming_fixture_must_be_future":
                True,

            "fixture_may_affect_its_own_form":
                False,

            "stale_if_team_context_stale":
                True,

            "stale_if_upcoming_fixtures_changed":
                True,
        },

        "dependency_invalidation": {

            "production_history_changed":
                [
                    "CURRENT_TEAM_FORM",
                    "TEAM_CONTEXT",
                    "ENRICHED_UPCOMING_FIXTURES",
                ],

            "standings_changed":
                [
                    "TEAM_CONTEXT",
                    "ENRICHED_UPCOMING_FIXTURES",
                ],

            "current_team_form_changed":
                [
                    "TEAM_CONTEXT",
                    "ENRICHED_UPCOMING_FIXTURES",
                ],

            "upcoming_fixtures_changed":
                [
                    "ENRICHED_UPCOMING_FIXTURES",
                ],

            "team_context_changed":
                [
                    "ENRICHED_UPCOMING_FIXTURES",
                ],
        },

        "runtime_policy": {

            "missing_required_dependency":
                "NOT_READY",

            "stale_required_dependency":
                "NOT_READY",

            "invalid_provenance":
                "NOT_READY",

            "partial_unverified_context_serving_allowed":
                False,

            "silent_stale_fallback_allowed":
                False,

            "failure_mode":
                "FAIL_CLOSED",
        },

        "temporal_safety": {

            "completed_match_required_for_form":
                True,

            "future_result_use_allowed":
                False,

            "upcoming_fixture_use_as_history_allowed":
                False,

            "fixture_context_is_snapshot_context":
                True,

            "historical_per_fixture_reconstruction_required_now":
                False,

            "historical_reconstruction_future_rule":
                (
                    "If historical per-fixture context is "
                    "implemented later, only information "
                    "strictly available before kickoff may be used."
                ),
        },
    }

    # ========================================================
    # 9. Save
    # ========================================================

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            contract,
            file,
            indent=2,
        )

    print(
        "\n4. CONTRACT OUTPUT"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\n" + "=" * 72
    )

    print(
        "STAGE 8.1.1: BUILT"
    )

    print(
        "STAGE 8.1.2: PRESERVED"
    )

    print(
        "STAGE 8.1.3: PRESERVED"
    )

    print(
        "STAGE 8.1.4: BUILT"
    )

    print(
        "STAGE 8.1: IN PROGRESS"
    )

    print("=" * 72)


if __name__ == "__main__":

    main()